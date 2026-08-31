from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
from uuid import uuid4

from sqlalchemy import or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.error_codes import CODE_IDEMPOTENCY_PAYLOAD_MISMATCH, CODE_STATE_CONFLICT
from core.errors import DomainError
from models.replan_task import ReplanTask
from services.outbox_service import complete_notification_step


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


REPLAN_STEP_LEASE_SECONDS = 300


@dataclass(frozen=True)
class ReplanStepClaim:
    task_id: int
    step: str
    token: str
    version: int


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _clear_claim_values() -> dict[str, object | None]:
    return {
        "claim_token": None,
        "claimed_by": None,
        "claimed_step": None,
        "claimed_at": None,
        "lease_until": None,
    }


def _load_task(db: Session, task_id: int) -> ReplanTask:
    db.expire_all()
    task = db.get(ReplanTask, task_id)
    if task is None:
        raise DomainError(CODE_STATE_CONFLICT, message="重规划任务不存在")
    return task


def claim_replan_step(
    db: Session,
    task_id: int,
    *,
    worker_id: str | None = None,
    lease_seconds: int = REPLAN_STEP_LEASE_SECONDS,
) -> tuple[ReplanTask, ReplanStepClaim | None]:
    """以条件更新抢占当前步骤；已完成任务直接回放。"""
    task = _load_task(db, task_id)
    if task.manual_required:
        raise DomainError(
            CODE_STATE_CONFLICT,
            message="重规划任务需要人工处理，不能自动继续",
        )
    if task.current_step == "COMPLETED":
        return task, None
    ready_statuses = _READY_STATUSES_BY_STEP.get(task.current_step, frozenset())
    if task.status not in ready_statuses:
        raise DomainError(CODE_STATE_CONFLICT)

    now = _utcnow()
    token = uuid4().hex
    step = task.current_step
    observed_version = task.version
    result = db.execute(
        update(ReplanTask)
        .where(
            ReplanTask.id == task_id,
            ReplanTask.current_step == step,
            ReplanTask.version == observed_version,
            ReplanTask.status.in_(ready_statuses),
            ReplanTask.manual_required.is_(False),
            or_(
                ReplanTask.claim_token.is_(None),
                ReplanTask.lease_until.is_(None),
                ReplanTask.lease_until <= now,
            ),
        )
        .values(
            claim_token=token,
            claimed_by=worker_id or f"replan-{token[:12]}",
            claimed_step=step,
            claimed_at=now,
            lease_until=now + timedelta(seconds=lease_seconds),
            version=observed_version + 1,
        )
    )
    if result.rowcount != 1:
        db.rollback()
        current = _load_task(db, task_id)
        if current.current_step == "COMPLETED":
            return current, None
        if current.manual_required:
            raise DomainError(
                CODE_STATE_CONFLICT,
                message="重规划任务需要人工处理，不能自动继续",
            )
        raise DomainError(CODE_STATE_CONFLICT, message="重规划步骤正在执行，请稍后重试")

    db.commit()
    task = _load_task(db, task_id)
    return task, ReplanStepClaim(task_id, step, token, observed_version + 1)


def _require_claim(task: ReplanTask, claim: ReplanStepClaim) -> None:
    if (
        task.claim_token != claim.token
        or task.claimed_step != claim.step
        or task.current_step != claim.step
        or task.version != claim.version
    ):
        raise DomainError(CODE_STATE_CONFLICT, message="重规划步骤执行权已失效")


def _finalize_claimed_step(
    db: Session,
    task: ReplanTask,
    claim: ReplanStepClaim,
    next_step: str,
    *,
    retain_claim: bool = False,
) -> None:
    """在业务事务内以 token fence 推进任务；失败时由调用方回滚业务写入。"""
    values = {
        "current_step": next_step,
        "status": "COMPLETED" if next_step == "COMPLETED" else "RUNNING",
        "retry_count": 0,
        "last_error": None,
        "version": claim.version + 1,
        **({} if retain_claim else _clear_claim_values()),
    }
    result = db.execute(
        update(ReplanTask)
        .where(
            ReplanTask.id == claim.task_id,
            ReplanTask.current_step == claim.step,
            ReplanTask.claimed_step == claim.step,
            ReplanTask.claim_token == claim.token,
            ReplanTask.version == claim.version,
        )
        .values(**values)
    )
    if result.rowcount != 1:
        raise DomainError(CODE_STATE_CONFLICT, message="重规划步骤执行权已失效")


