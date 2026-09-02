"""Annotate SQL statements with request/trace/task IDs for log correlation."""

from __future__ import annotations

from sqlalchemy import event
from sqlalchemy.engine import Engine

from core.request_context import get_request_context


def _sql_comment() -> str | None:
    context = get_request_context()
    if context is None:
        return None
    parts = [
        f"request_id={context.request_id}",
        f"trace_id={context.trace_id}",
    ]
    if context.task_id:
        parts.append(f"task_id={context.task_id}")
    return " /* " + " ".join(parts) + " */"


def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    comment = _sql_comment()
    if comment is None or not isinstance(statement, str):
        return statement, parameters
    if "request_id=" in statement:
        return statement, parameters
    return statement + comment, parameters


def instrument_engine(engine: Engine) -> Engine:
    """Idempotently attach SQL comment instrumentation to an engine."""
    if getattr(engine, "_r2_sql_comments", False):
        return engine
    event.listen(engine, "before_cursor_execute", _before_cursor_execute, retval=True)
    engine._r2_sql_comments = True  # type: ignore[attr-defined]
    return engine
