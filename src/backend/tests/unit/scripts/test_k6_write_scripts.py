from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[5]
K6 = ROOT / "load" / "k6"


def _read(name: str) -> str:
    return (K6 / name).read_text(encoding="utf-8")


def test_write_scripts_export_setup_and_business_metrics():
    idem = _read("idempotency.js")
    confirm = _read("confirm-conflict.js")
    helpers = _read("helpers.js")
    for source in (idem, confirm, helpers):
        assert source.count("{") == source.count("}")
        assert source.count("(") == source.count(")")
    assert "export function setup()" in idem
    assert "export function setup()" in confirm
    assert "newRequestId" in helpers
    assert "idempotency_replay_rate" in idem
    assert "duplicate_side_effects" in idem
    assert "unexpected_5xx" in idem
    assert "confirmation_success_total" in confirm
    assert "confirmation_conflict_rate" in confirm
    assert "expectedStatuses(200, 409)" in confirm
    assert 'confirmation_success_total: ["count==1"]' in confirm
    assert re.search(r"X-Request-ID", helpers)
    assert "login()" in idem
    assert "login()" in confirm
