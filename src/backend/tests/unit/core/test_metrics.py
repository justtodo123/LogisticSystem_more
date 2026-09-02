"""In-process metrics registry tests."""

from core.error_codes import CODE_STATE_CONFLICT
from core.metrics import (
    metrics,
    observe_business_error,
    observe_cache,
    observe_http_request,
    observe_idempotency_replay,
)


def setup_function():
    metrics.reset()


def test_http_and_business_counters_and_prometheus_render():
    observe_http_request(method="GET", path="/api/health", status=200)
    observe_http_request(method="POST", path="/api/orders/{id}", status=409)
    observe_business_error(CODE_STATE_CONFLICT)
    observe_idempotency_replay()
    observe_cache(hit=True)
    observe_cache(hit=False)
    observe_cache(degraded=True)

    assert metrics.total("http_requests_total") == 2
    assert metrics.total("http_errors_total") == 1
    assert metrics.total("confirm_conflicts_total") == 1
    assert metrics.total("idempotency_replay_total") == 1
    assert metrics.total("cache_hit_total") == 1
    assert metrics.total("cache_miss_total") == 1
    assert metrics.total("cache_degraded_total") == 1

    rendered = metrics.render_prometheus()
    assert 'http_requests_total{method="GET",path="/api/health",status="200"} 1' in rendered
    assert "confirm_conflicts_total 1" in rendered
