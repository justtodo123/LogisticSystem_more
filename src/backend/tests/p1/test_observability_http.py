"""P1 live probe for request IDs and /metrics."""
import os

import httpx
import pytest


def _worker_url() -> str:
    url = os.environ.get("P1_WORKER_A_URL", "").strip().rstrip("/")
    if not url:
        pytest.skip("requires P1_WORKER_A_URL")
    return url


@pytest.mark.integration
def test_p1_worker_echoes_request_id_and_exposes_metrics():
    base = _worker_url()
    with httpx.Client(timeout=15) as client:
        health = client.get(
            f"{base}/api/health",
            headers={"X-Request-ID": "p1-obs-probe", "X-Trace-ID": "p1-obs-trace"},
        )
        assert health.status_code == 200
        assert health.headers.get("x-request-id") == "p1-obs-probe"
        assert health.headers.get("x-trace-id") == "p1-obs-trace"

        metrics = client.get(f"{base}/metrics")
        assert metrics.status_code == 200
        body = metrics.json()
        assert body["code"] == 0
        assert "http_requests_total" in body["data"]["counters"]
        assert "outbox_backlog" in body["data"]["gauges"]
