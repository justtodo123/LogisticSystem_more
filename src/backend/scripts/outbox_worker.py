"""Transactional outbox worker; each loop uses an isolated database Session."""
import argparse
import asyncio
import logging
import socket
from contextlib import suppress

from config.database import SessionLocal
from core.json_logging import configure_logging
from core.request_context import (
    bind_request_context,
    get_request_context,
    reset_request_context,
)
from models.outbox_event import OutboxEvent
from services.notification.dispatcher import NotificationDispatcher
from services.outbox_service import (
    NonRetryableOutboxError,
    deliver_outbox_batch,
    execution_context_from_outbox,
)

configure_logging()


logger = logging.getLogger(__name__)
PROBE_EVENT_PREFIX = "write_path_probe."


def handle_write_path_probe(event: OutboxEvent) -> bool | None:
    """Deterministic success/retry/dead-letter cases for the write-path probe."""
    event_type = str(event.event_type or "")
    if not event_type.startswith(PROBE_EVENT_PREFIX):
        return None
    logger.info("worker_handle")
    case = event_type[len(PROBE_EVENT_PREFIX) :]
    if case == "dead":
        logger.info("notification_dead_letter")
        raise NonRetryableOutboxError("write-path probe dead-letter")
    if case == "retry" and int(event.retry_count or 0) <= 0:
        return False
    logger.info("notification_delivered")
    return True


async def _send(event: OutboxEvent) -> bool:
    """Deliver one outbox payload; bind execution context if the batch did not."""
    session = SessionLocal()
    try:
        payload = dict(event.payload or {})
        payload["idempotency_key"] = event.dedup_key
        token = None
        if get_request_context() is None:
            token = bind_request_context(execution_context_from_outbox(event))
        try:
            probe = handle_write_path_probe(event)
            if probe is not None:
                return probe
            scenario = event.event_type.replace(".", "_")
            results = await NotificationDispatcher(db=session).notify(scenario, payload)
            return bool(results) and all(value == "ok" for value in results.values())
        finally:
            if token is not None:
                reset_request_context(token)
    finally:
        session.close()


def run_once(
    *,
    worker_id: str,
    limit: int = 100,
    lease_seconds: int = 60,
    max_retries: int = 3,
    retry_delay_seconds: int = 60,
) -> dict[str, int]:
    """Run one claim/send/finalize batch."""
    return deliver_outbox_batch(
        SessionLocal,
        lambda event: asyncio.run(_send(event)),
        worker_id=worker_id,
        limit=limit,
        lease_seconds=lease_seconds,
        max_retries=max_retries,
        retry_delay_seconds=retry_delay_seconds,
    )


async def run_worker(
    stop_event: asyncio.Event,
    *,
    worker_id: str,
    poll_seconds: float = 1.0,
    limit: int = 100,
    lease_seconds: int = 60,
    max_retries: int = 3,
    retry_delay_seconds: int = 60,
) -> None:
    """Loop until cancelled; delivery is at-least-once."""
    while not stop_event.is_set():
        try:
            await asyncio.to_thread(
                run_once,
                worker_id=worker_id,
                limit=limit,
                lease_seconds=lease_seconds,
                max_retries=max_retries,
                retry_delay_seconds=retry_delay_seconds,
            )
        except Exception:
            logger.exception("Outbox worker iteration failed")
        with suppress(asyncio.TimeoutError):
            await asyncio.wait_for(stop_event.wait(), timeout=poll_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run transactional outbox worker")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--worker-id", default=f"{socket.gethostname()}-outbox")
    parser.add_argument("--poll-seconds", type=float, default=1.0)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--lease-seconds", type=int, default=60)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--retry-delay-seconds", type=int, default=60)
    args = parser.parse_args()
    if args.once:
        run_once(
            worker_id=args.worker_id,
            limit=args.limit,
            lease_seconds=args.lease_seconds,
            max_retries=args.max_retries,
            retry_delay_seconds=args.retry_delay_seconds,
        )
        return

    stop_event = asyncio.Event()
    try:
        asyncio.run(
            run_worker(
                stop_event,
                worker_id=args.worker_id,
                poll_seconds=args.poll_seconds,
                limit=args.limit,
                lease_seconds=args.lease_seconds,
                max_retries=args.max_retries,
                retry_delay_seconds=args.retry_delay_seconds,
            )
        )
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
