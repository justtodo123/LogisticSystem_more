"""Redact JSON log files before uploading CI artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path
import json
import sys

from core.json_logging import redact_mapping


def redact_line(line: str) -> str:
    text = line.strip()
    if not text:
        return ""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return json.dumps({"msg": "[non-json-line-omitted]"}, ensure_ascii=False)
    if not isinstance(payload, dict):
        return json.dumps({"msg": "[non-object-line-omitted]"}, ensure_ascii=False)
    return json.dumps(redact_mapping(payload), ensure_ascii=False, default=str)


def redact_file(source: Path, destination: Path) -> int:
    destination.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with source.open(encoding="utf-8", errors="replace") as incoming, destination.open(
        "w", encoding="utf-8", newline="\n"
    ) as outgoing:
        for raw in incoming:
            redacted = redact_line(raw)
            if not redacted:
                continue
            outgoing.write(redacted + "\n")
            count += 1
    return count


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Redact JSON log files")
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.source.exists():
        sys.stderr.write(f"missing log file: {args.source}\n")
        return 1
    count = redact_file(args.source, args.destination)
    sys.stdout.write(f"redacted_lines={count} destination={args.destination}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
