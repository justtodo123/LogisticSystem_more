"""HTTP -> outbox -> worker trace continuity for R2-06."""

import logging

import pytest

from core.json_logging import JsonFormatter, configure_logging
from core.request_context import (
    RequestContext,
    bind_request_context,
    get_request_context,
    reset_request_context,
)
from models.outbox_event import OutboxEvent
from services.outbox_service import (
    NonRetryableOutboxError,
    deliver_outbox_batch,
    enqueue_outbox,
)


TRACE_ID = "trc-http-outbox-1"
REQUEST_ID = "req-http-outbox-1"
TASK_ID = "task-http-outbox-1"
IDEMPOTENCY_KEY = "idem-http-outbox-1"


@pytest.mark.integration
def test_same_trace_id_on_http_outbox_worker_retry_and_dead_letter(
    client,
    db_session,
    caplog,
):
    configure_logging()
    caplog.set_level(logging.INFO)
    headers = {
        "X-Request-ID": REQUEST_ID,
        "X-Trace-ID": TRACE_ID,
        "X-Task-ID": TASK_ID,
        "X-Idempotency-Key": IDEMPOTENCY_KEY,
    }

    health = client.get("/api/health", headers=headers)
    assert health.status_code == 200
    assert health.headers["x-request-id"] == REQUEST_ID
    assert health.headers["x-trace-id"] == TRACE_ID
    assert health.headers["x-task-id"] == TASK_ID

    denied = client.get("/api/orders", headers=headers)
    assert denied.status_code in {401, 403}
    body = denied.json()
    assert body["meta"]["request_id"] == REQUEST_ID
    assert body["meta"]["trace_id"] == TRACE_ID

    token = bind_request_context(
        RequestContext(
            request_id=REQUEST_ID,
            trace_id=TRACE_ID,
            task_id=TASK_ID,
            idempotency_key=IDEMPOTENCY_KEY,
        )
    )
    try:
        enqueue_outbox(
            db_session,
            dedup_key="http-trace-retry",
            event_type="notification.test",
            payload={"task_id": 21},
        )
        enqueue_outbox(
            db_session,
            dedup_key="http-trace-dead",
            event_type="notification.test",
            payload={"task_id": 21},
        )
        db_session.commit()
    finally:
        reset_request_context(token)

    stored = {
        event.dedup_key: event
        for event in db_session.query(OutboxEvent).all()
    }
    assert stored["http-trace-retry"].payload["_trace"]["trace_id"] == TRACE_ID
    assert stored["http-trace-retry"].payload["_trace"]["request_id"] == REQUEST_ID
    assert stored["http-trace-dead"].payload["_trace"]["task_id"] == TASK_ID
    assert stored["http-trace-dead"].payload["_trace"]["idempotency_key"] == IDEMPOTENCY_KEY

    worker_request_ids = []

    def sender(event):
        ctx = get_request_context()
        assert ctx is not None
        assert ctx.trace_id == TRACE_ID
        assert ctx.parent_request_id == REQUEST_ID
        assert ctx.task_id == TASK_ID
        worker_request_ids.append(ctx.request_id)
        logging.getLogger("tests.outbox.http").info("worker_handle")
        if event.dedup_key == "http-trace-dead":
            raise NonRetryableOutboxError("invalid payload")
        return False

    result = deliver_outbox_batch(
        lambda: db_session,
        sender,
        max_retries=3,
        retry_delay_seconds=0,
    )
    assert result["retry"] == 1
    assert result["dead-letter"] == 1
    assert result["delivered"] == 0
    assert worker_request_ids
    assert all(value != REQUEST_ID for value in worker_request_ids)

    db_session.expire_all()
    retry_event = db_session.query(OutboxEvent).filter_by(dedup_key="http-trace-retry").one()
    dead_event = db_session.query(OutboxEvent).filter_by(dedup_key="http-trace-dead").one()
    assert retry_event.status == "retry"
    assert dead_event.status == "dead-letter"
    assert retry_event.payload["_trace"]["trace_id"] == TRACE_ID
    assert dead_event.payload["_trace"]["trace_id"] == TRACE_ID

    traced = [
        record
        for record in caplog.records
        if getattr(record, "trace_id", None) == TRACE_ID
    ]
    messages = {record.getMessage() for record in traced}
    assert "http_request" in messages or any(
        getattr(record, "request_id", None) == REQUEST_ID for record in traced
    )
    assert "outbox_execute" in messages
    assert "outbox_outcome" in messages
    assert "worker_handle" in messages
    rendered = JsonFormatter().format(traced[0])
    assert TRACE_ID in rendered
    assert IDEMPOTENCY_KEY not in rendered
    assert "password" not in rendered.lower() or "[REDACTED]" in rendered
    assert all(value != REQUEST_ID for value in worker_request_ids)
    assert len(set(worker_request_ids)) == len(worker_request_ids)
