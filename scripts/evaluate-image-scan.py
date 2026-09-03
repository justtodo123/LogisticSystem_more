#!/usr/bin/env python3
"""Evaluate Trivy image reports against the repository release policy."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

BLOCKING = {"CRITICAL", "HIGH"}


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON report {path}: {exc}") from exc


def parse_date(value: str, field: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid exception {field}: {value!r}") from exc


def validate_exceptions(raw: Any, today: dt.date) -> list[dict[str, str]]:
    if not isinstance(raw, dict) or not isinstance(raw.get("exceptions"), list):
        raise ValueError("exceptions file must contain an exceptions list")
    valid: list[dict[str, str]] = []
    required = {
        "vulnerability_id",
        "image",
        "package",
        "reason",
        "owner",
        "approved_at",
        "expires_at",
        "tracking_issue",
    }
    for item in raw["exceptions"]:
        if not isinstance(item, dict) or not required <= item.keys():
            raise ValueError("every exception must contain all governance fields")
        exception = {key: str(item[key]) for key in required}
        if any(not exception[key].strip() for key in required):
            raise ValueError("exception governance fields must not be empty")
        approved_at = parse_date(exception["approved_at"], "approved_at")
        expires_at = parse_date(exception["expires_at"], "expires_at")
        if approved_at > today:
            raise ValueError(f"exception approval is in the future: {exception['vulnerability_id']}")
        if expires_at < today:
            raise ValueError(f"exception expired: {exception['vulnerability_id']}")
        if expires_at < approved_at:
            raise ValueError(f"exception expires before approval: {exception['vulnerability_id']}")
        valid.append(exception)
    return valid


def vulnerabilities(report: Any) -> list[dict[str, Any]]:
    if not isinstance(report, dict) or not isinstance(report.get("Results"), list):
        raise ValueError("Trivy report must contain Results")
    found: list[dict[str, Any]] = []
    for result in report["Results"]:
        if not isinstance(result, dict):
            continue
        target = str(result.get("Target", ""))
        for vulnerability in result.get("Vulnerabilities") or []:
            if isinstance(vulnerability, dict):
                found.append({"target": target, **vulnerability})
    return found


def matches(item: dict[str, Any], exception: dict[str, str], image: str) -> bool:
    return (
        str(item.get("VulnerabilityID", "")) == exception["vulnerability_id"]
        and image == exception["image"]
        and str(item.get("PkgName", "")) == exception["package"]
    )


def evaluate(reports: list[tuple[str, Path]], policy_path: Path, exceptions_path: Path) -> dict[str, Any]:
    policy = load_json(policy_path)
    if not isinstance(policy, dict) or policy.get("schema_version") != 1:
        raise ValueError("unsupported image scan policy")
    required_policy = {
        "policy_version": str,
        "blocking_severities": list,
        "report_only_severities": list,
        "unknown_severity": str,
        "unfixed": str,
        "scanner_errors": str,
        "missing_reports": str,
    }
    if any(not isinstance(policy.get(key), kind) for key, kind in required_policy.items()):
        raise ValueError("image scan policy is incomplete")
    blocking = {str(value).upper() for value in policy["blocking_severities"]}
    if blocking != BLOCKING:
        raise ValueError("policy must block exactly CRITICAL and HIGH")
    report_only = {str(value).upper() for value in policy["report_only_severities"]}
    if report_only != {"MEDIUM", "LOW"}:
        raise ValueError("policy must report exactly MEDIUM and LOW")
    if policy["unknown_severity"] != "report_and_fail":
        raise ValueError("policy must fail UNKNOWN severity")
    if policy["unfixed"] != "block_when_blocking_severity":
        raise ValueError("policy must block unfixed blocking severities")
    if policy["scanner_errors"] != "fail" or policy["missing_reports"] != "fail":
        raise ValueError("policy must fail scanner errors and missing reports")
    exceptions = validate_exceptions(load_json(exceptions_path), dt.date.today())
    output: dict[str, Any] = {"schema_version": 1, "policy_version": policy.get("policy_version"), "passed": True, "images": []}
    for image, path in reports:
        findings = vulnerabilities(load_json(path))
        counts: dict[str, int] = {}
        blocked: list[dict[str, Any]] = []
        excepted: list[dict[str, Any]] = []
        for item in findings:
            severity = str(item.get("Severity", "UNKNOWN")).upper()
            counts[severity] = counts.get(severity, 0) + 1
            matched = next((exc for exc in exceptions if matches(item, exc, image)), None)
            compact = {"id": item.get("VulnerabilityID"), "package": item.get("PkgName"), "severity": severity, "target": item.get("target")}
            if matched:
                compact["exception"] = matched["tracking_issue"]
                excepted.append(compact)
            elif severity in blocking or severity == "UNKNOWN":
                blocked.append(compact)
        result = {"image": image, "report": str(path), "counts": counts, "blocked": blocked, "exceptions_applied": excepted, "passed": not blocked}
        output["images"].append(result)
        output["passed"] = output["passed"] and result["passed"]
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--exceptions", type=Path, required=True)
    parser.add_argument("--report", action="append", nargs=2, metavar=("IMAGE", "PATH"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = evaluate([(image, Path(path)) for image, path in args.report], args.policy, args.exceptions)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except ValueError as exc:
        print(f"image-scan-policy: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
