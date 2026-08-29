from collections.abc import Callable, Mapping
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from models.outbox_event import OutboxEvent
from models.replan_task import ReplanTask


class RetryableOutboxError(RuntimeError):
    """投递暂时失败，可按退避时间重试。"""


class NonRetryableOutboxError(RuntimeError):
    """投递永久失败，应直接进入 dead-letter。"""


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


def _claim_batch(db: Session, *, limit: int) -> list[OutboxEvent]:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    events = list(
        db.scalars(
            select(OutboxEvent)
            .where(
                OutboxEvent.status.in_(["pending", "retry"]),
                OutboxEvent.available_at <= now,
            )
            .order_by(OutboxEvent.id)
            .limit(limit)
        )
    )
    return events


def deliver_outbox_batch(
    session_factory: sessionmaker,
    sender: Callable[[OutboxEvent], bool],
    *,
    limit: int = 100,
    max_retries: int = 3,
    retry_delay_seconds: int = 60,
) -> dict[str, int]:
    """用独立 Session 投递一批事件；sender 在数据库事务外执行。"""
    db = session_factory()
    counts = {"delivered": 0, "retry": 0, "dead-letter": 0}
    try:
        events = _claim_batch(db, limit=limit)
        for event in events:
            db.expunge(event)
        db.rollback()
        for event in events:
            event_id = event.id
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
            if ok:
                # Re-read after external I/O: another worker may have completed it.
                current = db.get(OutboxEvent, event_id)
                if current is None or current.status == "delivered":
                    continue
                current.status = "delivered"
                current.delivered_at = datetime.now(timezone.utc).replace(tzinfo=None)
                current.last_error = None
                db.commit()
                counts["delivered"] += 1
                continue

            current = db.get(OutboxEvent, event_id)
            if current is None or current.status == "delivered":
                continue
            current.retry_count += 1
            current.last_error = error[:256]
            if permanent_failure or current.retry_count >= max_retries:
                current.status = "dead-letter"
                counts["dead-letter"] += 1
            else:
                current.status = "retry"
                current.available_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=retry_delay_seconds)
                counts["retry"] += 1
            db.commit()
        return counts
    finally:
        db.close()
