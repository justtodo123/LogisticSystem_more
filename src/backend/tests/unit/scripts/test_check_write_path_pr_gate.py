from scripts.check_write_path_pr_gate import evaluate_pr_gate, main


def _rate(rate: float) -> dict:
    return {"values": {"rate": rate, "value": rate}}


def _count(count: float) -> dict:
    return {"values": {"count": count}}


def _ok_idempotency() -> dict:
    return {
        "metrics": {
            "business_error_rate": _rate(0.0),
            "unexpected_5xx": _rate(0.0),
            "duplicate_side_effects": _count(0),
            "checks": _rate(1.0),
            "write_duration": {"values": {"p(95)": 20.0}},
        }
    }


def _ok_confirm() -> dict:
    return {
        "metrics": {
            "business_error_rate": _rate(0.0),
            "unexpected_5xx": _rate(0.0),
            "duplicate_side_effects": _count(0),
            "confirmation_success_total": _count(1),
            "checks": _rate(1.0),
            "confirm_duration": {"values": {"p(95)": 800.0}},
        }
    }


def test_pr_gate_passes_correctness_and_skips_p95():
    report = evaluate_pr_gate(_ok_idempotency(), _ok_confirm())
    assert report["passed"] is True
    assert report["p95_regression_ok"] is None
    assert report["mode"] == "pr_correctness"


def test_pr_gate_fails_on_5xx_and_duplicate_success(tmp_path):
    idem = _ok_idempotency()
    idem["metrics"]["unexpected_5xx"] = _rate(0.1)
    confirm = _ok_confirm()
    confirm["metrics"]["confirmation_success_total"] = _count(2)
    confirm["metrics"]["duplicate_side_effects"] = _count(1)
    report = evaluate_pr_gate(idem, confirm)
    assert report["passed"] is False
    assert report["unexpected_5xx_ok"] is False
    assert report["duplicate_side_effects"] == 1
    joined = " ".join(report["failures"])
    assert "unexpected 5xx" in joined
    assert "confirmation succeeded 2 times" in joined


def test_pr_gate_cli_roundtrip(tmp_path):
    import json
    from pathlib import Path as P

    idem_path = tmp_path / "idem.json"
    conf_path = tmp_path / "confirm.json"
    out_path = tmp_path / "gate.json"
    idem_path.write_text(json.dumps(_ok_idempotency()), encoding="utf-8")
    conf_path.write_text(json.dumps(_ok_confirm()), encoding="utf-8")
    assert main(['--idempotency', str(idem_path), '--confirm', str(conf_path), '--json-output', str(out_path)]) == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["passed"] is True
    assert payload["p95_regression_ok"] is None