def _release_claim_after_failure(
    db: Session,
    claim: ReplanStepClaim,
    error: Exception,
) -> None:
    result = db.execute(
        update(ReplanTask)
        .where(
            ReplanTask.id == claim.task_id,
            ReplanTask.current_step == claim.step,
            ReplanTask.claimed_step == claim.step,
            ReplanTask.claim_token == claim.token,
            ReplanTask.version == claim.version,
        )
        .values(
            retry_count=ReplanTask.retry_count + 1,
            last_error=str(error)[:256],
            version=claim.version + 1,
            **_clear_claim_values(),
        )
    )
    if result.rowcount == 1:
        db.commit()
    else:
        db.rollback()


def get_or_create_replan_task(
    db: Session,
    idempotency_key: str,
    *,
    request_fingerprint: str | None = None,
    operation_type: str | None = None,
    original_resource_id: int | None = None,
    original_resource_code: str | None = None,
    initial_step: str = "F007",
    initial_status: str = "PENDING",
) -> tuple[ReplanTask, bool]:
    """获取或创建任务，不提交调用方事务。"""
    def validate_and_backfill(existing: ReplanTask) -> ReplanTask:
        if request_fingerprint is not None:
            if (
                existing.request_fingerprint is not None
                and existing.request_fingerprint != request_fingerprint
            ):
                raise DomainError(CODE_IDEMPOTENCY_PAYLOAD_MISMATCH)
            if existing.request_fingerprint is None:
                existing.request_fingerprint = request_fingerprint
                existing.operation_type = operation_type
                existing.original_resource_id = original_resource_id
                existing.original_resource_code = original_resource_code
        return existing

    existing = db.scalar(
        select(ReplanTask).where(ReplanTask.idempotency_key == idempotency_key)
    )
    if existing is not None:
        return validate_and_backfill(existing), False

    task = ReplanTask(
        idempotency_key=idempotency_key,
        request_fingerprint=request_fingerprint,
        operation_type=operation_type,
        original_resource_id=original_resource_id,
        original_resource_code=original_resource_code,
        current_step=initial_step,
        status=initial_status,
    )
    try:
        with db.begin_nested():
            db.add(task)
            db.flush()
    except IntegrityError:
        db.expire_all()
        existing = db.scalar(
            select(ReplanTask).where(ReplanTask.idempotency_key == idempotency_key)
        )
        if existing is None:
            raise
        return validate_and_backfill(existing), False

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


def build_request_fingerprint(payload: dict[str, object]) -> str:
    """对规范化 Saga 输入生成稳定指纹。"""
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def start(
    db: Session,
    idempotency_key: str,
    *,
    request_fingerprint: str | None = None,
    operation_type: str | None = None,
    original_resource_id: int | None = None,
    original_resource_code: str | None = None,
    initial_step: str = "F007",
    initial_status: str = "PENDING",
) -> ReplanTask:
    """在短事务中创建任务；同一键仅允许回放相同请求。"""
    task, created = get_or_create_replan_task(
        db,
        idempotency_key,
        request_fingerprint=request_fingerprint,
        operation_type=operation_type,
        original_resource_id=original_resource_id,
        original_resource_code=original_resource_code,
        initial_step=initial_step,
        initial_status=initial_status,
    )
    if created or db.is_modified(task, include_collections=False):
        db.commit()
    return task


