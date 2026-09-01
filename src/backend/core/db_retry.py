"""Retry only PostgreSQL deadlock and serialization failures."""
from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TypeVar

from sqlalchemy.exc import DBAPIError

from config.settings import settings
from core.error_codes import CODE_DATABASE_ERROR
from core.errors import DomainError


logger = logging.getLogger(__name__)

TRANSIENT_PGCODES = frozenset({"40001", "40P01"})
T = TypeVar("T")


def pgcode_of(exc: BaseException) -> str | None:
    orig = getattr(exc, "orig", None)
    code = getattr(orig, "pgcode", None) or getattr(orig, "sqlstate", None)
    if code:
        return str(code)
    diag = getattr(orig, "diag", None)
    sqlstate = getattr(diag, "sqlstate", None) if diag is not None else None
    return str(sqlstate) if sqlstate else None


def is_transient_pg(exc: BaseException) -> bool:
    """True only for serialization failure (40001) or deadlock (40P01)."""
    if not isinstance(exc, DBAPIError):
        return False
    return pgcode_of(exc) in TRANSIENT_PGCODES


def retry_transient_pg(
    operation: Callable[[], T],
    *,
    on_retry: Callable[[], None] | None = None,
    attempts: int | None = None,
    backoff_seconds: float | None = None,
) -> T:
    """Retry a unit of work a limited number of times, then raise a stable DomainError."""
    max_attempts = attempts if attempts is not None else settings.DB_TRANSIENT_RETRY_ATTEMPTS
    backoff = (
        backoff_seconds
        if backoff_seconds is not None
        else settings.DB_TRANSIENT_RETRY_BACKOFF_MS / 1000.0
    )
    last: BaseException | None = None
    for index in range(max_attempts):
        try:
            return operation()
        except Exception as exc:  # noqa: BLE001 - must inspect pgcode then re-raise
            last = exc
            retryable = is_transient_pg(exc)
            if not retryable:
                raise
            if index >= max_attempts - 1:
                logger.warning("pg_transient_exhausted pgcode=%s", pgcode_of(exc))
                raise DomainError(CODE_DATABASE_ERROR) from exc
            logger.warning(
                "pg_transient_retry pgcode=%s attempt=%s",
                pgcode_of(exc),
                index + 1,
            )
            if on_retry is not None:
                on_retry()
            time.sleep(backoff * (2 ** index))
    assert last is not None
    raise last
