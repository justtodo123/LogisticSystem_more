"""事务 Outbox worker；每轮使用独立数据库 Session。"""
import argparse
import asyncio
import logging
import socket
from contextlib import suppress

from config.database import SessionLocal
from models.outbox_event import OutboxEvent
from services.notification.dispatcher import NotificationDispatcher
from services.outbox_service import deliver_outbox_batch


logger = logging.getLogger(__name__)


async def _send(event: OutboxEvent) -> bool:
    """将 outbox payload 交给通知分发器；dedup_key 作为外部幂等提示透传。"""
    session = SessionLocal()
    try:
        payload = dict(event.payload or {})
        payload["idempotency_key"] = event.dedup_key
        scenario = event.event_type.replace(".", "_")
        results = await NotificationDispatcher(db=session).notify(scenario, payload)
        return bool(results) and all(value == "ok" for value in results.values())
    finally:
        session.close()


def run_once(*, worker_id: str, limit: int = 100, lease_seconds: int = 60) -> dict[str, int]:
    """执行一轮；数据库 claim 和通知配置读取均使用独立 Session。"""
    return deliver_outbox_batch(
        SessionLocal,
        lambda event: asyncio.run(_send(event)),
        worker_id=worker_id,
        limit=limit,
        lease_seconds=lease_seconds,
    )


async def run_worker(
    stop_event: asyncio.Event,
    *,
    worker_id: str,
    poll_seconds: float = 1.0,
    limit: int = 100,
    lease_seconds: int = 60,
) -> None:
    """循环运行 outbox；投递语义为 at-least-once。"""
    while not stop_event.is_set():
        try:
            await asyncio.to_thread(
                run_once,
                worker_id=worker_id,
                limit=limit,
                lease_seconds=lease_seconds,
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
    args = parser.parse_args()
    if args.once:
        run_once(
            worker_id=args.worker_id,
            limit=args.limit,
            lease_seconds=args.lease_seconds,
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
            )
        )
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
