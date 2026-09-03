"""Prove HTTP -> outbox -> worker trace continuity for success, retry, and dead-letter."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
import logging
from pathlib import Path
import sys
import time
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
PROBE_PATH = "/api/debug/write-path-probe"
PROBE_KEYS = ("write-path-success", "write-path-retry", "write-path-dead")
EXPECTED_STATUS = {
    "write-path-success": "delivered",
    "write-path-retry": "delivered",
    "write-path-dead": "dead-letter",
}
PROBE_EVENT_TYPES = {
    "write-path-success": "write_path_probe.success",
    "write-path-retry": "write_path_probe.retry",
    "write-path-dead": "write_path_probe.dead",
}


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


def _probe_headers() -> dict[str, str]:
    return {
        "X-Request-ID": HTTP_REQUEST_ID,
        "X-Trace-ID": HTTP_TRACE_ID,
        "X-Task-ID": HTTP_TASK_ID,
        "Content-Type": "application/json",
    }


def probe_http(base_url: str, *, enqueue: bool = False) -> dict[str, Any]:
    path = PROBE_PATH if enqueue else "/api/health"
    url = base_url.rstrip("/") + path
    request = Request(
        url,
        data=b"{}" if enqueue else None,
        method="POST" if enqueue else "GET",
        headers=_probe_headers(),
    )
    with urlopen(request, timeout=10) as response:
        body: dict[str, Any] = {}
        raw = response.read()
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            parsed = None
        if isinstance(parsed, dict):
            body = parsed
        return {
            "status": response.status,
            "request_id": response.headers.get("X-Request-ID"),
            "trace_id": response.headers.get("X-Trace-ID"),
            "task_id": response.headers.get("X-Task-ID"),
            "path": path,
            "body": body,
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
        for dedup_key, event_type in PROBE_EVENT_TYPES.items():
            enqueue_outbox(
                db,
                dedup_key=dedup_key,
                event_type=event_type,
                payload={"task_id": HTTP_TASK_ID, "case": dedup_key.rsplit("-", 1)[-1]},
            )
        db.commit()
    finally:
        reset_request_context(token)


def _load_statuses(session_factory: sessionmaker) -> dict[str, str]:
    db = session_factory()
    try:
        return {
            event.dedup_key: event.status
            for event in db.query(OutboxEvent).filter(OutboxEvent.dedup_key.in_(PROBE_KEYS)).all()
        }
    finally:
        db.close()


def _wait_for_worker(session_factory: sessionmaker, timeout: float) -> dict[str, str]:
    deadline = time.time() + timeout
    final: dict[str, str] = {}
    while time.time() < deadline:
        final = _load_statuses(session_factory)
        if final == EXPECTED_STATUS:
            return final
        time.sleep(0.2)
    return final


def parse_worker_attempts(path: Path) -> dict[str, list[dict[str, str]]]:
    """Rebuild per-execution IDs from an independent worker JSON log."""
    attempts: dict[str, list[dict[str, str]]] = defaultdict(list)
    if not path.exists():
        return attempts
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line.startswith("{"):
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        if payload.get("msg") != "outbox_execute":
            continue
        if payload.get("trace_id") != HTTP_TRACE_ID:
            continue
        key = str(payload.get("dedup_key") or "")
        if key not in PROBE_KEYS:
            continue
        attempts[key].append(
            {
                "request_id": str(payload.get("request_id") or ""),
                "trace_id": str(payload.get("trace_id") or ""),
                "parent_request_id": str(payload.get("parent_request_id") or ""),
                "task_id": str(payload.get("task_id") or ""),
            }
        )
    return attempts


def parse_worker_messages(path: Path) -> set[str]:
    messages: set[str] = set()
    if not path.exists():
        return messages
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line.startswith("{"):
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        if payload.get("trace_id") != HTTP_TRACE_ID:
            continue
        msg = payload.get("msg")
        if msg:
            messages.add(str(msg))
    return messages


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


def _collect_http(base_url: str | None, *, enqueue: bool = False) -> tuple[dict[str, Any] | None, list[str]]:
    failures: list[str] = []
    http_info = None
    if not base_url:
        return http_info, failures
    try:
        http_info = probe_http(base_url, enqueue=enqueue)
    except (URLError, OSError, TimeoutError) as exc:
        failures.append(f"http probe failed: {exc}")
        return http_info, failures
    if http_info.get("trace_id") != HTTP_TRACE_ID:
        failures.append("HTTP trace_id mismatch")
    if http_info.get("request_id") != HTTP_REQUEST_ID:
        failures.append("HTTP request_id mismatch")
    if enqueue and http_info.get("status") != 200:
        failures.append(f"HTTP write-path probe status {http_info.get('status')}")
    if enqueue:
        body = http_info.get("body") if isinstance(http_info.get("body"), dict) else {}
        code = body.get("code")
        if code not in (None, 0):
            failures.append(f"HTTP write-path probe code {code}")
    return http_info, failures


def _assert_payload_trace(session_factory: sessionmaker, failures: list[str]) -> None:
    db = session_factory()
    try:
        events = {
            event.dedup_key: event
            for event in db.query(OutboxEvent).filter(OutboxEvent.dedup_key.in_(PROBE_KEYS)).all()
        }
        for key in PROBE_KEYS:
            event = events.get(key)
            if event is None:
                failures.append(f"missing outbox row {key}")
                continue
            nested = (event.payload or {}).get("_trace") if isinstance(event.payload, dict) else None
            if not isinstance(nested, dict):
                failures.append(f"{key} missing _trace metadata")
                continue
            if nested.get("trace_id") != HTTP_TRACE_ID:
                failures.append(f"{key} payload trace_id mismatch")
            if nested.get("request_id") != HTTP_REQUEST_ID:
                failures.append(f"{key} payload request_id mismatch")
            if not isinstance(event.payload, dict) or event.payload.get("case") != key.rsplit("-", 1)[-1]:
                failures.append(f"{key} business payload overwritten")
    finally:
        db.close()


def _assert_attempts(attempts: dict[str, list[dict[str, str]]], failures: list[str]) -> None:
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


def run_probe(
    session_factory: sessionmaker,
    *,
    base_url: str | None = None,
    wait_worker: bool = False,
    worker_log: Path | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
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
        logging.getLogger("scripts.outbox_worker"),
        logger,
    ]
    previous_logger_state = []
    for item in watched:
        previous_logger_state.append((item, item.level, item.propagate))
        item.setLevel(logging.INFO)
        item.addHandler(handler)
        item.propagate = False

    try:
        failures: list[str] = []
        http_info, http_failures = _collect_http(base_url, enqueue=wait_worker)
        failures.extend(http_failures)

        if wait_worker:
            if not base_url:
                failures.append("wait-worker requires --base-url for HTTP outbox enqueue")
            elif http_info is None:
                failures.append("HTTP write-path probe did not enqueue outbox events")
        else:
            db = session_factory()
            try:
                _enqueue_cases(db)
            finally:
                db.close()
        _assert_payload_trace(session_factory, failures)

        if wait_worker:
            if worker_log is None:
                failures.append("wait-worker requires --worker-log")
                final = _load_statuses(session_factory)
                attempts = {}
                first = {}
                second = {}
                traced_msgs = set()
            else:
                final = _wait_for_worker(session_factory, timeout)
                attempts = parse_worker_attempts(worker_log)
                traced_msgs = parse_worker_messages(worker_log)
                retry_attempts = len(attempts.get("write-path-retry", []))
                first = {
                    "delivered": 1 if final.get("write-path-success") == "delivered" else 0,
                    "retry": 1 if retry_attempts >= 1 else 0,
                    "dead-letter": 1 if final.get("write-path-dead") == "dead-letter" else 0,
                }
                second = {
                    "delivered": 1 if retry_attempts >= 2 and final.get("write-path-retry") == "delivered" else 0,
                    "retry": 0,
                    "dead-letter": 0,
                }
        else:
            attempts = defaultdict(list)
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
            final = _load_statuses(session_factory)
            traced_msgs = {
                line.get("msg")
                for line in handler.lines
                if line.get("trace_id") == HTTP_TRACE_ID
                or line.get("msg")
                in {
                    "outbox_execute",
                    "outbox_outcome",
                    "worker_handle",
                    "notification_dead_letter",
                    "notification_delivered",
                }
            }

        if final != EXPECTED_STATUS:
            failures.append(f"unexpected outbox statuses: {final}")
        if first.get("delivered", 0) < 1 or first.get("retry", 0) < 1 or first.get("dead-letter", 0) < 1:
            failures.append(f"first batch missing outcomes: {first}")
        if second.get("delivered", 0) < 1:
            failures.append(f"retry batch did not deliver: {second}")
        if wait_worker and worker_log is not None and not worker_log.exists():
            failures.append(f"independent worker log missing: {worker_log}")
        if wait_worker and not attempts:
            failures.append("independent worker log had no traced outbox_execute lines")

        _assert_attempts(attempts, failures)

        missing_logs = [
            name
            for name in ("outbox_execute", "outbox_outcome", "worker_handle", "notification_dead_letter")
            if name not in traced_msgs
        ]
        raw_idem = "idem-write-path-probe"
        log_source = list(handler.lines)
        if wait_worker and worker_log is not None and worker_log.exists():
            for raw in worker_log.read_text(encoding="utf-8", errors="replace").splitlines():
                if raw.strip().startswith("{"):
                    try:
                        log_source.append(json.loads(raw))
                    except json.JSONDecodeError:
                        continue
        if any(raw_idem in json.dumps(line, ensure_ascii=False) for line in log_source):
            failures.append("raw idempotency key leaked into probe logs")
        if missing_logs and (wait_worker or not attempts):
            failures.extend(f"missing traced log {name}" for name in missing_logs)

        return {
            "http": http_info,
            "worker_mode": "independent" if wait_worker else "in-process",
            "enqueue_source": "http" if wait_worker else "in-process",
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
    parser.add_argument("--wait-worker", action="store_true")
    parser.add_argument("--worker-log", type=Path)
    parser.add_argument("--timeout", type=float, default=30.0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    from config.database import SessionLocal

    report = run_probe(
        SessionLocal,
        base_url=args.base_url,
        wait_worker=args.wait_worker,
        worker_log=args.worker_log,
        timeout=args.timeout,
    )
    encoded = json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    sys.stdout.write(encoded)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
