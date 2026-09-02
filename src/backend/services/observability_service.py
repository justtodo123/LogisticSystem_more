"""Read-time gauges that complement the in-process R2-06 counters."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.outbox_event import OutboxEvent


def outbox_status_counts(db: Session) -> dict[str, int]:
    rows = db.execute(
        select(OutboxEvent.status, func.count()).group_by(OutboxEvent.status)
    ).all()
    return {str(status): int(count) for status, count in rows}


def collect_runtime_gauges() -> dict[str, int]:
    gauges = {
        "cache_degraded": 0,
        "outbox_backlog": 0,
        "outbox_dead_letter": 0,
        "outbox_processing": 0,
    }
    try:
        from utils.cache import redis_runtime_status

        if redis_runtime_status() == "degraded":
            gauges["cache_degraded"] = 1
    except Exception:
        pass

    try:
        from config.database import SessionLocal

        db = SessionLocal()
        try:
            counts = outbox_status_counts(db)
        finally:
            db.close()
        gauges["outbox_backlog"] = int(counts.get("pending", 0)) + int(counts.get("retry", 0))
        gauges["outbox_dead_letter"] = int(counts.get("dead-letter", 0))
        gauges["outbox_processing"] = int(counts.get("processing", 0))
    except Exception:
        gauges["metrics_degraded"] = 1
    return gauges
