"""PostgreSQL protocol reruns for R2-01 through R2-03."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from threading import Barrier
from uuid import uuid4

import pytest

from core.cas import claim_status
from core.code_allocation import RESOURCE_GLOBAL_SCHEDULE, allocate_code
from core.error_codes import CODE_STATE_CONFLICT
from core.errors import DomainError
from models.code_range import CodeRange
from models.global_schedule import GlobalSchedule
from models.idempotency_record import IdempotencyRecord
from models.outbox_event import OutboxEvent
from models.replan_task import ReplanTask
from services.outbox_service import claim_outbox_batch, enqueue_outbox
from services.replan_task_service import claim_replan_step, start
from utils.idempotency_store import (
    STATUS_PROCESSING,
    claim_request,
    reset_session_factory,
    set_session_factory,
)

NOW = datetime(2099, 12, 31, 12, 0, 0)


def _run_threaded(func, count: int):
    with ThreadPoolExecutor(max_workers=count) as pool:
        return list(pool.map(lambda _: func(), range(count)))


def _schedule(code: str) -> GlobalSchedule:
    return GlobalSchedule(
        schedule_code=code,
        order_codes=["P1-O001"],
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
def test_postgres_cas_has_single_winner(p1_postgres, p1_row_cleanup):
    _engine, factory = p1_postgres
    schedule_code = f"P1-CAS-{uuid4().hex}"
    seed = factory()
    try:
        schedule = _schedule(schedule_code)
        seed.add(schedule)
        seed.commit()
        schedule_id = schedule.id
    finally:
        seed.close()
    p1_row_cleanup(
        GlobalSchedule,
        filters={GlobalSchedule: GlobalSchedule.schedule_code == schedule_code},
    )

    barrier = Barrier(20)

    def worker():
        session = factory()
        try:
            barrier.wait()
            claim_status(
                session,
                GlobalSchedule,
                identity=GlobalSchedule.id == schedule_id,
                from_statuses="draft",
                to_status="active",
                increment_version=True,
            )
            session.commit()
            return "won"
        except DomainError as exc:
            session.rollback()
            return exc.code
        finally:
            session.close()

    results = _run_threaded(worker, 20)
    assert results.count("won") == 1
    assert results.count(CODE_STATE_CONFLICT) == 19

    verify = factory()
    try:
        stored = verify.get(GlobalSchedule, schedule_id)
        assert stored.status == "active"
        assert stored.version == 2
    finally:
        verify.close()


@pytest.mark.integration
def test_postgres_idempotency_claim_has_single_owner(p1_postgres, p1_row_cleanup):
    _engine, factory = p1_postgres
    key = f"p1-idempotency-{uuid4().hex}"
    p1_row_cleanup(
        IdempotencyRecord,
        filters={IdempotencyRecord: IdempotencyRecord.idempotency_key == key},
    )
    set_session_factory(factory)
    barrier = Barrier(20)

    def worker():
        barrier.wait()
        return claim_request(key, "payload-hash").kind

    try:
        results = _run_threaded(worker, 20)
    finally:
        reset_session_factory()

    assert results.count("OWNED") == 1
    assert results.count("IN_PROGRESS") == 19

    verify = factory()
    try:
        stored = (
            verify.query(IdempotencyRecord)
            .filter_by(idempotency_key=key)
            .one()
        )
        assert stored.status == STATUS_PROCESSING
        assert stored.payload_hash == "payload-hash"
        assert stored.claim_token
    finally:
        verify.close()


@pytest.mark.integration
def test_postgres_code_allocation_is_unique(p1_postgres, p1_row_cleanup):
    _engine, factory = p1_postgres
    prefix = "GS20991231"
    p1_row_cleanup(
        GlobalSchedule,
        CodeRange,
        filters={
            GlobalSchedule: GlobalSchedule.schedule_code.like(f"{prefix}%"),
            CodeRange: (CodeRange.resource == RESOURCE_GLOBAL_SCHEDULE)
            & (CodeRange.prefix == prefix),
        },
    )

    def worker():
        session = factory()
        try:
            code = allocate_code(session, RESOURCE_GLOBAL_SCHEDULE, now=NOW)
            session.add(_schedule(code))
            session.commit()
            return code
        finally:
            session.close()

    codes = _run_threaded(worker, 8)
    assert len(codes) == 8
    assert len(set(codes)) == 8
    assert set(codes) == {f"{prefix}{value:03d}" for value in range(1, 9)}

    verify = factory()
    try:
        assert (
            verify.query(GlobalSchedule)
            .filter(GlobalSchedule.schedule_code.like(f"{prefix}%"))
            .count()
            == 8
        )
        row = (
            verify.query(CodeRange)
            .filter_by(resource=RESOURCE_GLOBAL_SCHEDULE, prefix=prefix)
            .one()
        )
        assert row.next_value == 9
    finally:
        verify.close()


@pytest.mark.integration
def test_postgres_replan_step_claim_has_single_winner(p1_postgres, p1_row_cleanup):
    _engine, factory = p1_postgres
    idempotency_key = f"p1-replan-{uuid4().hex}"
    seed = factory()
    try:
        task_id = start(seed, idempotency_key).id
    finally:
        seed.close()
    p1_row_cleanup(
        ReplanTask,
        filters={ReplanTask: ReplanTask.idempotency_key == idempotency_key},
    )
    barrier = Barrier(2)

    def worker(worker_id: str):
        session = factory()
        try:
            barrier.wait()
            task, claim = claim_replan_step(session, task_id, worker_id=worker_id)
            return task.id, claim.token if claim else None
        except DomainError as exc:
            session.rollback()
            return exc.code
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(worker, ["p1-replan-a", "p1-replan-b"]))

    winners = [result for result in results if isinstance(result, tuple)]
    assert len(winners) == 1
    assert results.count(CODE_STATE_CONFLICT) == 1

    verify = factory()
    try:
        stored = verify.get(ReplanTask, task_id)
        assert stored.claim_token == winners[0][1]
        assert stored.claimed_by in {"p1-replan-a", "p1-replan-b"}
        assert stored.version == 2
    finally:
        verify.close()


@pytest.mark.integration
def test_postgres_outbox_claim_has_single_winner(p1_postgres, p1_row_cleanup):
    _engine, factory = p1_postgres
    dedup_key = f"p1-outbox-{uuid4().hex}"
    seed = factory()
    try:
        event = enqueue_outbox(
            seed,
            dedup_key=dedup_key,
            event_type="p1.protocol",
            payload={"scenario": "outbox-claim"},
        )
        seed.commit()
        event_id = event.id
    finally:
        seed.close()
    p1_row_cleanup(
        OutboxEvent,
        filters={OutboxEvent: OutboxEvent.dedup_key == dedup_key},
    )
    barrier = Barrier(2)

    def worker(worker_id: str):
        session = factory()
        try:
            barrier.wait()
            return [
                claimed.id
                for claimed in claim_outbox_batch(
                    session,
                    worker_id=worker_id,
                    limit=1,
                    lease_seconds=60,
                )
            ]
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(worker, ["p1-outbox-a", "p1-outbox-b"]))

    assert sorted(len(result) for result in results) == [0, 1]
    assert [event_id] in results

    verify = factory()
    try:
        stored = verify.get(OutboxEvent, event_id)
        assert stored.status == "processing"
        assert stored.claimed_by in {"p1-outbox-a", "p1-outbox-b"}
        assert stored.claim_token
    finally:
        verify.close()
