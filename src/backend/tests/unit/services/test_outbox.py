import pytest
from sqlalchemy.exc import IntegrityError

from models.outbox_event import OutboxEvent
from models.replan_task import ReplanTask
from services.outbox_service import (
    NonRetryableOutboxError,
    complete_notification_step,
    deliver_outbox_batch,
    enqueue_outbox,
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
