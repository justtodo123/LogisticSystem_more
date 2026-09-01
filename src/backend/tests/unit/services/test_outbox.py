from datetime import datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from models.outbox_event import OutboxEvent
from models.replan_task import ReplanTask
from services.outbox_service import (
    NonRetryableOutboxError,
    claim_outbox_batch,
    complete_notification_step,
    deliver_outbox_batch,
    enqueue_outbox,
    finalize_claimed_event,
)
from services.replan_task_service import resume, start


def test_enqueue_outbox_does_not_commit_and_deduplicates(db_session):
    event = enqueue_outbox(
        db_session,
        dedup_key="event-1",
        event_type="replan.completed",
        payload={"task_id": 1},
    )
    same = enqueue_outbox(
        db_session,
        dedup_key="event-1",
        event_type="replan.completed",
        payload={"task_id": 1},
    )
    assert same.id == event.id
    assert db_session.query(OutboxEvent).count() == 1
    db_session.rollback()
    assert db_session.query(OutboxEvent).count() == 0


def test_notification_completion_commits_task_and_outbox_together(db_session):
    task = start(db_session, "outbox-task")
    task.current_step = "NOTIFICATION"
    task.status = "RUNNING"
    db_session.commit()

    complete_notification_step(
        db_session,
        task,
        event_type="replan.completed",
        payload={"task_id": task.id},
    )

    assert task.status == "COMPLETED"
    assert db_session.query(OutboxEvent).count() == 1


def test_business_commit_survives_delivery_failure_and_event_remains(db_session):
    task = start(db_session, "outbox-failure")
    task.current_step = "NOTIFICATION"
    task.status = "RUNNING"
    complete_notification_step(
        db_session,
        task,
        event_type="replan.completed",
        payload={"task_id": task.id},
    )
    task_id = task.id

    result = deliver_outbox_batch(
        lambda: db_session,
        lambda _event: False,
        retry_delay_seconds=0,
    )

    assert result == {"delivered": 0, "retry": 1, "dead-letter": 0}
    event = db_session.query(OutboxEvent).one()
    assert event.status == "retry"
    assert event.retry_count == 1
    assert db_session.get(ReplanTask, task_id).status == "COMPLETED"


def test_delivery_uses_independent_session_and_is_idempotent(db_session):
    task = start(db_session, "outbox-independent")
    task.current_step = "NOTIFICATION"
    task.status = "RUNNING"
    complete_notification_step(
        db_session,
        task,
        event_type="replan.completed",
        payload={"task_id": task.id},
    )
    request_session = db_session
    sessions = []

    def make_session():
        from sqlalchemy.orm import sessionmaker

        session = sessionmaker(bind=request_session.get_bind())()
        sessions.append(session)
        return session

    side_effects = []

    def sender(event):
        side_effects.append(event.dedup_key)
        return True

    deliver_outbox_batch(make_session, sender)
    deliver_outbox_batch(make_session, sender)

    assert sessions[0] is not request_session
    assert side_effects == ["replan-task:1:notification"]
    assert db_session.query(OutboxEvent).one().status == "delivered"
    for session in sessions:
        session.close()


def test_non_retryable_failure_becomes_dead_letter(db_session):
    enqueue_outbox(db_session, dedup_key="dead-1", event_type="x", payload={})
    db_session.commit()
    result = deliver_outbox_batch(
        lambda: db_session,
        lambda _event: (_ for _ in ()).throw(NonRetryableOutboxError("invalid payload")),
        max_retries=3,
    )
    assert result["dead-letter"] == 1
    assert db_session.query(OutboxEvent).one().status == "dead-letter"


