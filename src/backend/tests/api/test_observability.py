"""HTTP observability: request IDs, error meta, metrics, and log correlation."""

import json
import logging

from core.json_logging import JsonFormatter
from core.metrics import metrics


def test_health_generates_and_echoes_request_ids(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    request_id = response.headers.get("x-request-id")
    trace_id = response.headers.get("x-trace-id")
    assert request_id
    assert trace_id == request_id


def test_caller_ids_are_echoed_and_invalid_ids_are_replaced(client):
    ok = client.get(
        "/api/health",
        headers={"X-Request-ID": "req-keep", "X-Trace-ID": "trc-keep", "X-Task-ID": "task-1"},
    )
    assert ok.headers["x-request-id"] == "req-keep"
    assert ok.headers["x-trace-id"] == "trc-keep"
    assert ok.headers["x-task-id"] == "task-1"

    replaced = client.get(
        "/api/health",
        headers={"X-Request-ID": "bad id", "X-Trace-ID": "also bad"},
    )
    assert replaced.headers["x-request-id"] != "bad id"
    assert replaced.headers["x-trace-id"] == replaced.headers["x-request-id"]


def test_failed_request_meta_and_logs_share_request_id(client, caplog):
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("middleware.request_context")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    caplog.set_level(logging.INFO)
    try:
        response = client.get(
            "/api/orders",
            headers={"X-Request-ID": "req-fail-1", "X-Trace-ID": "trc-fail-1"},
        )
    finally:
        logger.removeHandler(handler)

    assert response.status_code in {401, 403}
    body = response.json()
    assert body["code"] in {40100, 40300}
    assert body["meta"]["request_id"] == "req-fail-1"
    assert body["meta"]["trace_id"] == "trc-fail-1"
    assert response.headers["x-request-id"] == "req-fail-1"

    matching = [
        record
        for record in caplog.records
        if getattr(record, "request_id", None) == "req-fail-1"
    ]
    assert matching
    rendered = JsonFormatter().format(matching[0])
    payload = json.loads(rendered)
    assert payload["request_id"] == "req-fail-1"
    assert "password" not in rendered.lower() or "[REDACTED]" in rendered


def test_metrics_endpoint_counts_requests_and_errors(client):
    metrics.reset()
    client.get("/api/health")
    client.get("/api/orders")
    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    snapshot = body["data"]["counters"]
    assert "http_requests_total" in snapshot
    assert "gauges" in body["data"]
    http_count = sum(series["value"] for series in snapshot["http_requests_total"])
    assert http_count >= 2
    assert any(
        series["labels"].get("status") == "401"
        for series in snapshot.get("http_errors_total", [])
    )

    prom = client.get("/metrics", params={"format": "prometheus"})
    assert prom.status_code == 200
    assert "http_requests_total" in prom.text
    assert "outbox_backlog" in prom.text
