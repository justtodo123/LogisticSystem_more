"""P1 fault checks that require live Postgres/Redis workers and Docker."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx


BACKEND_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ARTIFACTS = BACKEND_ROOT / "p1-artifacts"


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, text=True, **kwargs)


def docker_id(image_prefix: str) -> str:
    result = run(
        ["docker", "ps", "--format", "{{.ID}} {{.Image}}"],
        capture_output=True,
    )
    for line in result.stdout.splitlines():
        container_id, image = line.split(" ", 1)
        if image.startswith(image_prefix):
            return container_id
    raise SystemExit(f"no running container for {image_prefix}")


def wait_http(urls: list[str], timeout: float = 60) -> None:
    cmd = [sys.executable, str(BACKEND_ROOT / "scripts" / "wait_http.py"), "--timeout", str(timeout), *urls]
    run(cmd)


def start_worker(port: int, log_path: Path, pid_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(log_path, "ab")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=BACKEND_ROOT,
        stdout=handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    pid_path.write_text(str(proc.pid), encoding="utf-8")


def stop_pid(pid_path: Path) -> None:
    if not pid_path.exists():
        return
    pid = pid_path.read_text(encoding="utf-8").strip()
    if pid:
        subprocess.run(["kill", pid], check=False)


def login(base_url: str) -> str:
    response = httpx.post(
        f"{base_url}/api/auth/login",
        json={"username": "dispatcher", "password": "123456"},
        timeout=30,
    )
    response.raise_for_status()
    body = response.json()
    if body.get("code") != 0:
        raise SystemExit(f"login failed: {body}")
    return body["data"]["access_token"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", default=str(DEFAULT_ARTIFACTS))
    parser.add_argument("--worker-a-url", default="http://127.0.0.1:18001")
    parser.add_argument("--worker-b-url", default="http://127.0.0.1:18002")
    args = parser.parse_args()
    artifacts = Path(args.artifacts)
    artifacts.mkdir(parents=True, exist_ok=True)

    summary = artifacts / "fault-summary.txt"
    lines = [
        "fault_checks=redis-pause,worker-restart,pg-schema-dump",
        "data=synthetic",
    ]

    redis_id = docker_id("redis:7-alpine")
    postgres_id = docker_id("postgres:16-alpine")
    run(["docker", "pause", redis_id])
    try:
        health = httpx.get(f"{args.worker_a_url}/api/health", timeout=10)
        health.raise_for_status()
        redis_status = (health.json().get("data") or {}).get("redis")
        token = login(args.worker_a_url)
        me = httpx.get(
            f"{args.worker_b_url}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        if me.status_code != 200 or me.json().get("code") != 0:
            raise SystemExit(f"login/me failed while redis paused: {me.text[:300]}")
        lines.append(f"redis_paused_health={redis_status}")
        lines.append("db_login_during_redis_pause=ok")
    finally:
        run(["docker", "unpause", redis_id])
        time.sleep(2)

    stop_pid(artifacts / "worker-a.pid")
    stop_pid(artifacts / "worker-b.pid")
    time.sleep(1)
    start_worker(18001, artifacts / "worker-a.log", artifacts / "worker-a.pid")
    start_worker(18002, artifacts / "worker-b.log", artifacts / "worker-b.pid")
    wait_http([f"{args.worker_a_url}/api/health", f"{args.worker_b_url}/api/health"])
    token = login(args.worker_a_url)
    orders = httpx.get(
        f"{args.worker_b_url}/api/orders",
        params={"page": 1, "page_size": 20},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    orders.raise_for_status()
    total = int((orders.json().get("data") or {}).get("total") or 0)
    if total < 1:
        raise SystemExit(f"orders missing after worker restart: {orders.text[:300]}")
    lines.append(f"orders_after_restart={total}")

    dump = artifacts / "pg-schema.sql"
    with dump.open("w", encoding="utf-8") as handle:
        run(
            [
                "docker",
                "exec",
                postgres_id,
                "pg_dump",
                "-U",
                "logistics",
                "-d",
                "logistics",
                "--schema-only",
            ],
            stdout=handle,
        )
    schema = dump.read_text(encoding="utf-8")
    if "alembic_version" not in schema or len(schema) < 100:
        raise SystemExit("pg_dump schema output looks empty")
    lines.append(f"pg_dump_schema_bytes={dump.stat().st_size}")
    summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
