from pathlib import Path
import json

from scripts.redact_json_logs import redact_file, redact_line


def test_redact_line_hashes_idempotency_and_secrets():
    line = json.dumps(
        {
            "msg": "http_request",
            "authorization": "Bearer secret-token",
            "idempotency_key": "caller-raw-key",
            "trace_id": "trc-1",
        }
    )
    payload = json.loads(redact_line(line))
    assert payload["authorization"] == "[REDACTED]"
    assert payload["idempotency_key"].startswith("idem-")
    assert payload["idempotency_key"] != "caller-raw-key"
    assert payload["trace_id"] == "trc-1"


def test_redact_file_skips_non_json():
    scratch = Path(__file__).parent / "data"
    source = scratch / "_tmp_raw.log"
    dest = scratch / "_tmp_redacted.log"
    try:
        source.write_text(
            json.dumps({"password": "hunter2", "msg": "ok"}) + "\nnot json\n\n",
            encoding="utf-8",
        )
        count = redact_file(source, dest)
        assert count == 2
        lines = dest.read_text(encoding="utf-8").splitlines()
        first = json.loads(lines[0])
        assert first["password"] == "[REDACTED]"
        assert json.loads(lines[1])["msg"] == "[non-json-line-omitted]"
    finally:
        for path in (source, dest):
            if path.exists():
                path.unlink()
