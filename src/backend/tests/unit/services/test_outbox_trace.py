"""Outbox payload metadata preserves request/trace IDs across worker attempts."""

import logging

from core.json_logging import configure_logging
from core.request_context import (
    RequestContext,
    bind_request_context,
    get_request_context,
    reset_request_context,
)
from models.outbox_event import OutboxEvent
from services.outbox_service import (
    NonRetryableOutboxError,
    attach_trace_metadata,
    deliver_outbox_batch,
    enqueue_outbox,
    execution_context_from_outbox,
    extract_trace_metadata,
)


def test_enqueue_outbox_stamps_current_request_context(db_session):
    token = bind_request_context(
        RequestContext(
            request_id="req-outbox-1",
            trace_id="trc-outbox-1",
            task_id="task-9",
            idempotency_key="idem-outbox-1",
        )
    )
    try:
        event = enqueue_outbox(
            db_session,
            dedup_key="trace-stamp-1",
            event_type="replan.completed",
            payload={"task_id": 9, "schedule_code": "GS001"},
        )
        db_session.commit()
    finally:
        reset_request_context(token)

    assert event.payload["task_id"] == 9
    assert event.payload["schedule_code"] == "GS001"
    assert event.payload["_trace"] == {
        "request_id": "req-outbox-1",
        "trace_id": "trc-outbox-1",
        "task_id": "task-9",
        "idempotency_key": "idem-outbox-1",
    }
    assert extract_trace_metadata(event.payload)["trace_id"] == "trc-outbox-1"


def test_execution_context_restores_trace_and_mints_new_request_id():
    token = bind_request_context(
        RequestContext(
            request_id="req-original",
            trace_id="trc-original",
            task_id="4",
            idempotency_key="idem-original",
        )
    )
    try:
        payload = attach_trace_metadata({"task_id": 4})
    finally:
        reset_request_context(token)
    event = OutboxEvent(
        dedup_key="trace-restore-1",
        event_type="replan.completed",
        payload=payload,
    )

    restored = execution_context_from_outbox(event)
    assert restored.trace_id == "trc-original"
    assert restored.parent_request_id == "req-original"
    assert restored.task_id == "4"
    assert restored.idempotency_key == "idem-original"
    assert restored.request_id != "req-original"
    assert restored.request_id


def test_worker_retry_and_dead_letter_keep_original_trace(db_session, caplog):
    token = bind_request_context(
        RequestContext(
            request_id="req-worker-1",
            trace_id="trc-worker-1",
            task_id="task-11",
            idempotency_key="idem-worker-1",
        )
    )
    try:
        enqueue_outbox(
            db_session,
            dedup_key="trace-retry-keep",
            event_type="notification.test",
            payload={"task_id": 11},
        )
        enqueue_outbox(
            db_session,
            dedup_key="trace-dead-keep",
            event_type="notification.test",
            payload={"task_id": 11},
        )
        db_session.commit()
    finally:
        reset_request_context(token)

    seen = []

    def sender(event):
        ctx = get_request_context()
        assert ctx is not None
        seen.append(
            {
                "dedup_key": event.dedup_key,
                "trace_id": ctx.trace_id,
                "parent_request_id": ctx.parent_request_id,
                "request_id": ctx.request_id,
                "task_id": ctx.task_id,
            }
        )
        logging.getLogger("tests.outbox.trace").info("worker_handle")
        if event.dedup_key == "trace-dead-keep":
            raise NonRetryableOutboxError("invalid payload")
        return False

    configure_logging()
    caplog.set_level(logging.INFO)
    caplog.set_level(logging.INFO, logger="services.outbox_service")
    caplog.set_level(logging.INFO, logger="tests.outbox.trace")
    result = deliver_outbox_batch(
        lambda: db_session,
        sender,
        max_retries=3,
        retry_delay_seconds=0,
    )

    assert result == {"delivered": 0, "retry": 1, "dead-letter": 1}
    assert {item["dedup_key"] for item in seen} == {"trace-retry-keep", "trace-dead-keep"}
    assert {item["trace_id"] for item in seen} == {"trc-worker-1"}
    assert {item["parent_request_id"] for item in seen} == {"req-worker-1"}
    assert {item["task_id"] for item in seen} == {"task-11"}
    assert all(item["request_id"] != "req-worker-1" for item in seen)

    stored = {event.dedup_key: event for event in db_session.query(OutboxEvent).all()}
    assert stored["trace-retry-keep"].status == "retry"
    assert stored["trace-dead-keep"].status == "dead-letter"
    assert stored["trace-retry-keep"].payload["_trace"]["trace_id"] == "trc-worker-1"
    assert stored["trace-dead-keep"].payload["_trace"]["trace_id"] == "trc-worker-1"

    traced_msgs = {
        record.getMessage()
        for record in caplog.records
        if getattr(record, "trace_id", None) == "trc-worker-1"
    }
    assert "worker_handle" in traced_msgs