def test_duplicate_dedup_key_is_rejected_at_database_boundary(db_session):
    db_session.add_all(
        [
            OutboxEvent(dedup_key="duplicate", event_type="x", payload={}),
            OutboxEvent(dedup_key="duplicate", event_type="x", payload={}),
        ]
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_two_sessions_only_one_can_claim_same_event(db_session):
    from sqlalchemy.orm import sessionmaker

    enqueue_outbox(db_session, dedup_key="claim-race", event_type="x", payload={})
    db_session.commit()
    make_session = sessionmaker(bind=db_session.get_bind())
    first_session = make_session()
    second_session = make_session()
    try:
        first = claim_outbox_batch(
            first_session, worker_id="worker-a", limit=1, lease_seconds=60
        )
        second = claim_outbox_batch(
            second_session, worker_id="worker-b", limit=1, lease_seconds=60
        )

        assert [event.dedup_key for event in first] == ["claim-race"]
        assert second == []
        claimed = db_session.query(OutboxEvent).one()
        db_session.refresh(claimed)
        assert claimed.status == "processing"
        assert claimed.claimed_by == "worker-a"
        assert claimed.claim_token
    finally:
        first_session.close()
        second_session.close()


def test_expired_processing_lease_is_reclaimed(db_session):
    event = OutboxEvent(
        dedup_key="expired-lease",
        event_type="x",
        payload={},
        status="processing",
        claim_token="old-token",
        claimed_by="dead-worker",
        claimed_at=datetime.utcnow() - timedelta(minutes=2),
        lease_until=datetime.utcnow() - timedelta(minutes=1),
    )
    db_session.add(event)
    db_session.commit()

    reclaimed = claim_outbox_batch(
        db_session, worker_id="replacement", limit=1, lease_seconds=60
    )

    assert [item.id for item in reclaimed] == [event.id]
    assert reclaimed[0].status == "processing"
    assert reclaimed[0].claimed_by == "replacement"
    assert reclaimed[0].claim_token != "old-token"
    assert reclaimed[0].lease_until > datetime.utcnow()


def test_active_processing_lease_is_not_reclaimed(db_session):
    event = OutboxEvent(
        dedup_key="active-lease",
        event_type="x",
        payload={},
        status="processing",
        claim_token="active-token",
        claimed_by="active-worker",
        claimed_at=datetime.utcnow(),
        lease_until=datetime.utcnow() + timedelta(minutes=1),
    )
    db_session.add(event)
    db_session.commit()

    claimed = claim_outbox_batch(
        db_session, worker_id="other-worker", limit=1, lease_seconds=60
    )

    assert claimed == []
    db_session.refresh(event)
    assert event.claim_token == "active-token"
    assert event.claimed_by == "active-worker"



    """worker sender 接收独立 Session，不复用请求 Session。"""
    from sqlalchemy.orm import sessionmaker

    from services.notification.dispatcher import NotificationDispatcher
    from services.outbox_service import complete_notification_step, deliver_outbox_batch

    task = ReplanTask(
        idempotency_key="step5-worker-session",
        current_step="NOTIFICATION",
        status="RUNNING",
    )
    db_session.add(task)
    db_session.commit()
    complete_notification_step(
        db_session,
        task,
        event_type="replan.completed",
        payload={"schedule_code": "GS_STEP5_002"},
    )

    request_session = db_session
    worker_sessions = []

    def worker_session_factory():
        session = sessionmaker(bind=request_session.get_bind())()
        worker_sessions.append(session)
        return session

    dispatcher_sessions = []

    def sender(_event):
        worker_session = worker_sessions[-1]
        dispatcher = NotificationDispatcher(db=worker_session)
        dispatcher_sessions.append(dispatcher._db)
        return True

    result = deliver_outbox_batch(worker_session_factory, sender)

    assert result["delivered"] == 1
    assert worker_sessions[0] is not request_session
    assert dispatcher_sessions == [worker_sessions[0]]



def test_stale_claim_token_cannot_finalize(db_session):
    enqueue_outbox(db_session, dedup_key="stale-token", event_type="x", payload={})
    db_session.commit()
    first = claim_outbox_batch(
        db_session, worker_id="old-worker", limit=1, lease_seconds=60
    )
    assert len(first) == 1
    old_token = first[0].claim_token
    event_id = first[0].id
    first[0].lease_until = datetime.utcnow() - timedelta(seconds=5)
    db_session.commit()

    reclaimed = claim_outbox_batch(
        db_session, worker_id="new-worker", limit=1, lease_seconds=60
    )
    assert len(reclaimed) == 1
    assert reclaimed[0].claim_token != old_token

    outcome = finalize_claimed_event(
        db_session,
        event_id=event_id,
        claim_token=old_token,
        worker_id="old-worker",
        ok=True,
        error="",
        permanent_failure=False,
        max_retries=3,
        retry_delay_seconds=1,
    )
    assert outcome == "stale"
    stored = db_session.get(OutboxEvent, event_id)
    db_session.refresh(stored)
    assert stored.status == "processing"
    assert stored.claimed_by == "new-worker"

    outcome = finalize_claimed_event(
        db_session,
        event_id=event_id,
        claim_token=reclaimed[0].claim_token,
        worker_id="new-worker",
        ok=True,
        error="",
        permanent_failure=False,
        max_retries=3,
        retry_delay_seconds=1,
    )
    assert outcome == "delivered"
    db_session.refresh(stored)
    assert stored.status == "delivered"
