"""Outbox gauge helpers used by /metrics."""

from services.observability_service import collect_runtime_gauges, outbox_status_counts
from services.outbox_service import enqueue_outbox


def test_outbox_status_counts_and_gauges(db_session):
    enqueue_outbox(
        db_session,
        dedup_key="obs-pending-1",
        event_type="notification.test",
        payload={"task_id": 1},
    )
    dead = enqueue_outbox(
        db_session,
        dedup_key="obs-dead-1",
        event_type="notification.test",
        payload={"task_id": 2},
    )
    dead.status = "dead-letter"
    db_session.commit()

    counts = outbox_status_counts(db_session)
    assert counts["pending"] == 1
    assert counts["dead-letter"] == 1

    gauges = collect_runtime_gauges()
    assert "outbox_backlog" in gauges
    assert "outbox_dead_letter" in gauges
    assert "cache_degraded" in gauges
