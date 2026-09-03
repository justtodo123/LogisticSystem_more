from __future__ import annotations

import datetime as dt
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "evaluate-image-scan.py"
SPEC = importlib.util.spec_from_file_location("evaluate_image_scan", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ImageScanPolicyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.policy = self.write(
            "policy.json",
            {
                "schema_version": 1,
                "policy_version": "test.1",
                "blocking_severities": ["CRITICAL", "HIGH"],
                "report_only_severities": ["MEDIUM", "LOW"],
                "unknown_severity": "report_and_fail",
                "unfixed": "block_when_blocking_severity",
                "scanner_errors": "fail",
                "missing_reports": "fail",
            },
        )
        self.exceptions = self.write("exceptions.json", {"schema_version": 1, "exceptions": []})

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write(self, name: str, value: object) -> Path:
        path = self.root / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def report(self, *items: tuple[str, str, str]) -> Path:
        vulnerabilities = [
            {"VulnerabilityID": identifier, "PkgName": package, "Severity": severity}
            for identifier, package, severity in items
        ]
        return self.write("report.json", {"Results": [{"Target": "runtime", "Vulnerabilities": vulnerabilities}]})

    def evaluate(self, report: Path) -> dict[str, object]:
        return MODULE.evaluate([("backend", report)], self.policy, self.exceptions)

    def test_clean_report_passes(self) -> None:
        result = self.evaluate(self.report())
        self.assertTrue(result["passed"])

    def test_high_and_unknown_block(self) -> None:
        result = self.evaluate(self.report(("CVE-1", "openssl", "HIGH"), ("CVE-2", "libc", "UNKNOWN")))
        self.assertFalse(result["passed"])
        self.assertEqual(2, len(result["images"][0]["blocked"]))

    def test_medium_and_low_are_report_only(self) -> None:
        result = self.evaluate(self.report(("CVE-1", "openssl", "MEDIUM"), ("CVE-2", "libc", "LOW")))
        self.assertTrue(result["passed"])
        self.assertEqual({"MEDIUM": 1, "LOW": 1}, result["images"][0]["counts"])

    def test_exact_unexpired_exception_passes(self) -> None:
        today = dt.date.today()
        self.exceptions = self.write(
            "exceptions.json",
            {
                "schema_version": 1,
                "exceptions": [
                    {
                        "vulnerability_id": "CVE-1",
                        "image": "backend",
                        "package": "openssl",
                        "reason": "temporary upstream wait",
                        "owner": "security-team",
                        "approved_at": str(today),
                        "expires_at": str(today + dt.timedelta(days=7)),
                        "tracking_issue": "SEC-1",
                    }
                ],
            },
        )
        result = self.evaluate(self.report(("CVE-1", "openssl", "CRITICAL")))
        self.assertTrue(result["passed"])
        self.assertEqual("SEC-1", result["images"][0]["exceptions_applied"][0]["exception"])

    def test_exception_does_not_match_other_package(self) -> None:
        today = dt.date.today()
        self.exceptions = self.write(
            "exceptions.json",
            {
                "schema_version": 1,
                "exceptions": [
                    {
                        "vulnerability_id": "CVE-1",
                        "image": "backend",
                        "package": "other",
                        "reason": "temporary upstream wait",
                        "owner": "security-team",
                        "approved_at": str(today),
                        "expires_at": str(today + dt.timedelta(days=7)),
                        "tracking_issue": "SEC-1",
                    }
                ],
            },
        )
        self.assertFalse(self.evaluate(self.report(("CVE-1", "openssl", "HIGH")))["passed"])

    def test_expired_or_incomplete_exception_fails_closed(self) -> None:
        today = dt.date.today()
        for item in (
            {
                "vulnerability_id": "CVE-1",
                "image": "backend",
                "package": "openssl",
                "reason": "expired",
                "owner": "security-team",
                "approved_at": str(today - dt.timedelta(days=2)),
                "expires_at": str(today - dt.timedelta(days=1)),
                "tracking_issue": "SEC-1",
            },
            {"vulnerability_id": "CVE-1"},
        ):
            with self.subTest(item=item):
                self.exceptions = self.write("exceptions.json", {"schema_version": 1, "exceptions": [item]})
                with self.assertRaises(ValueError):
                    self.evaluate(self.report(("CVE-1", "openssl", "HIGH")))

    def test_missing_or_malformed_report_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            self.evaluate(self.root / "missing.json")
        malformed = self.write("report.json", {"not_results": []})
        with self.assertRaises(ValueError):
            self.evaluate(malformed)

    def test_invalid_policy_fails_closed(self) -> None:
        invalid = json.loads(self.policy.read_text(encoding="utf-8"))
        invalid["unknown_severity"] = "ignore"
        self.policy = self.write("policy.json", invalid)
        with self.assertRaises(ValueError):
            self.evaluate(self.report())


if __name__ == "__main__":
    unittest.main()
