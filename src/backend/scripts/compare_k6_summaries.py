"""Compare k6 summary-export JSON files and emit a regression report.

Rules (R2-06):
- error rate < 1%
- no unexpected 5xx
- P95 regression versus baseline <= 15% (skipped when establishing a baseline)
- no duplicate side effects
- compare the same scenario only; never mix read-mix P95 with write-path P95
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ERROR_RATE_LIMIT = 0.01
P95_REGRESSION_LIMIT = 0.15
WRITE_SCENARIOS = frozenset({"idempotency", "confirm-conflict"})
READ_SCENARIOS = frozenset({"load", "spike", "read-mix"})


def load_summary(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or "metrics" not in payload:
        raise ValueError(f"{path} is not a k6 summary-export file")
    return payload


_METRIC_META_KEYS = frozenset({"values", "thresholds", "type", "contains"})


def _values(summary: dict[str, Any], name: str) -> dict[str, Any]:
    metric = (summary.get("metrics") or {}).get(name) or {}
    if not isinstance(metric, dict):
        return {}
    merged: dict[str, Any] = {}
    nested = metric.get("values")
    if isinstance(nested, dict):
        merged.update(nested)
    for key, value in metric.items():
        if key in _METRIC_META_KEYS:
            continue
        merged.setdefault(key, value)
    return merged


def metric_rate(summary: dict[str, Any], name: str, default: float = 0.0) -> float:
    values = _values(summary, name)
    if "rate" in values:
        return float(values["rate"])
    if "value" in values:
        return float(values["value"])
    return default


def metric_count(summary: dict[str, Any], name: str, default: float = 0.0) -> float:
    values = _values(summary, name)
    if "count" in values:
        return float(values["count"])
    if "fails" in values:
        return float(values["fails"])
    if "passes" in values:
        return float(values["passes"])
    return default


def metric_percentile(summary: dict[str, Any], name: str, percentile: str) -> float | None:
    values = _values(summary, name)
    raw = values.get(percentile)
    if raw is None:
        return None
    return float(raw)


def _first_present(summary: dict[str, Any], names: list[str], reader, default=0.0):
    for name in names:
        if name in (summary.get("metrics") or {}):
            return reader(summary, name)
    return default


def extract_snapshot(summary: dict[str, Any]) -> dict[str, float | None]:
    error_rate = _first_present(
        summary,
        ["business_error_rate", "http_req_failed"],
        metric_rate,
    )
    unexpected_5xx = _first_present(
        summary,
        ["unexpected_5xx"],
        metric_rate,
        default=0.0,
    )
    dropped = metric_count(summary, "dropped_iterations")
    duplicate = metric_count(summary, "duplicate_side_effects")
    success_total = metric_count(summary, "confirmation_success_total")
    write_p95 = metric_percentile(summary, "write_duration", "p(95)") or metric_percentile(
        summary, "http_req_duration{name:write}", "p(95)"
    )
    confirm_p95 = metric_percentile(summary, "confirm_duration", "p(95)") or metric_percentile(
        summary, "http_req_duration{name:confirm}", "p(95)"
    )
    return {
        "error_rate": float(error_rate),
        "unexpected_5xx": float(unexpected_5xx),
        "p95": metric_percentile(summary, "http_req_duration", "p(95)"),
        "p99": metric_percentile(summary, "http_req_duration", "p(99)"),
        "read_p95": metric_percentile(summary, "http_req_duration{name:health}", "p(95)"),
        "write_p95": write_p95,
        "confirm_p95": confirm_p95,
        "login_p95": metric_percentile(summary, "http_req_duration{name:login}", "p(95)"),
        "dropped_iterations": float(dropped),
        "duplicate_side_effects": float(duplicate),
        "confirmation_success_total": float(success_total),
        "confirmation_conflict_rate": metric_rate(summary, "confirmation_conflict_rate"),
        "idempotency_replay_rate": metric_rate(summary, "idempotency_replay_rate"),
        "checks_rate": metric_rate(summary, "checks", default=1.0),
    }


def _pct_change(baseline: float | None, candidate: float | None) -> float | None:
    if baseline is None or candidate is None:
        return None
    if baseline == 0:
        return 0.0 if candidate == 0 else None
    return (candidate - baseline) / baseline


def _scenario_p95(snapshot: dict[str, float | None], scenario: str | None) -> float | None:
    if scenario == "idempotency":
        return snapshot.get("write_p95") or snapshot.get("p95")
    if scenario == "confirm-conflict":
        return snapshot.get("confirm_p95") or snapshot.get("p95")
    return snapshot.get("p95")


def evaluate(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    *,
    scenario: str | None = None,
    establish_baseline: bool = False,
) -> dict[str, Any]:
    before = extract_snapshot(baseline)
    after = extract_snapshot(candidate)
    failures: list[str] = []
    notes: list[str] = []
    scenario_name = scenario or "unspecified"

    error_rate_ok = after["error_rate"] < ERROR_RATE_LIMIT
    unexpected_5xx_ok = after["unexpected_5xx"] <= 0
    duplicate_ok = after["duplicate_side_effects"] <= 0

    if not error_rate_ok:
        failures.append(
            f"error rate {after['error_rate']:.4%} exceeds {ERROR_RATE_LIMIT:.0%}"
        )
    if not unexpected_5xx_ok:
        failures.append(f"unexpected 5xx rate {after['unexpected_5xx']:.4%} > 0")
    if not duplicate_ok:
        failures.append(
            f"duplicate side effects {after['duplicate_side_effects']:.0f} > 0"
        )
    if scenario_name == "confirm-conflict" and after["confirmation_success_total"] > 1:
        failures.append(
            f"confirmation succeeded {after['confirmation_success_total']:.0f} times"
        )
    if after["checks_rate"] < 1 and after["error_rate"] >= ERROR_RATE_LIMIT:
        failures.append(f"checks rate {after['checks_rate']:.4%} below gate")

    before_p95 = _scenario_p95(before, scenario_name)
    after_p95 = _scenario_p95(after, scenario_name)
    p95_change = None if establish_baseline else _pct_change(before_p95, after_p95)
    p95_regression_ok: bool | None
    if establish_baseline:
        p95_regression_ok = None
        notes.append("建立写路径 baseline。")
        notes.append("relative P95 gate skipped until a second comparable run exists")
    elif p95_change is not None and p95_change > P95_REGRESSION_LIMIT:
        p95_regression_ok = False
        failures.append(
            f"P95 regression {p95_change:.1%} exceeds {P95_REGRESSION_LIMIT:.0%}"
        )
    elif p95_change is None and after_p95 is not None and before_p95 is None:
        p95_regression_ok = None
        notes.append("candidate has P95 but baseline does not; skipped relative gate")
    else:
        p95_regression_ok = True if p95_change is not None else None

    p99_change = None if establish_baseline else _pct_change(before["p99"], after["p99"])
    if p99_change is not None and p99_change > P95_REGRESSION_LIMIT:
        notes.append(f"P99 changed {p99_change:.1%} versus baseline")

    if after["dropped_iterations"] > max(before["dropped_iterations"], 0) and after[
        "dropped_iterations"
    ] > 0:
        notes.append(
            f"dropped iterations {after['dropped_iterations']:.0f} vs baseline "
            f"{before['dropped_iterations']:.0f}"
        )

    machine = {
        "scenario": scenario_name,
        "mode": "establish_baseline" if establish_baseline else "compare",
        "error_rate_ok": error_rate_ok,
        "unexpected_5xx_ok": unexpected_5xx_ok,
        "p95_regression_pct": None if p95_change is None else round(p95_change * 100, 1),
        "p95_regression_ok": p95_regression_ok,
        "duplicate_side_effects": int(after["duplicate_side_effects"]),
        "passed": not failures,
    }
    if establish_baseline:
        machine["note"] = "建立写路径 baseline。"

    return {
        "scenario": scenario_name,
        "establish_baseline": establish_baseline,
        "baseline": before,
        "candidate": after,
        "p95_change": p95_change,
        "p99_change": p99_change,
        "failures": failures,
        "notes": notes,
        "passed": not failures,
        "machine": machine,
    }


def render_report(result: dict[str, Any], baseline_path: Path, candidate_path: Path) -> str:
    status = "PASS" if result["passed"] else "FAIL"
    mode = "establish baseline" if result.get("establish_baseline") else "compare"
    lines = [
        f"k6 regression report: {status}",
        f"scenario: {result.get('scenario') or 'unspecified'}",
        f"mode: {mode}",
        f"baseline: {baseline_path}",
        f"candidate: {candidate_path}",
        "",
        "metric,baseline,candidate,change",
    ]
    keys = [
        "error_rate",
        "unexpected_5xx",
        "p95",
        "p99",
        "login_p95",
        "write_p95",
        "confirm_p95",
        "dropped_iterations",
        "duplicate_side_effects",
        "confirmation_conflict_rate",
        "idempotency_replay_rate",
        "checks_rate",
    ]
    for key in keys:
        left = result["baseline"].get(key)
        right = result["candidate"].get(key)
        change = None if result.get("establish_baseline") else _pct_change(left, right)
        change_text = "" if change is None else f"{change:.1%}"
        lines.append(f"{key},{_fmt(left)},{_fmt(right)},{change_text}")
    if result["failures"]:
        lines.append("")
        lines.append("failures:")
        lines.extend(f"- {item}" for item in result["failures"])
    if result["notes"]:
        lines.append("")
        lines.append("notes:")
        lines.extend(f"- {item}" for item in result["notes"])
    return "\n".join(lines) + "\n"


def _fmt(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.6g}"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare two k6 summary-export files")
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--output", type=Path, help="Write text report to this path")
    parser.add_argument("--json-output", type=Path, help="Write machine-readable JSON report")
    parser.add_argument(
        "--scenario",
        choices=sorted(WRITE_SCENARIOS | READ_SCENARIOS | {"unspecified"}),
        default="unspecified",
        help="Compare one scenario; do not mix read-mix with write-path P95",
    )
    parser.add_argument(
        "--establish-baseline",
        action="store_true",
        help="Record absolute gates only; do not claim a relative P95 pass",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Always exit 0 after writing the report",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    scenario = None if args.scenario == "unspecified" else args.scenario
    result = evaluate(
        load_summary(args.baseline),
        load_summary(args.candidate),
        scenario=scenario,
        establish_baseline=args.establish_baseline,
    )
    report = render_report(result, args.baseline, args.candidate)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(result["machine"], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    sys.stdout.write(report)
    if args.report_only or result["passed"]:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
