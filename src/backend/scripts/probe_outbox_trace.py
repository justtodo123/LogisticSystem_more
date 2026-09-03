"""Prove HTTP -> outbox -> worker trace continuity for success, retry, and dead-letter."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
import logging
from pathlib import Path
import sys
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from sqlalchemy.orm import Session, sessionmaker

from core.json_logging import JsonFormatter, configure_logging
from core.request_context import RequestContext, bind_request_context, reset_request_context
from models.outbox_event import OutboxEvent
from services.outbox_service import (
    NonRetryableOutboxError,
    deliver_outbox_batch,
    enqueue_outbox,
)

logger = logging.getLogger(__name__)

HTTP_TRACE_ID = "trc-write-path-probe"
HTTP_REQUEST_ID = "req-write-path-probe"
HTTP_TASK_ID = "task-write-path-probe"


class RecordingHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.formatter = JsonFormatter()
        self.lines: list[dict[str, Any]] = []

    def emit(self, record: logging.LogRecord) -> None:
        from core.request_context import context_as_dict

        ctx = context_as_dict()
        payload = {
            "msg": record.getMessage(),
            "logger": record.name,
            "trace_id": getattr(record, "trace_id", None) or ctx.get("trace_id"),
            "request_id": getattr(record, "request_id", None) or ctx.get("request_id"),
        }
        try:
            formatted = json.loads(self.formatter.format(record))
        except Exception:
            formatted = {}
        if isinstance(formatted, dict):
            for key, value in formatted.items():
                current = payload.get(key)
                if current not in (None, "", "-"):
                    continue
                payload[key] = value
        self.lines.append(payload)


def probe_http(base_url: str) -> dict[str, Any]:
    url = base_url.rstrip("/") + "/api/health"
    request = Request(
        url,
        headers={
            "X-Request-ID": HTTP_REQUEST_ID,
            "X-Trace-ID": HTTP_TRACE_ID,
            "X-Task-ID": HTTP_TASK_ID,
        },
    )
    with urlopen(request, timeout=10) as response:
        return {
            "status": response.status,
            "request_id": response.headers.get("X-Request-ID"),
            "trace_id": response.headers.get("X-Trace-ID"),
            "task_id": response.headers.get("X-Task-ID"),
        }


def _enqueue_cases(db: Session) -> None:
    token = bind_request_context(
        RequestContext(
            request_id=HTTP_REQUEST_ID,
            trace_id=HTTP_TRACE_ID,
            task_id=HTTP_TASK_ID,
            idempotency_key="idem-write-path-probe",
        )
    )
    try:
        enqueue_outbox(
            db,
            dedup_key="write-path-success",
            event_type="notification.test",
            payload={"task_id": HTTP_TASK_ID, "case": "success"},
        )
        enqueue_outbox(
            db,
            dedup_key="write-path-retry",
            event_type="notification.test",
            payload={"task_id": HTTP_TASK_ID, "case": "retry"},
        )
        enqueue_outbox(
            db,
            dedup_key="write-path-dead",
            event_type="notification.test",
            payload={"task_id": HTTP_TASK_ID, "case": "dead-letter"},
        )
        db.commit()
    finally:
        reset_request_context(token)


def _sender_factory(attempts: dict[str, list[dict[str, str]]]):
    def sender(event: OutboxEvent) -> bool:
        from core.request_context import get_request_context

        ctx = get_request_context()
        assert ctx is not None
        attempts[event.dedup_key].append(
            {
                "request_id": ctx.request_id,
                "trace_id": ctx.trace_id,
                "parent_request_id": ctx.parent_request_id or "",
                "task_id": ctx.task_id or "",
            }
        )
        logger.info("worker_handle")
        if event.dedup_key.endswith("dead"):
            logger.info("notification_dead_letter")
            raise NonRetryableOutboxError("invalid payload")
        if event.dedup_key.endswith("retry") and len(attempts[event.dedup_key]) == 1:
            return False
        logger.info("notification_delivered")
        return True

    return sender


def run_probe(session_factory: sessionmaker, *, base_url: str | None = None) -> dict[str, Any]:
    configure_logging()
    handler = RecordingHandler()
    handler.setLevel(logging.INFO)
    root = logging.getLogger()
    previous_level = root.level
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    watched = [
        logging.getLogger("services.outbox_service"),
        logging.getLogger("scripts.probe_outbox_trace"),
        logger,
    ]
    previous_logger_state = []
    for item in watched:
        previous_logger_state.append((item, item.level, item.propagate))
        item.setLevel(logging.INFO)
        item.propagate = True
        item.addHandler(handler)
    failures: list[str] = []
    http_info: dict[str, Any] | None = None
    try:
        if base_url:
            try:
                http_info = probe_http(base_url)
                if http_info.get("trace_id") != HTTP_TRACE_ID:
                    failures.append(f"HTTP trace mismatch: {http_info}")
                if http_info.get("request_id") != HTTP_REQUEST_ID:
                    failures.append(f"HTTP request mismatch: {http_info}")
            except (URLError, OSError, TimeoutError) as exc:
                failures.append(f"HTTP probe failed: {exc}")

        db = session_factory()
        try:
            _enqueue_cases(db)
            stored = {
                event.dedup_key: event
                for event in db.query(OutboxEvent)
                .filter(OutboxEvent.dedup_key.in_([
                    "write-path-success",
                    "write-path-retry",
                    "write-path-dead",
                ]))
                .all()
            }
            for key, event in stored.items():
                nested = (event.payload or {}).get("_trace") or {}
                if nested.get("trace_id") != HTTP_TRACE_ID:
                    failures.append(f"{key} payload trace_id mismatch")
                if nested.get("request_id") != HTTP_REQUEST_ID:
                    failures.append(f"{key} payload request_id mismatch")
        finally:
            db.close()

        attempts: dict[str, list[dict[str, str]]] = defaultdict(list)
        sender = _sender_factory(attempts)
        first = deliver_outbox_batch(
            session_factory,
            sender,
            worker_id="write-path-trace-probe",
            max_retries=3,
            retry_delay_seconds=0,
        )
        second = deliver_outbox_batch(
            session_factory,
            sender,
            worker_id="write-path-trace-probe",
            max_retries=3,
            retry_delay_seconds=0,
        )

        db = session_factory()
        try:
            final = {
                event.dedup_key: event.status
                for event in db.query(OutboxEvent)
                .filter(OutboxEvent.dedup_key.in_([
                    "write-path-success",
                    "write-path-retry",
                    "write-path-dead",
                ]))
                .all()
            }
        finally:
            db.close()

        expected_status = {
            "write-path-success": "delivered",
            "write-path-retry": "delivered",
            "write-path-dead": "dead-letter",
        }
        if final != expected_status:
            failures.append(f"unexpected outbox statuses: {final}")
        if first.get("delivered") < 1 or first.get("retry") < 1 or first.get("dead-letter") < 1:
            failures.append(f"first batch missing outcomes: {first}")
        if second.get("delivered") < 1:
            failures.append(f"retry batch did not deliver: {second}")

        retry_ids = [item["request_id"] for item in attempts.get("write-path-retry", [])]
        if len(retry_ids) != 2 or retry_ids[0] == retry_ids[1]:
            failures.append(f"retry execution request_id not unique: {retry_ids}")
        for key, rows in attempts.items():
            for row in rows:
                if row["trace_id"] != HTTP_TRACE_ID:
                    failures.append(f"{key} worker trace_id mismatch")
                if row["parent_request_id"] != HTTP_REQUEST_ID:
                    failures.append(f"{key} parent_request_id mismatch")
                if row["request_id"] == HTTP_REQUEST_ID:
                    failures.append(f"{key} reused HTTP request_id")
                if row["task_id"] != HTTP_TASK_ID:
                    failures.append(f"{key} task_id mismatch")

        traced_msgs = {
            line.get("msg")
            for line in handler.lines
            if line.get("trace_id") == HTTP_TRACE_ID or line.get("msg") in {
                "outbox_execute",
                "outbox_outcome",
                "worker_handle",
                "notification_dead_letter",
                "notification_delivered",
            }
        }
        missing_logs = [
            name
            for name in ("outbox_execute", "outbox_outcome", "worker_handle", "notification_dead_letter")
            if name not in traced_msgs
        ]
        raw_idem = "idem-write-path-probe"
        if any(raw_idem in json.dumps(line, ensure_ascii=False) for line in handler.lines):
            failures.append("raw idempotency key leaked into probe logs")

        if missing_logs and not attempts:
            failures.extend(f"missing traced log {name}" for name in missing_logs)

        return {
            "http": http_info,
            "first_batch": first,
            "second_batch": second,
            "final_status": final,
            "attempts": dict(attempts),
            "trace_id": HTTP_TRACE_ID,
            "http_request_id": HTTP_REQUEST_ID,
            "log_messages": sorted(msg for msg in traced_msgs if msg),
            "log_warnings": missing_logs,
            "passed": not failures,
            "failures": failures,
        }
    finally:
        root.removeHandler(handler)
        root.setLevel(previous_level)
        for item, level, propagate in previous_logger_state:
            item.removeHandler(handler)
            item.setLevel(level)
            item.propagate = propagate


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe outbox trace continuity")
    parser.add_argument("--base-url")
    parser.add_argument("--output", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    from config.database import SessionLocal

    report = run_probe(SessionLocal, base_url=args.base_url)
    encoded = json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    sys.stdout.write(encoded)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
