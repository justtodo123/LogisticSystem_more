from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from threading import Barrier, Lock
import asyncio
import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from core.error_codes import CODE_IDEMPOTENCY_PAYLOAD_MISMATCH, CODE_STATE_CONFLICT
from core.errors import DomainError
from models.notification_config import NotificationConfig
from models.outbox_event import OutboxEvent
from models.replan_task import ReplanTask
from services.replan_task_service import (
    build_request_fingerprint,
    claim_replan_step,
    resume,
    resume_async,
    start,
)


from models.base import Base
from models.registry import import_all_models

def _isolated_engine(prefix: str):
    import_all_models()
    db_dir = Path(__file__).resolve().parents[5] / "tmp"
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / f"{prefix}_{uuid.uuid4().hex}.db"
    engine = create_engine(
        f"sqlite:///{db_path.resolve().as_posix()}",
        connect_args={"check_same_thread": False, "timeout": 30},
        poolclass=NullPool,
    )
    with engine.begin() as connection:
        connection.execute(text("PRAGMA journal_mode=WAL"))
        connection.execute(text("PRAGMA busy_timeout=30000"))
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, factory


def _run_threaded(func, count: int):
    with ThreadPoolExecutor(max_workers=count) as pool:
        return list(pool.map(lambda _: func(), range(count)))


def _domain_code(result):
    return result.code if isinstance(result, DomainError) else None


@pytest.mark.unit
def test_concurrent_sync_resume_executes_step_once():
    engine, factory = _isolated_engine("replan_sync_claim")
    seed = factory()
    try:
        task_id = start(seed, "sync-claim").id
    finally:
        seed.close()

    barrier = Barrier(2)
    counter_lock = Lock()
    calls = 0

    def execute(db, _task):
        nonlocal calls
        with counter_lock:
            calls += 1
        db.add(NotificationConfig(enabled_channels=["console"]))

    def worker():
        session = factory()
        try:
            barrier.wait()
            return resume(session, task_id, executors={"F007": execute})
        except DomainError as exc:
            session.rollback()
            return exc
        finally:
            session.close()

    try:
        results = _run_threaded(worker, 2)
        assert calls == 1
        assert sum(isinstance(item, ReplanTask) for item in results) == 1
        assert [_domain_code(item) for item in results].count(CODE_STATE_CONFLICT) == 1

        verify = factory()
        try:
            task = verify.get(ReplanTask, task_id)
            assert task.current_step == "F021"
            assert task.claim_token is None
            assert verify.query(NotificationConfig).count() == 1
        finally:
            verify.close()
    finally:
        engine.dispose()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_concurrent_async_resume_executes_step_once():
    engine, factory = _isolated_engine("replan_async_claim")
    seed = factory()
    try:
        task_id = start(seed, "async-claim").id
    finally:
        seed.close()

    barrier = Barrier(2)
    counter_lock = Lock()
    calls = 0

    async def execute(db, _task):
        nonlocal calls
        with counter_lock:
            calls += 1
        db.add(NotificationConfig(enabled_channels=["console"]))

    def worker():
        session = factory()
        try:
            barrier.wait()
            return asyncio.run(
                resume_async(session, task_id, executors={"F007": execute})
            )
        except DomainError as exc:
            session.rollback()
            return exc
        finally:
            session.close()

    try:
        results = await asyncio.to_thread(_run_threaded, worker, 2)
        assert calls == 1
        assert sum(isinstance(item, ReplanTask) for item in results) == 1
        assert [_domain_code(item) for item in results].count(CODE_STATE_CONFLICT) == 1

        verify = factory()
        try:
            assert verify.query(NotificationConfig).count() == 1
        finally:
            verify.close()
    finally:
        engine.dispose()


@pytest.mark.unit
def test_active_lease_blocks_and_expired_lease_is_reclaimed():
    engine, factory = _isolated_engine("replan_lease_reclaim")
    first = factory()
    second = factory()
    try:
        task_id = start(first, "lease-reclaim").id
        _task, original = claim_replan_step(
            first, task_id, worker_id="worker-a", lease_seconds=60
        )
        assert original is not None

        with pytest.raises(DomainError) as caught:
            claim_replan_step(second, task_id, worker_id="worker-b", lease_seconds=60)
        assert caught.value.code == CODE_STATE_CONFLICT

        first.execute(
            text("UPDATE replan_tasks SET lease_until = :expired WHERE id = :task_id"),
            {"expired": datetime.now() - timedelta(days=1), "task_id": task_id},
        )
        first.commit()
        claimed_task, replacement = claim_replan_step(
            second, task_id, worker_id="worker-b", lease_seconds=60
        )
        assert replacement is not None
        assert replacement.token != original.token
        assert claimed_task.claimed_by == "worker-b"
    finally:
        first.close()
        second.close()
        engine.dispose()


