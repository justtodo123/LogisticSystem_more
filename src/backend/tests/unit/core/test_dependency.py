"""Dependency instrumentation stays low-cardinality and redacts secrets."""

import logging

from core.dependency import observe_dependency, outbound_trace_headers, track_dependency
from core.json_logging import JsonFormatter, configure_logging
from core.metrics import metrics
from core.request_context import RequestContext, bind_request_context, reset_request_context


class _ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.messages = []
        self.lines = []

    def emit(self, record):
        self.messages.append(record.getMessage())
        self.lines.append(JsonFormatter().format(record))


def _capture_logger(name: str) -> tuple[logging.Logger, _ListHandler]:
    handler = _ListHandler()
    handler.setLevel(logging.INFO)
    log = logging.getLogger(name)
    log.setLevel(logging.INFO)
    log.disabled = False
    log.propagate = True
    log.addHandler(handler)
    return log, handler


def setup_function():
    metrics.reset()


def test_outbound_headers_copy_ids_without_inventing_secrets():
    token = bind_request_context(
        RequestContext(request_id="req-dep-1", trace_id="trc-dep-1", task_id="task-dep-1")
    )
    try:
        headers = outbound_trace_headers({"Authorization": "Bearer secret-token"})
    finally:
        reset_request_context(token)

    assert headers["X-Request-ID"] == "req-dep-1"
    assert headers["X-Trace-ID"] == "trc-dep-1"
    assert headers["X-Task-ID"] == "task-dep-1"
    assert headers["Authorization"] == "Bearer secret-token"


def test_observe_dependency_records_counters_and_structured_log():
    token = bind_request_context(
        RequestContext(request_id="req-dep-2", trace_id="trc-dep-2")
    )
    configure_logging()
    log, handler = _capture_logger("core.dependency")
    try:
        observe_dependency(
            dependency="redis",
            operation="get",
            status="ok",
            duration_ms=12.34,
        )
        observe_dependency(
            dependency="deepseek",
            operation="chat",
            status="error",
            duration_ms=50,
            error_type="TimeoutException",
        )
        assert "dependency_call" in handler.messages
        line = handler.lines[0]
    finally:
        log.removeHandler(handler)
        reset_request_context(token)

    assert metrics.total("dependency_calls_total") == 2
    assert metrics.total("dependency_errors_total") == 1
    rendered = metrics.render_prometheus()
    assert 'dependency_calls_total{dependency="redis",operation="get",status="ok"} 1' in rendered
    assert "user_id" not in rendered
    assert "http://example.com/?key=secret" not in rendered
    assert "trc-dep-2" in line
    assert "token" not in line.lower() or "[REDACTED]" in line


def test_track_dependency_marks_errors():
    try:
        with track_dependency("wechat", "webhook"):
            raise ConnectionError("down")
    except ConnectionError:
        pass
    assert metrics.total("dependency_calls_total", dependency="wechat", operation="webhook", status="error") == 1
    assert metrics.total("dependency_errors_total") == 1


def test_observe_dependency_redacts_unbounded_labels():
    observe_dependency(
        dependency="https://example.com/orders/123?token=secret",
        operation="user_id=9",
        status="ok",
        duration_ms=1,
    )
    rendered = metrics.render_prometheus()
    assert "example.com" not in rendered
    assert "token=secret" not in rendered
    assert "user_id=9" not in rendered
    assert 'dependency="redacted"' in rendered
    assert 'operation="redacted"' in rendered
