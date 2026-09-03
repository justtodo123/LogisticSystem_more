"""Request-scoped IDs and caller context for logs, metrics, and SQL comments."""

from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass, fields, replace
import re
import uuid

REQUEST_ID_HEADER = "X-Request-ID"
TRACE_ID_HEADER = "X-Trace-ID"
TASK_ID_HEADER = "X-Task-ID"

_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")

_current: ContextVar["RequestContext | None"] = ContextVar(
    "r2_request_context",
    default=None,
)


@dataclass(frozen=True, slots=True)
class RequestContext:
    request_id: str
    trace_id: str
    task_id: str | None = None
    user_id: str | None = None
    role: str | None = None
    idempotency_key: str | None = None
    parent_request_id: str | None = None


def generate_id() -> str:
    return uuid.uuid4().hex


def normalize_id(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if not _ID_RE.fullmatch(candidate):
        return None
    return candidate


def get_request_context() -> RequestContext | None:
    return _current.get()


def bind_request_context(context: RequestContext) -> Token[RequestContext | None]:
    return _current.set(context)


def reset_request_context(token: Token[RequestContext | None] | None = None) -> None:
    if token is not None:
        _current.reset(token)
        return
    _current.set(None)


def update_request_context(**changes: str | None) -> RequestContext | None:
    current = _current.get()
    if current is None:
        return None
    allowed = {item.name for item in fields(RequestContext)}
    payload = {key: value for key, value in changes.items() if key in allowed}
    if not payload:
        return current
    updated = replace(current, **payload)
    _current.set(updated)
    return updated


def context_as_dict(context: RequestContext | None = None) -> dict[str, str]:
    current = context if context is not None else _current.get()
    if current is None:
        return {}
    payload = {
        "request_id": current.request_id,
        "trace_id": current.trace_id,
    }
    if current.task_id:
        payload["task_id"] = current.task_id
    if current.user_id:
        payload["user_id"] = current.user_id
    if current.role:
        payload["role"] = current.role
    if current.idempotency_key:
        payload["idempotency_key"] = current.idempotency_key
    if current.parent_request_id:
        payload["parent_request_id"] = current.parent_request_id
    return payload
