"""Structured JSON logging with request context and sensitive-field redaction."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
import hashlib
import json
import logging
import re
from typing import Any

from core.request_context import context_as_dict, get_request_context

_SENSITIVE_KEY_RE = re.compile(
    r"(password|passwd|secret|token|authorization|cookie|set-cookie|"
    r"api[_-]?key|jwt|dsn|database_url|access_token|refresh_token|private)",
    re.IGNORECASE,
)
_REDACTED = "[REDACTED]"
_MAX_MESSAGE = 2048
_MAX_VALUE = 512
_IDEMPOTENCY_FINGERPRINT_RE = re.compile(r"^idem-[0-9a-f]{16}$")
_IDEMPOTENCY_KEY_NAMES = frozenset({"idempotency_key", "idempotency-key"})
_STANDARD_RECORD_KEYS = frozenset(
    {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "message",
        "taskName",
        "request_id",
        "trace_id",
        "task_id",
        "user_id",
        "role",
        "idempotency_key",
        "parent_request_id",
    }
)


def fingerprint_idempotency_key(value: str | None) -> str | None:
    """Hash caller-provided idempotency keys before they reach logs."""
    if not value or value == "-":
        return None
    candidate = str(value)
    if _IDEMPOTENCY_FINGERPRINT_RE.fullmatch(candidate):
        return candidate
    digest = hashlib.sha256(candidate.encode("utf-8")).hexdigest()[:16]
    return f"idem-{digest}"


def redact_value(key: str, value: Any) -> Any:
    key_name = str(key)
    if key_name.lower() in _IDEMPOTENCY_KEY_NAMES:
        if value is None:
            return value
        return fingerprint_idempotency_key(str(value)) or _REDACTED
    if _SENSITIVE_KEY_RE.search(key_name):
        return _REDACTED
    if isinstance(value, Mapping):
        return redact_mapping(value)
    if isinstance(value, list):
        return [redact_value(str(index), item) for index, item in enumerate(value[:20])]
    if isinstance(value, str):
        if _SENSITIVE_KEY_RE.search(value) and ("=" in value or "://" in value):
            return _REDACTED
        if len(value) > _MAX_VALUE:
            return value[:_MAX_VALUE] + "..."
        return value
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return str(value)[:_MAX_VALUE]


def redact_mapping(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        return {}
    return {
        str(key): redact_value(str(key), value)
        for key, value in list(payload.items())[:40]
    }


class RequestContextFilter(logging.Filter):
    """Copy request context onto every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        context = context_as_dict()
        record.request_id = context.get("request_id", "-")
        record.trace_id = context.get("trace_id", "-")
        record.task_id = context.get("task_id", "-")
        record.user_id = context.get("user_id", "-")
        record.role = context.get("role", "-")
        record.idempotency_key = fingerprint_idempotency_key(context.get("idempotency_key")) or "-"
        record.parent_request_id = context.get("parent_request_id", "-")
        return True


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per line; never include request bodies or secrets."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage()[:_MAX_MESSAGE],
        }
        record_ctx = {
            "request_id": getattr(record, "request_id", None),
            "trace_id": getattr(record, "trace_id", None),
            "task_id": getattr(record, "task_id", None),
            "user_id": getattr(record, "user_id", None),
            "role": getattr(record, "role", None),
            "idempotency_key": getattr(record, "idempotency_key", None),
            "parent_request_id": getattr(record, "parent_request_id", None),
        }
        for key, value in record_ctx.items():
            if isinstance(value, str) and value and value != "-":
                if key == "idempotency_key":
                    fingerprinted = fingerprint_idempotency_key(value)
                    if fingerprinted:
                        payload[key] = fingerprinted
                    continue
                payload[key] = value
        for key, value in context_as_dict(get_request_context()).items():
            if key == "idempotency_key":
                fingerprinted = fingerprint_idempotency_key(value)
                if fingerprinted:
                    payload.setdefault(key, fingerprinted)
                continue
            payload.setdefault(key, value)
        extra = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _STANDARD_RECORD_KEYS and not key.startswith("_")
        }
        if extra:
            payload.update(redact_mapping(extra))
        if record.exc_info and record.exc_info[0] is not None:
            payload["exc_type"] = record.exc_info[0].__name__
        return json.dumps(redact_mapping(payload), ensure_ascii=False, default=str)


def configure_logging(*, force: bool = False) -> None:
    """Attach JSON formatting without wiping pytest/uvicorn handlers."""
    from config.settings import settings

    root = logging.getLogger()
    ctx_filter = RequestContextFilter()
    if not any(isinstance(item, RequestContextFilter) for item in root.filters):
        root.addFilter(ctx_filter)

    level_name = str(getattr(settings, "LOG_LEVEL", "INFO") or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    has_json = any(isinstance(handler.formatter, JsonFormatter) for handler in root.handlers)
    if root.handlers and has_json and getattr(root, "_r2_json_logging", False) and not force:
        return

    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        handler.addFilter(ctx_filter)
        root.addHandler(handler)
        root.setLevel(level)
    else:
        for handler in root.handlers:
            if not isinstance(handler.formatter, JsonFormatter):
                handler.setFormatter(JsonFormatter())
            if not any(isinstance(item, RequestContextFilter) for item in handler.filters):
                handler.addFilter(ctx_filter)
        if root.level == logging.NOTSET:
            root.setLevel(level)
    root._r2_json_logging = True  # type: ignore[attr-defined]