@pytest.mark.unit
def test_stale_claim_cannot_finalize_or_commit_business_write():
    engine, factory = _isolated_engine("replan_stale_fence")
    stale = factory()
    replacement_session = factory()
    try:
        task_id = start(stale, "stale-fence").id
        _task, original = claim_replan_step(stale, task_id, worker_id="worker-a")
        assert original is not None
        stale.execute(
            text("UPDATE replan_tasks SET lease_until = :expired WHERE id = :task_id"),
            {"expired": datetime.now() - timedelta(days=1), "task_id": task_id},
        )
        stale.commit()
        _task, replacement = claim_replan_step(
            replacement_session, task_id, worker_id="worker-b"
        )
        assert replacement is not None

        def stale_execute(db, _task):
            db.add(NotificationConfig(enabled_channels=["console"]))

        with pytest.raises(DomainError) as caught:
            resume(stale, task_id, executors={"F007": stale_execute})
        assert caught.value.code == CODE_STATE_CONFLICT

        verify = factory()
        try:
            assert verify.query(NotificationConfig).count() == 0
            task = verify.get(ReplanTask, task_id)
            assert task.claim_token == replacement.token
            assert task.current_step == "F007"
        finally:
            verify.close()
    finally:
        stale.close()
        replacement_session.close()
        engine.dispose()


@pytest.mark.unit
def test_concurrent_notification_creates_one_outbox_event():
    engine, factory = _isolated_engine("replan_notification_claim")
    seed = factory()
    try:
        task = start(
            seed,
            "notification-claim",
            initial_step="NOTIFICATION",
            initial_status="RUNNING",
        )
        task_id = task.id
    finally:
        seed.close()

    barrier = Barrier(2)

    def notification(_db, _task):
        return None

    def worker():
        session = factory()
        try:
            barrier.wait()
            return resume(
                session,
                task_id,
                executors={"NOTIFICATION": notification},
            )
        except DomainError as exc:
            session.rollback()
            return exc
        finally:
            session.close()

    try:
        results = _run_threaded(worker, 2)
        completed = [item for item in results if isinstance(item, ReplanTask)]
        conflicts = [item for item in results if _domain_code(item) == CODE_STATE_CONFLICT]
        assert len(completed) + len(conflicts) == 2
        assert len(completed) >= 1
        assert all(item.status == "COMPLETED" for item in completed)
        verify = factory()
        try:
            assert verify.get(ReplanTask, task_id).status == "COMPLETED"
            assert verify.query(OutboxEvent).count() == 1
        finally:
            verify.close()
    finally:
        engine.dispose()


@pytest.mark.unit
def test_concurrent_start_reuses_same_fingerprint():
    engine, factory = _isolated_engine("replan_start_same")
    barrier = Barrier(2)
    fingerprint = build_request_fingerprint({"reason": "same"})

    def worker():
        session = factory()
        try:
            barrier.wait()
            return start(
                session,
                "start-same",
                request_fingerprint=fingerprint,
                operation_type="redispatch",
            ).id
        except Exception as exc:
            session.rollback()
            return exc
        finally:
            session.close()

    try:
        results = _run_threaded(worker, 2)
        assert all(isinstance(item, int) for item in results)
        assert len(set(results)) == 1
        verify = factory()
        try:
            assert verify.query(ReplanTask).count() == 1
        finally:
            verify.close()
    finally:
        engine.dispose()


@pytest.mark.unit
def test_concurrent_start_rejects_different_fingerprint():
    engine, factory = _isolated_engine("replan_start_mismatch")
    barrier = Barrier(2)
    fingerprints = [
        build_request_fingerprint({"reason": "one"}),
        build_request_fingerprint({"reason": "two"}),
    ]

    def worker(index: int):
        session = factory()
        try:
            barrier.wait()
            return start(
                session,
                "start-mismatch",
                request_fingerprint=fingerprints[index],
                operation_type="redispatch",
            )
        except DomainError as exc:
            session.rollback()
            return exc
        finally:
            session.close()

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(worker, range(2)))
        assert sum(isinstance(item, ReplanTask) for item in results) == 1
        assert [_domain_code(item) for item in results].count(
            CODE_IDEMPOTENCY_PAYLOAD_MISMATCH
        ) == 1
        verify = factory()
        try:
            assert verify.query(ReplanTask).count() == 1
        finally:
            verify.close()
    finally:
        engine.dispose()