def _mark_manual_required(
    db: Session,
    task_id: int,
    reason: str,
    claim: ReplanStepClaim,
) -> ReplanTask:
    task = _load_task(db, task_id)
    if (
        task.claim_token != claim.token
        or task.claimed_step != claim.step
        or task.version not in {claim.version, claim.version + 1}
    ):
        raise DomainError(CODE_STATE_CONFLICT, message="重规划步骤执行权已失效")
    observed_version = task.version
    result = db.execute(
        update(ReplanTask)
        .where(
            ReplanTask.id == claim.task_id,
            ReplanTask.claimed_step == claim.step,
            ReplanTask.claim_token == claim.token,
            ReplanTask.version == observed_version,
        )
        .values(
            manual_required=True,
            status="FAILED",
            last_error=reason[:256],
            version=observed_version + 1,
            **_clear_claim_values(),
        )
    )
    if result.rowcount != 1:
        db.rollback()
        raise DomainError(CODE_STATE_CONFLICT, message="重规划步骤执行权已失效")
    db.commit()
    return _load_task(db, task_id)


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
    claim: ReplanStepClaim,
) -> ReplanTask:
    task = _load_task(db, task_id)
    if task.claim_token != claim.token or task.claimed_step != claim.step:
        raise DomainError(CODE_STATE_CONFLICT, message="重规划步骤执行权已失效")
    observed_version = task.version
    compensator = compensators.get(step)
    if compensator is None:
        return _mark_manual_required(
            db, task_id, f"{step} 缺少可靠补偿：{error}", claim
        )
    try:
        compensator(db, task)
        result = db.execute(
            update(ReplanTask)
            .where(
                ReplanTask.id == claim.task_id,
                ReplanTask.claim_token == claim.token,
                ReplanTask.claimed_step == claim.step,
                ReplanTask.version == observed_version,
            )
            .values(
                current_step=step,
                status="RUNNING",
                retry_count=ReplanTask.retry_count + 1,
                last_error=str(error)[:256],
                version=observed_version + 1,
                **_clear_claim_values(),
            )
        )
        if result.rowcount != 1:
            raise DomainError(CODE_STATE_CONFLICT, message="重规划步骤执行权已失效")
        db.commit()
        return _load_task(db, task_id)
    except DomainError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        return _mark_manual_required(
            db, task_id, f"{step} 补偿失败：{error}", claim
        )


def _retain_claim_after_committed_error(
    db: Session,
    claim: ReplanStepClaim,
) -> bool:
    """将 executor 已提交的当前步骤转为 retained claim，供补偿或人工处理。"""
    result = db.execute(
        update(ReplanTask)
        .where(
            ReplanTask.id == claim.task_id,
            ReplanTask.current_step == claim.step,
            ReplanTask.claimed_step == claim.step,
            ReplanTask.claim_token == claim.token,
            ReplanTask.version == claim.version,
        )
        .values(version=claim.version + 1)
    )
    if result.rowcount != 1:
        db.rollback()
        return False
    db.commit()
    return True


def _clear_retained_claim(
    db: Session,
    claim: ReplanStepClaim,
) -> ReplanTask:
    result = db.execute(
        update(ReplanTask)
        .where(
            ReplanTask.id == claim.task_id,
            ReplanTask.claim_token == claim.token,
            ReplanTask.claimed_step == claim.step,
            ReplanTask.version == claim.version + 1,
        )
        .values(**_clear_claim_values())
    )
    if result.rowcount != 1:
        db.rollback()
        raise DomainError(CODE_STATE_CONFLICT, message="重规划步骤执行权已失效")
    db.commit()
    return _load_task(db, claim.task_id)


