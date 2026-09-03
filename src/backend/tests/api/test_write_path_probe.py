from models.outbox_event import OutboxEvent
from scripts.probe_outbox_trace import (
    HTTP_REQUEST_ID,
    HTTP_TASK_ID,
    HTTP_TRACE_ID,
    PROBE_KEYS,
    PROBE_PATH,
)


def _probe_headers():
    return {
        "X-Request-ID": HTTP_REQUEST_ID,
        "X-Trace-ID": HTTP_TRACE_ID,
        "X-Task-ID": HTTP_TASK_ID,
    }


def test_write_path_probe_enqueues_traced_outbox_rows(client, db_session):
    response = client.post(PROBE_PATH, headers=_probe_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert response.headers["X-Request-ID"] == HTTP_REQUEST_ID
    assert response.headers["X-Trace-ID"] == HTTP_TRACE_ID
    assert response.headers["X-Task-ID"] == HTTP_TASK_ID
    assert body["data"]["request_id"] == HTTP_REQUEST_ID
    assert body["data"]["trace_id"] == HTTP_TRACE_ID
    assert {item["dedup_key"] for item in body["data"]["enqueued"]} == set(PROBE_KEYS)

    db_session.expire_all()
    rows = {
        row.dedup_key: row
        for row in db_session.query(OutboxEvent).filter(OutboxEvent.dedup_key.in_(PROBE_KEYS))
    }
    assert set(rows) == set(PROBE_KEYS)
    for key, row in rows.items():
        payload = row.payload
        assert payload["case"] == key.rsplit("-", 1)[-1]
        assert payload["_trace"]["request_id"] == HTTP_REQUEST_ID
        assert payload["_trace"]["trace_id"] == HTTP_TRACE_ID
        assert payload["_trace"]["task_id"] == HTTP_TASK_ID


def test_write_path_probe_hidden_outside_dev(client, db_session, monkeypatch):
    from config.settings import settings

    monkeypatch.setattr(settings, "ENV", "prod")
    response = client.post(PROBE_PATH, headers=_probe_headers())
    assert response.status_code == 404
    body = response.json()
    assert body["code"] == 40400
    db_session.expire_all()
    count = (
        db_session.query(OutboxEvent)
        .filter(OutboxEvent.dedup_key.in_(PROBE_KEYS))
        .count()
    )
    assert count == 0
