import pytest
from sqlalchemy import event

from core.error_codes import CODE_IDEMPOTENCY_PAYLOAD_MISMATCH, CODE_STATE_CONFLICT
from core.errors import DomainError
from models.notification_config import NotificationConfig
from models.replan_task import ReplanTask
from services.replan_task_service import (
    StepExecutionError,
    build_request_fingerprint,
    check_replan_task_preconditions,
    get_or_create_replan_task,
    resume,
    resume_async,
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


def test_start_rejects_same_key_with_different_fingerprint(db_session):
    fingerprint = build_request_fingerprint({"reason": "one"})
    start(db_session, "replan-fingerprint", request_fingerprint=fingerprint)

    with pytest.raises(DomainError) as caught:
        start(
            db_session,
            "replan-fingerprint",
            request_fingerprint=build_request_fingerprint({"reason": "two"}),
        )

    assert caught.value.code == CODE_IDEMPOTENCY_PAYLOAD_MISMATCH


def test_start_commits_existing_task_fingerprint_backfill(db_session):
    task = start(db_session, "replan-backfill")
    assert task.request_fingerprint is None

    fingerprint = build_request_fingerprint({"reason": "backfill"})
    start(
        db_session,
        "replan-backfill",
        request_fingerprint=fingerprint,
        operation_type="redispatch",
        original_resource_id=42,
        original_resource_code="GS-BACKFILL",
    )

    db_session.expire_all()
    persisted = db_session.get(ReplanTask, task.id)
    assert persisted.request_fingerprint == fingerprint
    assert persisted.operation_type == "redispatch"
    assert persisted.original_resource_id == 42
    assert persisted.original_resource_code == "GS-BACKFILL"


def test_resume_rolls_back_business_and_task_on_precommit_failure(db_session):

    task = start(db_session, "replan-precommit-failure")
    initial_version = task.version

    def fail_before_commit(db, _task):
        db.add(NotificationConfig(enabled_channels=["console"]))
        raise RuntimeError("injected before commit")

    with pytest.raises(RuntimeError, match="injected before commit"):
        resume(db_session, task.id, executors={"F007": fail_before_commit})

    db_session.expire_all()
    persisted = db_session.get(ReplanTask, task.id)
    assert persisted.current_step == "F007"
    assert persisted.status == "PENDING"
    assert persisted.version == initial_version + 2
    assert persisted.claim_token is None
    assert db_session.query(NotificationConfig).count() == 0


def test_resume_continues_from_step_after_f007(db_session):
    task = start(db_session, "replan-resume-f021")
    calls = []

    def finish_f007(_db, _task):
        calls.append("F007")

    initial_version = task.version
    resumed = resume(db_session, task.id, executors={"F007": finish_f007})
    assert resumed.current_step == "F021"
    assert resumed.version == initial_version + 2

    def finish_f021(_db, _task):
        calls.append("F021")

    resumed = resume(db_session, task.id, executors={"F021": finish_f021})
    assert calls == ["F007", "F021"]
    assert resumed.current_step == "F005"
    assert resumed.status == "RUNNING"
    assert resumed.version == initial_version + 4
    assert resumed.claim_token is None


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

    calls = []

    def retry_successfully(_db, _task):
        calls.append(step)

    resumed = resume(
        db_session,
        task.id,
        executors={step: retry_successfully},
    )

    assert calls == [step]
    assert resumed.current_step != step
    assert resumed.retry_count == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("step", ["F007", "F005", "F006"])
async def test_resume_async_compensation_rewinds_and_retries_step(db_session, step):
    task = start(db_session, f"replan-async-{step}-compensate")
    task.current_step = step
    task.status = "PENDING" if step == "F007" else "RUNNING"
    db_session.commit()
    fail_once = True
    calls = []

    async def execute(_db, _task):
        nonlocal fail_once
        calls.append(step)
        if fail_once:
            fail_once = False
            return None

    def fail_after_first_commit(committed_step, _task):
        if committed_step == step and len(calls) == 1:
            raise RuntimeError(f"injected {step} after commit")

    compensated = []
    first = await resume_async(
        db_session,
        task.id,
        executors={step: execute},
        compensators={step: lambda _db, _task: compensated.append(step)},
        after_commit_hook=fail_after_first_commit,
    )

    assert compensated == [step]
    assert first.current_step == step
    assert first.retry_count == 1

    second = await resume_async(
        db_session,
        task.id,
        executors={step: execute},
    )

    assert calls == [step, step]
    assert second.current_step != step
    assert second.retry_count == 0
