"""Wait until HTTP endpoints return 200."""
from __future__ import annotations

import argparse
import sys
import time
import urllib.error
import urllib.request


def wait_for_urls(urls: list[str], timeout: float) -> list[str]:
    deadline = time.monotonic() + timeout
    pending = set(urls)
    while pending and time.monotonic() < deadline:
        for url in tuple(pending):
            try:
                with urllib.request.urlopen(url, timeout=2) as response:
                    if response.status == 200:
                        pending.remove(url)
            except (urllib.error.URLError, TimeoutError, OSError):
                pass
        if pending:
            time.sleep(1)
    return sorted(pending)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Wait for HTTP 200 responses")
    parser.add_argument("urls", nargs="+")
    parser.add_argument("--timeout", type=float, default=60)
    args = parser.parse_args(argv)
    pending = wait_for_urls(args.urls, args.timeout)
    if pending:
        print(f"workers not ready: {pending}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
