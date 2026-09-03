import json

from scripts.check_soak_report import evaluate_soak, main


def _sample(*, health_ok=True, rss_kb=1000, pg=4, redis=2):
    return {
        "health_ok": health_ok,
        "rss_kb": rss_kb,
        "pg_connections": pg,
        "redis_clients": redis,
    }


def _rate(rate: float) -> dict:
    return {"values": {"rate": rate, "value": rate}}


def _count(count: float) -> dict:
    return {"values": {"count": count}}


def _ok_summary() -> dict:
    return {
        "metrics": {
            "business_error_rate": _rate(0.0),
            "http_req_failed": _rate(0.0),
            "unexpected_5xx": _rate(0.0),
            "dropped_iterations": _count(0),
            "checks": _rate(1.0),
            "http_req_duration": {"values": {"p(95)": 12.0}},
        }
    }


def test_soak_smoke_passes_and_skips_p95():
    samples = [_sample(rss_kb=1000), _sample(rss_kb=1100), _sample(rss_kb=1050)]
    report = evaluate_soak(samples, _ok_summary(), mode="smoke")
    assert report["passed"] is True
    assert report["p95_regression_ok"] is None
    assert report["rss_growth_ratio"] == 1.05


def test_soak_smoke_fails_on_health_and_rss_explosion():
    samples = [
        _sample(health_ok=True, rss_kb=1000),
        _sample(health_ok=False, rss_kb=2000),
        _sample(health_ok=True, rss_kb=4000),
    ]
    report = evaluate_soak(samples, _ok_summary(), mode="smoke")
    assert report["passed"] is False
    joined = " ".join(report["failures"])
    assert "health samples failed" in joined
    assert "rss grew" in joined


def test_soak_cli_roundtrip(tmp_path):
    samples_path = tmp_path / "samples.jsonl"
    summary_path = tmp_path / "k6.json"
    out_path = tmp_path / "report.json"
    rows = [_sample(rss_kb=1000 + i) for i in range(3)]
    samples_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    summary_path.write_text(json.dumps(_ok_summary()), encoding="utf-8")
    assert main([
        "--samples", str(samples_path),
        "--k6-summary", str(summary_path),
        "--mode", "smoke",
        "--json-output", str(out_path),
    ]) == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["passed"] is True
    assert payload["p95_regression_ok"] is None
