"""Lightweight dependency-call instrumentation for R2-06.

Records low-cardinality counters and structured logs. Never log tokens,
cookies, or raw URL query strings.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
import logging
import re
import time
from typing import Any

from core.metrics import metrics
from core.request_context import (
    REQUEST_ID_HEADER,
    TASK_ID_HEADER,
    TRACE_ID_HEADER,
    get_request_context,
)

logger = logging.getLogger(__name__)

_SUCCESS_STATUSES = frozenset({"ok", "hit", "miss", "skip"})
_UNSAFE_LABEL_RE = re.compile(r"(://|[/?&=@]|user_id|order_id|token)", re.IGNORECASE)


def bounded_label(value: object, limit: int) -> str:
    """Keep metric/log labels short and free of URLs, tokens, and identifiers."""
    text = str(value or "").strip()
    if not text or _UNSAFE_LABEL_RE.search(text):
        return "redacted"[:limit]
    return text[:limit]


def outbound_trace_headers(extra: Mapping[str, str] | None = None) -> dict[str, str]:
    """Propagate request/trace IDs to HTTP dependencies without copying secrets."""
    headers = {str(key): str(value) for key, value in dict(extra or {}).items()}
    context = get_request_context()
    if context is None:
        return headers
    headers.setdefault(REQUEST_ID_HEADER, context.request_id)
    headers.setdefault(TRACE_ID_HEADER, context.trace_id)
    if context.task_id:
        headers.setdefault(TASK_ID_HEADER, context.task_id)
    return headers


def observe_dependency(
    *,
    dependency: str,
    operation: str,
    status: str,
    duration_ms: float,
    error_type: str | None = None,
) -> None:
    dep = bounded_label(dependency, 32)
    op = bounded_label(operation, 64)
    st = bounded_label(status, 32)
    metrics.inc("dependency_calls_total", dependency=dep, operation=op, status=st)
    if st not in _SUCCESS_STATUSES:
        metrics.inc(
            "dependency_errors_total",
            dependency=dep,
            operation=op,
            error_type=bounded_label(error_type or st, 64),
        )
    extra: dict[str, Any] = {
        "dependency": dep,
        "operation": op,
        "call_status": st,
        "duration_ms": round(float(duration_ms), 2),
    }
    if error_type:
        extra["error_type"] = bounded_label(error_type, 64)
    logger.info("dependency_call", extra=extra)


@contextmanager
def track_dependency(dependency: str, operation: str) -> Iterator[dict[str, Any]]:
    started = time.perf_counter()
    state: dict[str, Any] = {"status": "ok", "error_type": None}
    try:
        yield state
    except Exception as exc:
        if state.get("status") == "ok":
            state["status"] = "error"
        state["error_type"] = type(exc).__name__
        raise
    finally:
        observe_dependency(
            dependency=dependency,
            operation=operation,
            status=str(state.get("status") or "ok"),
            duration_ms=(time.perf_counter() - started) * 1000,
            error_type=state.get("error_type"),
        )
