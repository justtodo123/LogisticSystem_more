from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.error_codes import CODE_STATE_CONFLICT
from core.errors import DomainError
from models.replan_task import ReplanTask


_READY_STATUSES_BY_STEP = {
    "F007": frozenset({"PENDING", "RUNNING"}),
    "F021": frozenset({"RUNNING"}),
    "F005": frozenset({"RUNNING"}),
    "F006": frozenset({"RUNNING"}),
    "NOTIFICATION": frozenset({"RUNNING"}),
    "COMPLETED": frozenset(),
}


@dataclass(frozen=True)
class ReplanTaskPreflight:
    task_id: int | None
    current_step: str | None
    ready: bool
    reason: str | None = None


def get_or_create_replan_task(
    db: Session,
    idempotency_key: str,
) -> tuple[ReplanTask, bool]:
    """获取或创建任务，不提交调用方事务。"""
    existing = db.scalar(
        select(ReplanTask).where(ReplanTask.idempotency_key == idempotency_key)
    )
    if existing is not None:
        return existing, False

    task = ReplanTask(idempotency_key=idempotency_key)
    try:
        with db.begin_nested():
            db.add(task)
            db.flush()
    except IntegrityError:
        existing = db.scalar(
            select(ReplanTask).where(ReplanTask.idempotency_key == idempotency_key)
        )
        if existing is None:
            raise
        return existing, False

    return task, True


def check_replan_task_preconditions(
    db: Session,
    idempotency_key: str,
) -> ReplanTaskPreflight:
    """按持久化步骤执行无写入的可重复前置检查。"""
    with db.no_autoflush:
        task = db.scalar(
            select(ReplanTask).where(ReplanTask.idempotency_key == idempotency_key)
        )

    if task is None:
        return ReplanTaskPreflight(None, None, False, "TASK_NOT_FOUND")
    if task.manual_required:
        return ReplanTaskPreflight(task.id, task.current_step, False, "MANUAL_REQUIRED")

    ready_statuses = _READY_STATUSES_BY_STEP.get(task.current_step)
    if ready_statuses is None:
        return ReplanTaskPreflight(task.id, task.current_step, False, "UNKNOWN_STEP")
    if task.status not in ready_statuses:
        return ReplanTaskPreflight(task.id, task.current_step, False, "STATUS_MISMATCH")

    return ReplanTaskPreflight(task.id, task.current_step, True)


_STEP_ORDER = {
    "F007": "F021",
    "F021": "F005",
    "F005": "F006",
    "F006": "NOTIFICATION",
    "NOTIFICATION": "COMPLETED",
}


@dataclass(frozen=True)
class StepResult:
    """可注入步骤执行器的结果；业务写入由执行器留在当前事务。"""

    next_step: str | None = None


class StepExecutionError(RuntimeError):
    """步骤失败；committed 表示异常发生在业务提交之后。"""

    def __init__(
        self,
        message: str,
        *,
        committed: bool = False,
        resource_state: str | None = None,
    ) -> None:
        super().__init__(message)
        self.committed = committed
        self.resource_state = resource_state


StepExecutor = Callable[[Session, ReplanTask], StepResult | None]
Compensator = Callable[[Session, ReplanTask], None]


def start(db: Session, idempotency_key: str) -> ReplanTask:
    """在短事务中创建任务；同一幂等键冲突时返回已有任务。"""
    task, created = get_or_create_replan_task(db, idempotency_key)
    if created:
        db.commit()
    return task


def _mark_manual_required(db: Session, task_id: int, reason: str) -> ReplanTask:
    task = db.get(ReplanTask, task_id)
    task.manual_required = True
    task.status = "FAILED"
    task.last_error = reason[:256]
    task.version += 1
    db.commit()
    return task


def _requires_manual(step: str, resource_state: str | None) -> bool:
    if step == "F021":
        return True
    if step == "F005":
        return resource_state == "in_transit"
    if step == "F006":
        return resource_state == "executed"
    return False


def _compensate_after_commit(
    db: Session,
    task_id: int,
    step: str,
    error: StepExecutionError,
    compensators: dict[str, Compensator],
) -> ReplanTask:
    task = db.get(ReplanTask, task_id)
    compensator = compensators.get(step)
    if compensator is None:
        return _mark_manual_required(db, task_id, f"{step} 缺少可靠补偿：{error}")
    try:
        compensator(db, task)
        task.status = "RUNNING"
        task.retry_count += 1
        task.last_error = str(error)[:256]
        task.version += 1
        db.commit()
        return task
    except Exception:
        db.rollback()
        return _mark_manual_required(db, task_id, f"{step} 补偿失败：{error}")


def resume(
    db: Session,
    task_id: int,
    *,
    executors: dict[str, StepExecutor],
    compensators: dict[str, Compensator] | None = None,
) -> ReplanTask:
    """从持久化 current_step 执行一个步骤，并用单次提交推进任务。"""
    task = db.get(ReplanTask, task_id)
    if task is None:
        raise DomainError(CODE_STATE_CONFLICT, message="重规划任务不存在")
    if task.manual_required:
        raise DomainError(
            CODE_STATE_CONFLICT,
            message="重规划任务需要人工处理，不能自动继续",
        )
    if task.current_step == "COMPLETED":
        return task
    if task.status not in _READY_STATUSES_BY_STEP.get(task.current_step, frozenset()):
        raise DomainError(CODE_STATE_CONFLICT)

    step = task.current_step
    try:
        executor = executors[step]
    except KeyError as exc:
        raise DomainError(CODE_STATE_CONFLICT, message="重规划步骤执行器未配置") from exc

    try:
        outcome = executor(db, task) or StepResult()
        next_step = outcome.next_step or _STEP_ORDER[step]
        task.current_step = next_step
        task.status = "COMPLETED" if next_step == "COMPLETED" else "RUNNING"
        task.retry_count = 0
        task.last_error = None
        task.version += 1
        db.commit()
        return task
    except StepExecutionError as exc:
        db.rollback()
        if not exc.committed:
            raise
        if _requires_manual(step, exc.resource_state):
            return _mark_manual_required(db, task_id, f"{step} 提交后失败：{exc}")
        return _compensate_after_commit(
            db,
            task_id,
            step,
            exc,
            compensators or {},
        )
    except Exception:
        db.rollback()
        raise
