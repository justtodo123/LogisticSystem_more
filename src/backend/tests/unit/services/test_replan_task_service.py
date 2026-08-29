import pytest
from sqlalchemy import event

from core.error_codes import CODE_STATE_CONFLICT
from core.errors import DomainError
from models.notification_config import NotificationConfig
from models.replan_task import ReplanTask
from services.replan_task_service import (
    StepExecutionError,
    check_replan_task_preconditions,
    get_or_create_replan_task,
    resume,
    start,
)


def test_get_or_create_replan_task_reuses_idempotency_key(db_session):
    first, first_created = get_or_create_replan_task(db_session, "replan-same-key")
    db_session.commit()

    second, second_created = get_or_create_replan_task(db_session, "replan-same-key")

    assert first_created is True
    assert second_created is False
    assert second.id == first.id
    assert db_session.query(ReplanTask).count() == 1


def test_check_replan_task_preconditions_is_repeatable_and_read_only(db_session):
    task = ReplanTask(idempotency_key="replan-preflight", status="RUNNING", current_step="F021")
    db_session.add(task)
    db_session.commit()

    statements = []

    def record_statement(_conn, _cursor, statement, _parameters, _context, _executemany):
        statements.append(statement)

    event.listen(db_session.get_bind(), "before_cursor_execute", record_statement)
    try:
        first = check_replan_task_preconditions(db_session, task.idempotency_key)
        second = check_replan_task_preconditions(db_session, task.idempotency_key)
    finally:
        event.remove(db_session.get_bind(), "before_cursor_execute", record_statement)

    assert first == second
    assert first.ready is True
    assert first.current_step == "F021"
    assert statements
    assert all(statement.lstrip().upper().startswith("SELECT") for statement in statements)
    assert not db_session.new
    assert not db_session.dirty
    assert not db_session.deleted


def test_check_replan_task_preconditions_rejects_manual_task(db_session):
    task = ReplanTask(
        idempotency_key="replan-manual",
        status="RUNNING",
        current_step="F005",
        manual_required=True,
    )
    db_session.add(task)
    db_session.commit()

    result = check_replan_task_preconditions(db_session, task.idempotency_key)

    assert result.ready is False
    assert result.reason == "MANUAL_REQUIRED"
    assert result.current_step == "F005"


def test_start_reuses_existing_task(db_session):
    first = start(db_session, "replan-start-key")
    second = start(db_session, "replan-start-key")

    assert second.id == first.id
    assert db_session.query(ReplanTask).count() == 1


def test_resume_rolls_back_business_and_task_on_precommit_failure(db_session):
    task = start(db_session, "replan-precommit-failure")

    def fail_before_commit(db, _task):
        db.add(NotificationConfig(enabled_channels=["console"]))
        raise RuntimeError("injected before commit")

    with pytest.raises(RuntimeError, match="injected before commit"):
        resume(db_session, task.id, executors={"F007": fail_before_commit})

    db_session.expire_all()
    persisted = db_session.get(ReplanTask, task.id)
    assert persisted.current_step == "F007"
    assert persisted.status == "PENDING"
    assert persisted.version == 1
    assert db_session.query(NotificationConfig).count() == 0


def test_resume_continues_from_step_after_f007(db_session):
    task = start(db_session, "replan-resume-f021")
    calls = []

    def finish_f007(_db, _task):
        calls.append("F007")

    resumed = resume(db_session, task.id, executors={"F007": finish_f007})
    assert resumed.current_step == "F021"

    def finish_f021(_db, _task):
        calls.append("F021")

    resumed = resume(db_session, task.id, executors={"F021": finish_f021})
    assert calls == ["F007", "F021"]
    assert resumed.current_step == "F005"
    assert resumed.status == "RUNNING"
    assert resumed.version == 3


def test_f021_postcommit_failure_requires_manual_and_blocks_resume(db_session):
    task = start(db_session, "replan-f021-manual")
    task.current_step = "F021"
    task.status = "RUNNING"
    db_session.commit()

    def fail_after_f021_commit(_db, _task):
        raise StepExecutionError(
            "injected after commit",
            committed=True,
            resource_state="active",
        )

    result = resume(
        db_session,
        task.id,
        executors={"F021": fail_after_f021_commit},
    )

    assert result.manual_required is True
    assert result.status == "FAILED"
    assert result.current_step == "F021"

    with pytest.raises(DomainError) as caught:
        resume(db_session, task.id, executors={"F021": fail_after_f021_commit})
    assert caught.value.code == CODE_STATE_CONFLICT
    assert caught.value.public_message == "重规划任务需要人工处理，不能自动继续"


@pytest.mark.parametrize(
    ("step", "resource_state"),
    [("F005", "in_transit"), ("F006", "executed")],
)
def test_irreversible_dispatch_or_route_requires_manual(
    db_session,
    step,
    resource_state,
):
    task = start(db_session, f"replan-{step}-manual")
    task.current_step = step
    task.status = "RUNNING"
    db_session.commit()

    def fail_after_commit(_db, _task):
        raise StepExecutionError(
            "injected irreversible state",
            committed=True,
            resource_state=resource_state,
        )

    result = resume(db_session, task.id, executors={step: fail_after_commit})
    assert result.manual_required is True
    assert result.current_step == step


@pytest.mark.parametrize(
    ("step", "resource_state"),
    [("F007", "draft"), ("F005", "not_started"), ("F006", "not_executed")],
)
def test_compensatable_postcommit_failure_runs_compensator(
    db_session,
    step,
    resource_state,
):
    task = start(db_session, f"replan-{step}-compensate")
    task.current_step = step
    task.status = "RUNNING" if step != "F007" else "PENDING"
    db_session.commit()
    compensated = []

    def fail_after_commit(_db, _task):
        raise StepExecutionError(
            "injected compensatable state",
            committed=True,
            resource_state=resource_state,
        )

    def compensate(_db, _task):
        compensated.append(step)

    result = resume(
        db_session,
        task.id,
        executors={step: fail_after_commit},
        compensators={step: compensate},
    )

    assert compensated == [step]
    assert result.manual_required is False
    assert result.current_step == step
    assert result.status == "RUNNING"
    assert result.retry_count == 1
