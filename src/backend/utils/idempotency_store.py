"""Database-backed idempotency state machine and optional Redis success cache."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import logging
from typing import Callable, Literal
from uuid import uuid4

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from config.database import SessionLocal
from models.idempotency_record import IdempotencyRecord


logger = logging.getLogger(__name__)

IDEMPOTENCY_PREFIX = "idem"
STATUS_PROCESSING = "PROCESSING"
STATUS_SUCCEEDED = "SUCCEEDED"
STATUS_FAILED = "FAILED"
STATUS_EXPIRED = "EXPIRED"

ClaimResultKind = Literal["OWNED", "REPLAY", "IN_PROGRESS", "MISMATCH"]


@dataclass(frozen=True, slots=True)
class StoredResponse:
    http_status: int
    body: bytes
    media_type: str | None
    headers: dict[str, str]


@dataclass(frozen=True, slots=True)
class ClaimResult:
    kind: ClaimResultKind
    claim_token: str | None = None
    response: StoredResponse | None = None


_session_factory: Callable[[], Session] = SessionLocal


def set_session_factory(factory: Callable[[], Session]) -> None:
    """Override the middleware-owned Session factory, primarily for isolated tests."""
    global _session_factory
    _session_factory = factory


def reset_session_factory() -> None:
    global _session_factory
    _session_factory = SessionLocal


def _utcnow() -> datetime:
    # The project stores naive UTC DateTime values for SQLite/PostgreSQL parity.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _store_key(idempotency_key: str) -> str:
    return f"{IDEMPOTENCY_PREFIX}:{idempotency_key}"


def _to_stored_response(record: IdempotencyRecord) -> StoredResponse | None:
    if record.http_status is None or record.response_body is None:
        return None
    headers = record.response_headers if isinstance(record.response_headers, dict) else {}
    return StoredResponse(
        http_status=record.http_status,
        body=bytes(record.response_body),
        media_type=record.response_media_type,
        headers={str(key): str(value) for key, value in headers.items()},
    )


def _insert_claim(
    key: str,
    payload_hash: str,
    claim_token: str,
    expires_at: datetime,
) -> bool:
    session = _session_factory()
    try:
        session.add(
            IdempotencyRecord(
                idempotency_key=key,
                status=STATUS_PROCESSING,
                payload_hash=payload_hash,
                claim_token=claim_token,
                expires_at=expires_at,
            )
        )
        session.commit()
        return True
    except IntegrityError:
        session.rollback()
        return False
    finally:
        session.close()


def _read_record(key: str) -> IdempotencyRecord | None:
    session = _session_factory()
    try:
        record = (
            session.query(IdempotencyRecord)
            .filter(IdempotencyRecord.idempotency_key == key)
            .one_or_none()
        )
        if record is not None:
            session.expunge(record)
        return record
    finally:
        session.close()


def _reclaim_record(
    key: str,
    payload_hash: str,
    claim_token: str,
    expires_at: datetime,
    *,
    now: datetime,
) -> bool:
    session = _session_factory()
    try:
        result = session.execute(
            update(IdempotencyRecord)
            .where(
                IdempotencyRecord.idempotency_key == key,
                (
                    (IdempotencyRecord.status.in_([STATUS_FAILED, STATUS_EXPIRED]))
                    | (IdempotencyRecord.expires_at <= now)
                ),
            )
            .values(
                status=STATUS_PROCESSING,
                payload_hash=payload_hash,
                claim_token=claim_token,
                http_status=None,
                response_body=None,
                response_media_type=None,
                response_headers=None,
                expires_at=expires_at,
            )
        )
        session.commit()
        return result.rowcount == 1
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def claim_request(
    key: str,
    payload_hash: str,
    processing_lease_seconds: int = 120,
) -> ClaimResult:
    """Claim a key or classify its current durable state without waiting."""
    now = _utcnow()
    expires_at = now + timedelta(seconds=processing_lease_seconds)
    claim_token = str(uuid4())
    if _insert_claim(key, payload_hash, claim_token, expires_at):
        return ClaimResult("OWNED", claim_token=claim_token)

    record = _read_record(key)
    if record is None:
        retry_token = str(uuid4())
        if _insert_claim(key, payload_hash, retry_token, expires_at):
            return ClaimResult("OWNED", claim_token=retry_token)
        return ClaimResult("IN_PROGRESS")

    record_expired = record.status == STATUS_EXPIRED or record.expires_at <= now
    if (
        not record_expired
        and record.payload_hash is not None
        and record.payload_hash != payload_hash
    ):
        return ClaimResult("MISMATCH")

    if record.status == STATUS_SUCCEEDED and not record_expired:
        response = _to_stored_response(record)
        if response is not None:
            return ClaimResult("REPLAY", response=response)

    if record.status == STATUS_PROCESSING and not record_expired:
        return ClaimResult("IN_PROGRESS")

    reclaim_token = str(uuid4())
    if _reclaim_record(
        key,
        payload_hash,
        reclaim_token,
        expires_at,
        now=now,
    ):
        return ClaimResult("OWNED", claim_token=reclaim_token)

    current = _read_record(key)
    if current is None:
        return ClaimResult("IN_PROGRESS")

    current_expired = (
        current.status == STATUS_EXPIRED or current.expires_at <= _utcnow()
    )
    if (
        not current_expired
        and current.payload_hash is not None
        and current.payload_hash != payload_hash
    ):
        return ClaimResult("MISMATCH")
    if current.status == STATUS_SUCCEEDED and not current_expired:
        response = _to_stored_response(current)
        if response is not None:
            return ClaimResult("REPLAY", response=response)
    return ClaimResult("IN_PROGRESS")


def mark_succeeded(
    key: str,
    payload_hash: str,
    claim_token: str,
    *,
    http_status: int,
    body: bytes,
    media_type: str | None,
    headers: dict[str, str],
    retention_hours: int = 24,
) -> None:
    """Persist a replayable response only if the caller still owns PROCESSING."""
    replay_expires_at = _utcnow() + timedelta(hours=retention_hours)
    session = _session_factory()
    try:
        result = session.execute(
            update(IdempotencyRecord)
            .where(
                IdempotencyRecord.idempotency_key == key,
                IdempotencyRecord.payload_hash == payload_hash,
                IdempotencyRecord.claim_token == claim_token,
                IdempotencyRecord.status == STATUS_PROCESSING,
            )
            .values(
                status=STATUS_SUCCEEDED,
                claim_token=None,
                http_status=http_status,
                response_body=body,
                response_media_type=media_type,
                response_headers=headers,
                expires_at=replay_expires_at,
            )
        )
        if result.rowcount != 1:
            raise RuntimeError("idempotency owner lost before success finalization")
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def mark_failed(key: str, payload_hash: str, claim_token: str) -> None:
    """Release a failed owner for an explicit future retry; failure bodies are not replayed."""
    session = _session_factory()
    try:
        session.execute(
            update(IdempotencyRecord)
            .where(
                IdempotencyRecord.idempotency_key == key,
                IdempotencyRecord.payload_hash == payload_hash,
                IdempotencyRecord.claim_token == claim_token,
                IdempotencyRecord.status == STATUS_PROCESSING,
            )
            .values(
                status=STATUS_FAILED,
                claim_token=None,
                http_status=None,
                response_body=None,
                response_media_type=None,
                response_headers=None,
            )
        )
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def cache_succeeded_response(
    key: str,
    response: StoredResponse,
    ttl_hours: int = 24,
) -> None:
    """Best-effort Redis-only cache; never falls back to process memory."""
    try:
        from utils import cache as cache_module

        client = cache_module.resolve_redis()
        if client is None:
            return
        payload = json.dumps(
            {
                "http_status": response.http_status,
                "body": response.body.decode("latin1"),
                "media_type": response.media_type,
                "headers": response.headers,
            },
            ensure_ascii=False,
        )
        await client.setex(_store_key(key), ttl_hours * 3600, payload)
    except Exception as exc:  # pragma: no cover - depends on external Redis
        logger.warning("Redis idempotency cache write failed: exception=%s", type(exc).__name__)
