#!/usr/bin/env python3
"""Fail when tracked evidence contains credential-shaped values."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

JWT = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")
SENSITIVE_KEYS = {"access_token", "authorization", "cookie", "refresh_token", "token"}
REDACTED = "[REDACTED]"
EVIDENCE_ROOTS = (Path("load/baselines"), Path("My_doc/plan_todo/experiments"))


def tracked_files(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return [root / value.decode("utf-8") for value in result.stdout.split(b"\0") if value]


def sensitive_values(value: Any, location: str = "$") -> list[str]:
    failures: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{location}.{key}"
            if key.lower() in SENSITIVE_KEYS and item not in (None, "", REDACTED):
                failures.append(child)
            failures.extend(sensitive_values(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            failures.extend(sensitive_values(item, f"{location}[{index}]"))
    return failures


def scan(root: Path) -> list[str]:
    failures: list[str] = []
    for path in tracked_files(root):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        relative = path.relative_to(root)
        if JWT.search(text):
            failures.append(f"{relative}: JWT-shaped value")
        if path.suffix.lower() != ".json" or not any(relative.is_relative_to(base) for base in EVIDENCE_ROOTS):
            continue
        try:
            document = json.loads(text)
        except json.JSONDecodeError as exc:
            failures.append(f"{relative}: invalid JSON ({exc})")
            continue
        for location in sensitive_values(document):
            failures.append(f"{relative}:{location}: unredacted sensitive field")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    failures = scan(args.root.resolve())
    if failures:
        print("tracked-secret-check: failed", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("tracked-secret-check: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
