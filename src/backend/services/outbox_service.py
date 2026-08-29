from collections.abc import Callable, Mapping
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session, sessionmaker

from models.outbox_event import OutboxEvent
from models.replan_task import ReplanTask


class RetryableOutboxError(RuntimeError):
    """投递暂时失败，可按退避时间重试。"""


class NonRetryableOutboxError(RuntimeError):
    """投递永久失败，应直接进入 dead-letter。"""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def enqueue_outbox(
    db: Session,
    *,
    dedup_key: str,
    event_type: str,
    payload: Mapping[str, Any],
) -> OutboxEvent:
    """将通知写入调用方事务；不提交、不执行任何外部 I/O。"""
    existing = db.scalar(select(OutboxEvent).where(OutboxEvent.dedup_key == dedup_key))
    if existing is not None:
        return existing
    event = OutboxEvent(
        dedup_key=dedup_key,
        event_type=event_type,
        payload=dict(payload),
    )
    db.add(event)
    db.flush()
    return event


def complete_notification_step(
    db: Session,
    task: ReplanTask,
    *,
    event_type: str,
    payload: Mapping[str, Any],
) -> OutboxEvent:
    """在同一短事务中完成任务并写入唯一 outbox 事件。"""
    event = enqueue_outbox(
        db,
        dedup_key=f"replan-task:{task.id}:notification",
        event_type=event_type,
        payload=payload,
    )
    task.current_step = "COMPLETED"
    task.status = "COMPLETED"
    task.last_error = None
    task.retry_count = 0
    task.version += 1
    db.commit()
    return event


def claim_outbox_batch(
    db: Session,
    *,
    worker_id: str,
    limit: int,
    lease_seconds: int,
) -> list[OutboxEvent]:
    """以条件更新原子抢占可投递事件，并回收已过期的 processing 租约。"""
    now = _utcnow()
    lease_until = now + timedelta(seconds=lease_seconds)
    candidate_ids = list(
        db.scalars(
            select(OutboxEvent.id)
            .where(
                or_(
                    (
                        OutboxEvent.status.in_(["pending", "retry"])
                        & (OutboxEvent.available_at <= now)
                    ),
                    (
                        (OutboxEvent.status == "processing")
                        & (OutboxEvent.lease_until <= now)
                    ),
                )
            )
            .order_by(OutboxEvent.id)
            .limit(limit)
        )
    )
    claimed_ids: list[int] = []
    for event_id in candidate_ids:
        token = uuid4().hex
        result = db.execute(
            update(OutboxEvent)
            .where(
                OutboxEvent.id == event_id,
                or_(
                    (
                        OutboxEvent.status.in_(["pending", "retry"])
                        & (OutboxEvent.available_at <= now)
                    ),
                    (
                        (OutboxEvent.status == "processing")
                        & (OutboxEvent.lease_until <= now)
                    ),
                ),
            )
            .values(
                status="processing",
                claim_token=token,
                claimed_by=worker_id,
                claimed_at=now,
                lease_until=lease_until,
            )
        )
        if result.rowcount == 1:
            claimed_ids.append(event_id)
    db.commit()
    if not claimed_ids:
        return []
    return list(
        db.scalars(
            select(OutboxEvent)
            .where(
                OutboxEvent.id.in_(claimed_ids),
                OutboxEvent.status == "processing",
                OutboxEvent.claimed_by == worker_id,
            )
            .order_by(OutboxEvent.id)
        )
    )


def _clear_claim(event: OutboxEvent) -> None:
    event.claim_token = None
    event.claimed_by = None
    event.claimed_at = None
    event.lease_until = None


def deliver_outbox_batch(
    session_factory: sessionmaker,
    sender: Callable[[OutboxEvent], bool],
    *,
    worker_id: str = "outbox-worker",
    limit: int = 100,
    lease_seconds: int = 60,
    max_retries: int = 3,
    retry_delay_seconds: int = 60,
) -> dict[str, int]:
    """独立 Session 投递一批事件，保证 at-least-once 而非 exactly-once。

    claim 提交后 sender 才执行；若外部调用成功但进程在完成状态提交前崩溃，
    租约到期后事件会再次投递。外部邮件/Webhook 不支持幂等令牌时无法消除此边界。
    """
    db = session_factory()
    counts = {"delivered": 0, "retry": 0, "dead-letter": 0}
    try:
        events = claim_outbox_batch(
            db,
            worker_id=worker_id,
            limit=limit,
            lease_seconds=lease_seconds,
        )
        claimed = [(event.id, event.claim_token, event) for event in events]
        for _event_id, _token, event in claimed:
            db.expunge(event)

        for event_id, claim_token, event in claimed:
            permanent_failure = False
            try:
                ok = sender(event)
            except NonRetryableOutboxError as exc:
                ok = False
                permanent_failure = True
                error = str(exc)
            except Exception as exc:
                ok = False
                error = str(exc)
            else:
                error = "sender returned failure"

            current = db.scalar(
                select(OutboxEvent).where(
                    OutboxEvent.id == event_id,
                    OutboxEvent.status == "processing",
                    OutboxEvent.claim_token == claim_token,
                    OutboxEvent.claimed_by == worker_id,
                )
            )
            if current is None:
                db.rollback()
                continue
            if ok:
                current.status = "delivered"
                current.delivered_at = _utcnow()
                current.last_error = None
                _clear_claim(current)
                db.commit()
                counts["delivered"] += 1
                continue

            current.retry_count += 1
            current.last_error = error[:256]
            if permanent_failure or current.retry_count >= max_retries:
                current.status = "dead-letter"
                counts["dead-letter"] += 1
            else:
                current.status = "retry"
                current.available_at = _utcnow() + timedelta(seconds=retry_delay_seconds)
                counts["retry"] += 1
            _clear_claim(current)
            db.commit()
        return counts
    finally:
        db.close()
