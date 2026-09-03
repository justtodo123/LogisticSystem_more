"""Sample process RSS, connections, and /metrics during a soak run.

Intended for GitHub Actions Linux. Missing /proc, Postgres, or Redis is
recorded as null rather than crashing the sampler.
"""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_status(text: str) -> tuple[int | None, int | None, int]:
    pid = ppid = None
    rss_kb = 0
    for line in text.splitlines():
        if line.startswith("Pid:"):
            pid = int(line.split()[1])
        elif line.startswith("PPid:"):
            ppid = int(line.split()[1])
        elif line.startswith("VmRSS:"):
            rss_kb = int(line.split()[1])
    return pid, ppid, rss_kb


def process_tree_rss_kb(root_pid: int, proc_root: Path) -> int | None:
    if not proc_root.exists():
        return None
    children: dict[int, list[int]] = {}
    rss_map: dict[int, int] = {}
    for status_path in proc_root.glob("[0-9]*/status"):
        try:
            text = status_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        pid, ppid, rss_kb = parse_status(text)
        if pid is None:
            continue
        rss_map[pid] = rss_kb
        if ppid is not None:
            children.setdefault(ppid, []).append(pid)
    if root_pid not in rss_map:
        return None
    total = 0
    stack = [root_pid]
    seen: set[int] = set()
    while stack:
        pid = stack.pop()
        if pid in seen:
            continue
        seen.add(pid)
        total += rss_map.get(pid, 0)
        stack.extend(children.get(pid, []))
    return total


def read_pid(path: Path | None) -> int | None:
    if path is None or not path.exists():
        return None
    raw = path.read_text(encoding="utf-8", errors="ignore").strip()
    if not raw:
        return None
    try:
        return int(raw.split()[0])
    except ValueError:
        return None


def probe_http_json(url: str, timeout: float = 5.0) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"X-Request-ID": "soak-sample"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        try:
            payload: Any = json.loads(body)
        except json.JSONDecodeError:
            payload = {"raw": body[:500]}
        return {"ok": 200 <= resp.status < 300, "status": int(resp.status), "payload": payload}


def postgres_connections(dsn: str) -> int:
    import psycopg

    normalized = dsn.replace("postgresql+psycopg://", "postgresql://", 1)
    with psycopg.connect(normalized, connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute("select count(*) from pg_stat_activity")
            row = cur.fetchone()
    return int(row[0] if row else 0)


def redis_clients(url: str) -> int:
    import redis

    client = redis.Redis.from_url(url, socket_timeout=5)
    try:
        info = client.info("clients")
        return int(info.get("connected_clients") or 0)
    finally:
        client.close()


def collect_sample(
    *,
    pid: int | None,
    extra_pids: list[int],
    health_url: str,
    metrics_url: str,
    database_url: str | None,
    redis_url: str | None,
    proc_root: Path,
    http_probe: Callable[[str], dict[str, Any]] = probe_http_json,
    pg_probe: Callable[[str], int] = postgres_connections,
    redis_probe: Callable[[str], int] = redis_clients,
) -> dict[str, Any]:
    sample: dict[str, Any] = {
        "ts": _utc_now(),
        "rss_kb": None,
        "pg_connections": None,
        "redis_clients": None,
        "health_ok": False,
        "health_status": None,
        "outbox_backlog": None,
        "outbox_processing": None,
        "outbox_dead_letter": None,
        "cache_degraded": None,
        "errors": [],
    }
    pids = [item for item in [pid, *extra_pids] if item is not None]
    rss_total = 0
    rss_seen = False
    for item in pids:
        value = process_tree_rss_kb(item, proc_root)
        if value is None:
            sample["errors"].append(f"rss unavailable for pid {item}")
            continue
        rss_total += value
        rss_seen = True
    if rss_seen:
        sample["rss_kb"] = rss_total
    try:
        health = http_probe(health_url)
        sample["health_ok"] = bool(health.get("ok"))
        sample["health_status"] = health.get("status")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        sample["errors"].append(f"health: {exc}")
    try:
        metrics = http_probe(metrics_url)
        gauges = {}
        payload = metrics.get("payload")
        if isinstance(payload, dict):
            gauges = payload.get("gauges") or {}
        sample["outbox_backlog"] = gauges.get("outbox_backlog")
        sample["outbox_processing"] = gauges.get("outbox_processing")
        sample["outbox_dead_letter"] = gauges.get("outbox_dead_letter")
        sample["cache_degraded"] = gauges.get("cache_degraded")
    except (urllib.error.URLError, TimeoutError, OSError, AttributeError) as exc:
        sample["errors"].append(f"metrics: {exc}")
    if database_url:
        try:
            sample["pg_connections"] = pg_probe(database_url)
        except Exception as exc:  # pragma: no cover - driver/network failures
            sample["errors"].append(f"postgres: {exc}")
    if redis_url:
        try:
            sample["redis_clients"] = redis_probe(redis_url)
        except Exception as exc:  # pragma: no cover - driver/network failures
            sample["errors"].append(f"redis: {exc}")
    return sample


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sample soak runtime signals")
    parser.add_argument("--pid-file", type=Path)
    parser.add_argument("--extra-pid-file", type=Path, action="append", default=[])
    parser.add_argument("--health-url", default="http://127.0.0.1:18001/api/health")
    parser.add_argument("--metrics-url", default="http://127.0.0.1:18001/metrics")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"))
    parser.add_argument("--redis-url", default=os.environ.get("REDIS_URL"))
    parser.add_argument("--proc-root", type=Path, default=Path("/proc"))
    parser.add_argument("--interval", type=float, default=15.0)
    parser.add_argument("--duration", type=float, default=600.0)
    parser.add_argument("--stop-file", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + max(args.duration, 1.0)
    with args.output.open("w", encoding="utf-8") as handle:
        while True:
            extra = [read_pid(path) for path in args.extra_pid_file]
            sample = collect_sample(
                pid=read_pid(args.pid_file),
                extra_pids=[item for item in extra if item is not None],
                health_url=args.health_url,
                metrics_url=args.metrics_url,
                database_url=args.database_url,
                redis_url=args.redis_url,
                proc_root=args.proc_root,
            )
            handle.write(json.dumps(sample, ensure_ascii=False) + "\n")
            handle.flush()
            if args.stop_file is not None and args.stop_file.exists():
                break
            if time.monotonic() >= deadline:
                break
            time.sleep(max(args.interval, 0.1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
