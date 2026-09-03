from pathlib import Path
import json

from scripts.compare_k6_summaries import evaluate, load_summary, main

DATA = Path(__file__).parent / "data"


def test_comparator_passes_within_p95_budget(capsys):
    baseline = DATA / "k6_baseline.json"
    candidate = DATA / "k6_candidate_ok.json"
    assert main([str(baseline), str(candidate), "--scenario", "idempotency"]) == 0
    captured = capsys.readouterr()
    assert captured.out.startswith("k6 regression report: PASS")
    result = evaluate(load_summary(baseline), load_summary(candidate), scenario="idempotency")
    assert result["passed"] is True
    assert result["machine"]["error_rate_ok"] is True
    assert result["machine"]["unexpected_5xx_ok"] is True
    assert result["machine"]["p95_regression_ok"] is True
    assert result["machine"]["duplicate_side_effects"] == 0
    assert result["p95_change"] is not None
    assert result["p95_change"] < 0.15


def test_comparator_fails_on_error_rate_5xx_and_duplicates(capsys):
    baseline = DATA / "k6_baseline.json"
    candidate = DATA / "k6_candidate_fail.json"
    assert main([str(baseline), str(candidate)]) == 1
    captured = capsys.readouterr()
    assert "FAIL" in captured.out
    assert "error rate" in captured.out
    assert "unexpected 5xx" in captured.out
    assert "duplicate side effects" in captured.out
    assert main([str(baseline), str(candidate), "--report-only"]) == 0


def test_comparator_fails_on_p95_degradation():
    baseline = DATA / "k6_baseline.json"
    candidate = DATA / "k6_candidate_degraded.json"
    json_path = DATA / "_tmp_degraded_report.json"
    try:
        assert main([
            str(baseline),
            str(candidate),
            "--scenario",
            "idempotency",
            "--json-output",
            str(json_path),
        ]) == 1
        report = json.loads(json_path.read_text(encoding="utf-8"))
    finally:
        if json_path.exists():
            json_path.unlink()
    assert report["scenario"] == "idempotency"
    assert report["error_rate_ok"] is True
    assert report["unexpected_5xx_ok"] is True
    assert report["p95_regression_ok"] is False
    assert report["p95_regression_pct"] > 15
    assert report["passed"] is False


def test_comparator_fails_on_unexpected_5xx_only():
    result = evaluate(
        load_summary(DATA / "k6_baseline.json"),
        load_summary(DATA / "k6_candidate_5xx.json"),
        scenario="idempotency",
    )
    assert result["passed"] is False
    assert result["machine"]["unexpected_5xx_ok"] is False
    assert result["machine"]["error_rate_ok"] is True
    assert any("unexpected 5xx" in item for item in result["failures"])


def test_comparator_fails_on_duplicate_side_effects_only():
    result = evaluate(
        load_summary(DATA / "k6_baseline.json"),
        load_summary(DATA / "k6_candidate_duplicates.json"),
        scenario="confirm-conflict",
    )
    assert result["passed"] is False
    assert result["machine"]["duplicate_side_effects"] == 2
    assert any("duplicate side effects" in item for item in result["failures"])


def test_establish_baseline_skips_relative_p95():
    candidate = DATA / "k6_candidate_degraded.json"
    json_path = DATA / "_tmp_baseline_report.json"
    try:
        assert main([
            str(candidate),
            str(candidate),
            "--scenario",
            "idempotency",
            "--establish-baseline",
            "--json-output",
            str(json_path),
        ]) == 0
        report = json.loads(json_path.read_text(encoding="utf-8"))
    finally:
        if json_path.exists():
            json_path.unlink()
    assert report["mode"] == "establish_baseline"
    assert report["p95_regression_ok"] is None
    assert report["note"] == "建立写路径 baseline。"
    assert report["passed"] is True
