"""PostgreSQL deadlock, serialization, pool timeout, and outbox reclaim."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select, text, update
from sqlalchemy.exc import TimeoutError as SATimeoutError
from sqlalchemy.orm import sessionmaker

from config.database_url import engine_create_kwargs
from core.db_retry import retry_transient_pg
from models.global_schedule import GlobalSchedule
from models.outbox_event import OutboxEvent
from services.outbox_service import claim_outbox_batch, enqueue_outbox, finalize_claimed_event


def _schedule(code: str) -> GlobalSchedule:
    return GlobalSchedule(
        schedule_code=code,
        order_codes=["P1-F001"],
        goods_schedules=[],
        total_distance=1,
        total_time=1,
        total_goods=1,
        score=1,
        algorithm_type="traditional",
        status="draft",
        version=1,
        is_replan=False,
    )


@pytest.mark.integration
def test_postgres_deadlock_retries_without_duplicate_side_effects(p1_postgres, p1_row_cleanup):
    _engine, factory = p1_postgres
    codes = [f"P1-DL-{uuid4().hex[:12]}-{i}" for i in range(2)]
    seed = factory()
    try:
        rows = [_schedule(code) for code in codes]
        seed.add_all(rows)
        seed.commit()
        ids = [row.id for row in rows]
    finally:
        seed.close()
    p1_row_cleanup(
        GlobalSchedule,
        filters={GlobalSchedule: GlobalSchedule.schedule_code.in_(codes)},
    )

    barrier = Barrier(2)

    def worker(order: tuple[int, int], score: int) -> str:
        session = factory()
        first_id, second_id = order
        attempts = {"n": 0}

        def work() -> None:
            session.execute(
                update(GlobalSchedule)
                .where(GlobalSchedule.id == first_id)
                .values(score=score)
            )
            session.flush()
            if attempts["n"] == 0:
                barrier.wait()
            attempts["n"] += 1
            session.execute(
                update(GlobalSchedule)
                .where(GlobalSchedule.id == second_id)
                .values(score=score + 10)
            )
            session.commit()

        try:
            retry_transient_pg(work, on_retry=session.rollback, attempts=6, backoff_seconds=0.05)
            return "ok"
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda item: worker(*item),
                [((ids[0], ids[1]), 3), ((ids[1], ids[0]), 7)],
            )
        )

    assert results == ["ok", "ok"]
    verify = factory()
    try:
        stored = {
            row.id: row.score
            for row in verify.query(GlobalSchedule).filter(GlobalSchedule.id.in_(ids))
        }
        assert set(stored) == set(ids)
        assert all(value in {3, 7, 13, 17} for value in stored.values())
    finally:
        verify.close()


@pytest.mark.integration
def test_postgres_serialization_failure_is_retried(p1_postgres, p1_row_cleanup):
    engine, factory = p1_postgres
    code = f"P1-SER-{uuid4().hex[:16]}"
    seed = factory()
    try:
        row = _schedule(code)
        seed.add(row)
        seed.commit()
        row_id = row.id
    finally:
        seed.close()
    p1_row_cleanup(
        GlobalSchedule,
        filters={GlobalSchedule: GlobalSchedule.schedule_code == code},
    )

    barrier = Barrier(2)

    def worker() -> None:
        attempts = {"n": 0}
        with engine.connect().execution_options(isolation_level="SERIALIZABLE") as conn:
            def work() -> None:
                trans = conn.begin()
                try:
                    current = conn.execute(
                        text("SELECT version FROM global_schedules WHERE id = :id"),
                        {"id": row_id},
                    ).scalar_one()
                    if attempts["n"] == 0:
                        barrier.wait()
                    attempts["n"] += 1
                    conn.execute(
                        text(
                            "UPDATE global_schedules SET version = :version WHERE id = :id"
                        ),
                        {"version": int(current) + 1, "id": row_id},
                    )
                    trans.commit()
                except Exception:
                    trans.rollback()
                    raise

            retry_transient_pg(work, attempts=6, backoff_seconds=0.05)

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _: worker(), range(2)))

    verify = factory()
    try:
        stored = verify.get(GlobalSchedule, row_id)
        assert stored.version >= 2
    finally:
        verify.close()


@pytest.mark.integration
def test_postgres_pool_timeout_is_stable(p1_database_url):
    engine = create_engine(
        p1_database_url,
        **engine_create_kwargs(
            p1_database_url,
            pool_size=1,
            max_overflow=0,
            pool_timeout=1,
        ),
    )
    try:
        first = engine.connect()
        try:
            with pytest.raises(SATimeoutError):
                engine.connect()
        finally:
            first.close()
    finally:
        engine.dispose()


@pytest.mark.integration
def test_postgres_stale_outbox_token_cannot_complete(p1_postgres, p1_row_cleanup):
    _engine, factory = p1_postgres
    dedup_key = f"p1-stale-{uuid4().hex}"
    session = factory()
    try:
        event = enqueue_outbox(
            session,
            dedup_key=dedup_key,
            event_type="p1.fault",
            payload={"scenario": "stale-token"},
        )
        session.commit()
        event_id = event.id
        first = claim_outbox_batch(
            session, worker_id="old-worker", limit=1, lease_seconds=60
        )
        old_token = first[0].claim_token
        first[0].lease_until = datetime.utcnow() - timedelta(seconds=5)
        session.commit()
        reclaimed = claim_outbox_batch(
            session, worker_id="new-worker", limit=1, lease_seconds=60
        )
        assert reclaimed[0].claim_token != old_token
        assert (
            finalize_claimed_event(
                session,
                event_id=event_id,
                claim_token=old_token,
                worker_id="old-worker",
                ok=True,
                error="",
                permanent_failure=False,
                max_retries=3,
                retry_delay_seconds=1,
            )
            == "stale"
        )
        stored = session.get(OutboxEvent, event_id)
        session.refresh(stored)
        assert stored.claimed_by == "new-worker"
        assert stored.status == "processing"
    finally:
        session.close()
    p1_row_cleanup(
        OutboxEvent,
        filters={OutboxEvent: OutboxEvent.dedup_key == dedup_key},
    )
