"""Evaluate soak samples and k6 summary for a correctness-only smoke/soak gate.

Smoke does not prove the absence of leaks. Do not compare soak P95 with the
5-minute read-mix load/spike P95 or write-path P95.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from scripts.compare_k6_summaries import extract_snapshot, load_summary

ERROR_RATE_LIMIT = 0.01
RSS_GROWTH_LIMIT = 3.0
MIN_SAMPLES = 3


def load_samples(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _ratio(first: float, last: float) -> float:
    if first <= 0:
        return 0.0 if last <= 0 else float("inf")
    return last / first


def evaluate_soak(
    samples: list[dict[str, Any]],
    summary: dict[str, Any] | None,
    *,
    mode: str = "smoke",
) -> dict[str, Any]:
    failures: list[str] = []
    notes: list[str] = [
        "Soak smoke checks harness correctness only.",
        "It does not prove the absence of leaks.",
        "Do not compare soak P95 with 5m read-mix or write-path P95.",
    ]
    if len(samples) < MIN_SAMPLES:
        failures.append(f"expected at least {MIN_SAMPLES} samples, got {len(samples)}")
    unhealthy = [row for row in samples if not row.get("health_ok")]
    if unhealthy:
        failures.append(f"{len(unhealthy)} health samples failed")

    rss_values = [int(row["rss_kb"]) for row in samples if row.get("rss_kb") is not None]
    pg_values = [int(row["pg_connections"]) for row in samples if row.get("pg_connections") is not None]
    redis_values = [int(row["redis_clients"]) for row in samples if row.get("redis_clients") is not None]
    rss_growth = _ratio(rss_values[0], rss_values[-1]) if len(rss_values) >= 2 else None
    if rss_growth is not None and rss_growth >= RSS_GROWTH_LIMIT:
        failures.append(f"rss grew {rss_growth:.2f}x, limit {RSS_GROWTH_LIMIT:.0f}x")

    snapshot = extract_snapshot(summary) if summary is not None else None
    error_rate = float(snapshot["error_rate"]) if snapshot else 0.0
    unexpected_5xx = float(snapshot["unexpected_5xx"]) if snapshot else 0.0
    dropped = float(snapshot["dropped_iterations"]) if snapshot else 0.0
    checks_rate = float(snapshot["checks_rate"]) if snapshot else 1.0
    if snapshot is None:
        failures.append("k6 summary missing")
    else:
        if error_rate >= ERROR_RATE_LIMIT:
            failures.append(f"error rate {error_rate:.4%} exceeds {ERROR_RATE_LIMIT:.0%}")
        if unexpected_5xx > 0:
            failures.append("unexpected 5xx > 0")
        if checks_rate < 1:
            failures.append("k6 checks failed")

    return {
        "mode": mode,
        "sample_count": len(samples),
        "health_ok": not unhealthy,
        "error_rate_ok": error_rate < ERROR_RATE_LIMIT,
        "unexpected_5xx_ok": unexpected_5xx <= 0,
        "dropped_iterations": int(dropped),
        "rss_kb_first": rss_values[0] if rss_values else None,
        "rss_kb_last": rss_values[-1] if rss_values else None,
        "rss_growth_ratio": None if rss_growth is None else round(rss_growth, 3),
        "pg_connections_first": pg_values[0] if pg_values else None,
        "pg_connections_last": pg_values[-1] if pg_values else None,
        "redis_clients_first": redis_values[0] if redis_values else None,
        "redis_clients_last": redis_values[-1] if redis_values else None,
        "p95": None if snapshot is None else snapshot.get("p95"),
        "p95_regression_ok": None,
        "notes": notes,
        "failures": failures,
        "passed": not failures,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Correctness-only soak/smoke gate")
    parser.add_argument("--samples", type=Path, required=True)
    parser.add_argument("--k6-summary", type=Path)
    parser.add_argument("--mode", choices=("smoke", "soak"), default="smoke")
    parser.add_argument("--json-output", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary = load_summary(args.k6_summary) if args.k6_summary else None
    report = evaluate_soak(load_samples(args.samples), summary, mode=args.mode)
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(encoded, encoding="utf-8")
    sys.stdout.write(encoded)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
