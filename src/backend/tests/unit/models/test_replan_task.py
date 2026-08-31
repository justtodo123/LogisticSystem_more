import pytest
from sqlalchemy.exc import IntegrityError

from models.replan_task import ReplanTask


def test_replan_task_defaults_and_fields(db_session):
    task = ReplanTask(idempotency_key="replan-001")
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    assert task.status == "PENDING"
    assert task.current_step == "F007"
    assert task.retry_count == 0
    assert task.version == 1
    assert task.manual_required is False
    assert task.last_error is None
    assert task.created_at is not None
    assert task.updated_at is not None


def test_replan_task_idempotency_key_is_unique(db_session):
    db_session.add_all(
        [
            ReplanTask(idempotency_key="same-key"),
            ReplanTask(idempotency_key="same-key"),
        ]
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
