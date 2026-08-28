"""Direct tests for the database-backed idempotency state machine."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from models.base import Base
from models.idempotency_record import IdempotencyRecord
from utils.idempotency_store import (
    STATUS_FAILED,
    STATUS_PROCESSING,
    STATUS_SUCCEEDED,
    claim_request,
    mark_failed,
    mark_succeeded,
    reset_session_factory,
    set_session_factory,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@pytest.fixture
def idempotency_store(tmp_path):
    database = tmp_path / "idempotency-state.db"
    engine = create_engine(
        f"sqlite:///{database.as_posix()}",
        connect_args={"check_same_thread": False, "timeout": 30},
        poolclass=NullPool,
    )

    @event.listens_for(engine, "connect")
    def _set_busy_timeout(dbapi_connection, _connection_record):
        dbapi_connection.execute("PRAGMA busy_timeout=30000")

    Base.metadata.create_all(engine, tables=[IdempotencyRecord.__table__])
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    set_session_factory(factory)
    try:
        yield factory
    finally:
        reset_session_factory()
        engine.dispose()


def _record(factory, key: str) -> IdempotencyRecord:
    with factory() as session:
        record = session.scalar(
            select(IdempotencyRecord).where(IdempotencyRecord.idempotency_key == key)
        )
        assert record is not None
        session.expunge(record)
        return record


def test_claim_success_replay_and_payload_mismatch(idempotency_store):
    owned = claim_request("state-key", "hash-a")
    assert owned.kind == "OWNED"
    assert owned.claim_token

    mark_succeeded(
        "state-key",
        "hash-a",
        owned.claim_token,
        http_status=201,
        body=b"\x00binary-response\xff",
        media_type="application/octet-stream",
        headers={"X-Request-ID": "request-1"},
    )

    replay = claim_request("state-key", "hash-a")
    assert replay.kind == "REPLAY"
    assert replay.response is not None
    assert replay.response.http_status == 201
    assert replay.response.body == b"\x00binary-response\xff"
    assert replay.response.media_type == "application/octet-stream"
    assert replay.response.headers == {"X-Request-ID": "request-1"}
    assert claim_request("state-key", "hash-b").kind == "MISMATCH"

    with idempotency_store() as session:
        record = session.scalar(
            select(IdempotencyRecord).where(
                IdempotencyRecord.idempotency_key == "state-key"
            )
        )
        record.expires_at = _utcnow() - timedelta(seconds=1)
        session.commit()

    expired_reuse = claim_request("state-key", "hash-b")
    assert expired_reuse.kind == "OWNED"
    assert expired_reuse.claim_token != owned.claim_token


def test_processing_failed_and_expired_records_are_handled(idempotency_store):
    first = claim_request("retry-key", "hash-a")
    assert first.kind == "OWNED"
    assert first.claim_token is not None
    assert claim_request("retry-key", "hash-a").kind == "IN_PROGRESS"

    mark_failed("retry-key", "hash-a", first.claim_token)
    assert _record(idempotency_store, "retry-key").status == STATUS_FAILED

    retry = claim_request("retry-key", "hash-a")
    assert retry.kind == "OWNED"
    assert retry.claim_token != first.claim_token

    with idempotency_store() as session:
        record = session.scalar(
            select(IdempotencyRecord).where(
                IdempotencyRecord.idempotency_key == "retry-key"
            )
        )
        record.expires_at = _utcnow() - timedelta(seconds=1)
        session.commit()

    reclaimed = claim_request("retry-key", "hash-a")
    assert reclaimed.kind == "OWNED"
    assert reclaimed.claim_token != retry.claim_token


def test_stale_owner_cannot_finalize_reclaimed_record(idempotency_store):
    first = claim_request("fencing-key", "hash-a")
    assert first.claim_token is not None
    with idempotency_store() as session:
        record = session.scalar(
            select(IdempotencyRecord).where(
                IdempotencyRecord.idempotency_key == "fencing-key"
            )
        )
        record.expires_at = _utcnow() - timedelta(seconds=1)
        session.commit()

    second = claim_request("fencing-key", "hash-a")
    assert second.kind == "OWNED"
    assert second.claim_token is not None
    with pytest.raises(RuntimeError, match="owner lost"):
        mark_succeeded(
            "fencing-key",
            "hash-a",
            first.claim_token,
            http_status=200,
            body=b"stale",
            media_type="text/plain",
            headers={},
        )

    mark_succeeded(
        "fencing-key",
        "hash-a",
        second.claim_token,
        http_status=200,
        body=b"current",
        media_type="text/plain",
        headers={},
    )
    record = _record(idempotency_store, "fencing-key")
    assert record.status == STATUS_SUCCEEDED
    assert record.response_body == b"current"


@pytest.mark.parametrize("contenders", [20, 100])
def test_concurrent_claims_have_one_owner(idempotency_store, contenders):
    def contend(_index: int) -> str:
        return claim_request("concurrent-key", "hash-a").kind

    with ThreadPoolExecutor(max_workers=contenders) as executor:
        results = list(executor.map(contend, range(contenders)))

    assert results.count("OWNED") == 1
    assert results.count("IN_PROGRESS") == contenders - 1
    record = _record(idempotency_store, "concurrent-key")
    assert record.status == STATUS_PROCESSING
