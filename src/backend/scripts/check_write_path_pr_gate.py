"""PR write-path gate: correctness only.

Never compare 30s smoke P95 with the 5-minute write-path baseline or the
read-mix load/spike P95.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from scripts.compare_k6_summaries import extract_snapshot, load_summary

ERROR_RATE_LIMIT = 0.01


def evaluate_pr_gate(idempotency: dict, confirm: dict) -> dict:
    idem = extract_snapshot(idempotency)
    conf = extract_snapshot(confirm)
    failures: list[str] = []
    if idem["error_rate"] >= ERROR_RATE_LIMIT:
        failures.append(f"idempotency error rate {idem['error_rate']:.4%} exceeds {ERROR_RATE_LIMIT:.0%}")
    if conf["error_rate"] >= ERROR_RATE_LIMIT:
        failures.append(f"confirm error rate {conf['error_rate']:.4%} exceeds {ERROR_RATE_LIMIT:.0%}")
    if idem["unexpected_5xx"] > 0:
        failures.append("idempotency unexpected 5xx > 0")
    if conf["unexpected_5xx"] > 0:
        failures.append("confirm unexpected 5xx > 0")
    if idem["duplicate_side_effects"] > 0 or conf["duplicate_side_effects"] > 0:
        failures.append("duplicate side effects > 0")
    success_total = conf.get("confirmation_success_total") or 0
    if success_total != 1:
        failures.append(f"confirmation succeeded {success_total:.0f} times, expected 1")
    if (idem.get("checks_rate") or 1) < 1:
        failures.append("idempotency checks failed")
    if (conf.get("checks_rate") or 1) < 1:
        failures.append("confirm checks failed")
    return {
        "mode": "pr_correctness",
        "error_rate_ok": idem["error_rate"] < ERROR_RATE_LIMIT and conf["error_rate"] < ERROR_RATE_LIMIT,
        "unexpected_5xx_ok": idem["unexpected_5xx"] <= 0 and conf["unexpected_5xx"] <= 0,
        "duplicate_side_effects": int(idem["duplicate_side_effects"] + conf["duplicate_side_effects"]),
        "confirmation_success_total": int(success_total),
        "p95_regression_ok": None,
        "note": "PR gate checks correctness only; it does not compare smoke P95 with the 5m write-path baseline or read-mix P95.",
        "failures": failures,
        "passed": not failures,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Correctness-only write-path PR gate")
    parser.add_argument("--idempotency", type=Path, required=True)
    parser.add_argument("--confirm", type=Path, required=True)
    parser.add_argument("--json-output", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = evaluate_pr_gate(load_summary(args.idempotency), load_summary(args.confirm))
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(encoded, encoding="utf-8")
    sys.stdout.write(encoded)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