def resume(
    db: Session,
    task_id: int,
    *,
    executors: dict[str, StepExecutor],
    compensators: dict[str, Compensator] | None = None,
) -> ReplanTask:
    """从持久化 current_step 执行一个步骤，并以租约和 token fence 推进任务。"""
    task, claim = claim_replan_step(db, task_id)
    if claim is None:
        return task
    step = claim.step
    try:
        executor = executors[step]
    except KeyError as exc:
        _release_claim_after_failure(db, claim, exc)
        raise DomainError(CODE_STATE_CONFLICT, message="重规划步骤执行器未配置") from exc

    committed = False
    try:
        task = _load_task(db, task_id)
        _require_claim(task, claim)
        outcome = executor(db, task) or StepResult()
        next_step = outcome.next_step or _STEP_ORDER[step]
        if step == "NOTIFICATION":
            complete_notification_step(
                db,
                task,
                event_type="replan.completed",
                payload={"task_id": task.id, "idempotency_key": task.idempotency_key},
                commit=False,
            )
            _finalize_claimed_step(db, task, claim, "COMPLETED")
        else:
            _finalize_claimed_step(db, task, claim, next_step, retain_claim=True)
        db.commit()
        committed = True
        if step == "NOTIFICATION":
            return _load_task(db, task_id)
        return _clear_retained_claim(db, claim)
    except StepExecutionError as exc:
        db.rollback()
        if not exc.committed:
            _release_claim_after_failure(db, claim, exc)
            raise
        if not committed:
            retained = _retain_claim_after_committed_error(db, claim)
            if not retained:
                raise DomainError(CODE_STATE_CONFLICT, message="重规划步骤执行权已失效") from exc
        if _requires_manual(step, exc.resource_state):
            return _mark_manual_required(db, task_id, f"{step} 提交后失败：{exc}", claim)
        return _compensate_after_commit(db, task_id, step, exc, compensators or {}, claim)
    except Exception as exc:
        db.rollback()
        if committed:
            raise
        _release_claim_after_failure(db, claim, exc)
        raise


async def resume_async(
    db: Session,
    task_id: int,
    *,
    executors: dict[str, Callable[[Session, ReplanTask], object]],
    compensators: dict[str, Compensator] | None = None,
    after_commit_hook: Callable[[str, ReplanTask], None] | None = None,
    notification_payload: dict[str, object] | None = None,
) -> ReplanTask:
    """异步步骤版本的 resume；事务、租约和补偿语义与 resume 一致。"""
    task, claim = claim_replan_step(db, task_id)
    if claim is None:
        return task
    step = claim.step
    try:
        executor = executors[step]
    except KeyError as exc:
        _release_claim_after_failure(db, claim, exc)
        raise DomainError(CODE_STATE_CONFLICT, message="重规划步骤执行器未配置") from exc

    committed = False
    try:
        task = _load_task(db, task_id)
        _require_claim(task, claim)
        outcome = await executor(db, task)
        outcome = outcome or StepResult()
        next_step = outcome.next_step or _STEP_ORDER[step]
        if step == "NOTIFICATION":
            complete_notification_step(
                db,
                task,
                event_type="replan.completed",
                payload=notification_payload
                or {"task_id": task.id, "idempotency_key": task.idempotency_key},
                commit=False,
            )
            _finalize_claimed_step(db, task, claim, "COMPLETED")
        else:
            _finalize_claimed_step(db, task, claim, next_step, retain_claim=True)
        db.commit()
        committed = True
        task = _load_task(db, task_id)
        if after_commit_hook is not None:
            try:
                after_commit_hook(step, task)
            except Exception as exc:
                if step == "F021":
                    return _mark_manual_required(
                        db, task_id, f"F021 提交后失败：{exc}", claim
                    )
                if (
                    step == "F006"
                    and notification_payload
                    and notification_payload.get("strategy") == "reroute"
                ):
                    return _mark_manual_required(
                        db, task_id, f"F006 已执行后失败：{exc}", claim
                    )
                raise StepExecutionError(str(exc), committed=True) from exc
        if step == "NOTIFICATION":
            return task
        return _clear_retained_claim(db, claim)
    except StepExecutionError as exc:
        db.rollback()
        if not exc.committed:
            _release_claim_after_failure(db, claim, exc)
            raise
        if not committed:
            retained = _retain_claim_after_committed_error(db, claim)
            if not retained:
                raise DomainError(CODE_STATE_CONFLICT, message="重规划步骤执行权已失效") from exc
        if _requires_manual(step, exc.resource_state):
            return _mark_manual_required(db, task_id, f"{step} 提交后失败：{exc}", claim)
        return _compensate_after_commit(
            db, task_id, step, exc, compensators or {}, claim
        )
    except Exception as exc:
        db.rollback()
        if committed:
            raise
        _release_claim_after_failure(db, claim, exc)
        raise
