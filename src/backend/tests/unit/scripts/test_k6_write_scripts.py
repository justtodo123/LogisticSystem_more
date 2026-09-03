from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[5]
K6 = ROOT / "load" / "k6"


def _read(name: str) -> str:
    return (K6 / name).read_text(encoding="utf-8")


def test_write_scripts_keep_vu_tokens_out_of_setup_data():
    idem = _read("idempotency.js")
    confirm = _read("confirm-conflict.js")
    helpers = _read("helpers.js")
    for source in (idem, confirm, helpers):
        assert source.count("{") == source.count("}")
        assert source.count("(") == source.count(")")
    assert "export function setup()" not in idem
    assert "export function setup()" in confirm
    assert "return { scheduleCode };" in confirm
    assert "token:" not in confirm.split("export function setup()", 1)[1].split("export function confirmSame", 1)[0]
    assert "function getVuToken()" in helpers
    assert "getVuToken()" in idem
    assert "getVuToken()" in confirm
    assert "newRequestId" in helpers
    assert "idempotency_replay_rate" in idem
    assert "duplicate_side_effects" in idem
    assert "unexpected_5xx" in idem
    assert "confirmation_success_total" in confirm
    assert "confirmation_conflict_rate" in confirm
    assert "expectedStatuses(200, 409)" in confirm
    assert 'confirmation_success_total: ["count==1"]' in confirm
    assert re.search(r"X-Request-ID", helpers)
    assert "login()" in helpers
