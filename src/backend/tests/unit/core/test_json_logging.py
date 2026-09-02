"""JSON log redaction and formatter tests."""

import json
import logging

from core.json_logging import JsonFormatter, redact_mapping
from core.request_context import RequestContext, bind_request_context, reset_request_context


def test_redact_mapping_strips_secrets_and_dsn_like_strings():
    payload = redact_mapping(
        {
            "password": "hunter2",
            "authorization": "Bearer abc",
            "note": "ok",
            "dsn": "postgresql://user:secret@db/app",
            "nested": {"api_key": "k", "count": 1},
        }
    )
    assert payload["password"] == "[REDACTED]"
    assert payload["authorization"] == "[REDACTED]"
    assert payload["dsn"] == "[REDACTED]"
    assert payload["note"] == "ok"
    assert payload["nested"]["api_key"] == "[REDACTED]"
    assert payload["nested"]["count"] == 1


def test_json_formatter_includes_request_context_and_redacts_extra():
    token = bind_request_context(
        RequestContext(request_id="req-log", trace_id="trc-log", task_id="42")
    )
    try:
        record = logging.LogRecord(
            "test.logger",
            logging.INFO,
            __file__,
            1,
            "hello",
            (),
            None,
        )
        record.password = "hunter2"
        line = JsonFormatter().format(record)
        payload = json.loads(line)
    finally:
        reset_request_context(token)

    assert payload["msg"] == "hello"
    assert payload["request_id"] == "req-log"
    assert payload["trace_id"] == "trc-log"
    assert payload["task_id"] == "42"
    assert payload["password"] == "[REDACTED]"