def test_attach_trace_metadata_does_not_overwrite_business_payload():
    token = bind_request_context(
        RequestContext(request_id="req-keep", trace_id="trc-keep", task_id="task-keep")
    )
    try:
        payload = attach_trace_metadata(
            {
                "task_id": 44,
                "schedule_code": "GS009",
                "trace_id": "business-trace-field",
                "_trace": {"trace_id": "existing-trace", "request_id": "existing-req"},
            }
        )
        again = attach_trace_metadata(payload)
    finally:
        reset_request_context(token)

    assert again["task_id"] == 44
    assert again["schedule_code"] == "GS009"
    assert again["trace_id"] == "business-trace-field"
    assert again["_trace"]["trace_id"] == "existing-trace"
    assert again["_trace"]["request_id"] == "existing-req"
    assert "_trace" not in again["_trace"]


def test_attach_trace_metadata_preserves_non_mapping_trace_field():
    token = bind_request_context(
        RequestContext(request_id="req-nmt", trace_id="trc-nmt")
    )
    try:
        payload = attach_trace_metadata({"task_id": 1, "_trace": "business-string"})
    finally:
        reset_request_context(token)
    assert payload["_trace"] == "business-string"
    assert payload["task_id"] == 1


def test_legacy_outbox_without_trace_is_still_consumed(db_session):
    event = enqueue_outbox(
        db_session,
        dedup_key="legacy-no-trace",
        event_type="notification.test",
        payload={"task_id": 77, "schedule_code": "GS077"},
    )
    db_session.commit()
    event.payload = {"task_id": 77, "schedule_code": "GS077"}
    db_session.commit()

    restored = execution_context_from_outbox(event)
    assert restored.task_id == "77"
    assert restored.trace_id
    assert restored.request_id
    assert restored.parent_request_id is None

    seen = []

    def sender(item):
        ctx = get_request_context()
        assert ctx is not None
        seen.append(ctx.trace_id)
        return True

    result = deliver_outbox_batch(lambda: db_session, sender)
    assert result["delivered"] == 1
    assert seen
    stored = db_session.query(OutboxEvent).filter_by(dedup_key="legacy-no-trace").one()
    assert stored.status == "delivered"
    assert stored.payload == {"task_id": 77, "schedule_code": "GS077"}


def test_retry_keeps_trace_and_mints_unique_execution_ids(db_session):
    token = bind_request_context(
        RequestContext(
            request_id="req-retry-unique",
            trace_id="trc-retry-unique",
            task_id="task-retry",
            idempotency_key="idem-retry-unique",
        )
    )
    try:
        enqueue_outbox(
            db_session,
            dedup_key="trace-retry-unique",
            event_type="notification.test",
            payload={"task_id": 12, "note": "payload-keep"},
        )
        db_session.commit()
    finally:
        reset_request_context(token)

    original = db_session.query(OutboxEvent).filter_by(dedup_key="trace-retry-unique").one()
    original_trace = dict(original.payload["_trace"])
    attempts = []

    def sender(event):
        ctx = get_request_context()
        assert ctx is not None
        attempts.append(
            {
                "request_id": ctx.request_id,
                "trace_id": ctx.trace_id,
                "parent_request_id": ctx.parent_request_id,
                "payload_trace": dict(event.payload.get("_trace") or {}),
            }
        )
        return len(attempts) > 1

    first = deliver_outbox_batch(
        lambda: db_session,
        sender,
        max_retries=3,
        retry_delay_seconds=0,
    )
    assert first["retry"] == 1
    second = deliver_outbox_batch(
        lambda: db_session,
        sender,
        max_retries=3,
        retry_delay_seconds=0,
    )
    assert second["delivered"] == 1
    assert len(attempts) == 2
    assert attempts[0]["trace_id"] == attempts[1]["trace_id"] == "trc-retry-unique"
    assert attempts[0]["parent_request_id"] == attempts[1]["parent_request_id"] == "req-retry-unique"
    assert attempts[0]["request_id"] != attempts[1]["request_id"]
    assert all(item["request_id"] != "req-retry-unique" for item in attempts)
    stored = db_session.query(OutboxEvent).filter_by(dedup_key="trace-retry-unique").one()
    assert stored.status == "delivered"
    assert stored.payload["note"] == "payload-keep"
    assert stored.payload["_trace"] == original_trace
    assert stored.payload["_trace"] == attempts[0]["payload_trace"] == attempts[1]["payload_trace"]
