"""P1 fault checks that require live Postgres/Redis workers and Docker."""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.database_url import engine_create_kwargs, resolve_database_url
from config.settings import settings
from models.node import Node
from models.outbox_event import OutboxEvent
from models.user import User
from services.auth_service import get_password_hash
from services.outbox_service import claim_outbox_batch, enqueue_outbox, finalize_claimed_event


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


def start_outbox(log_path: Path, pid_path: Path, worker_id: str, lease_seconds: int) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(log_path, "ab")
    proc = subprocess.Popen(
        [
            sys.executable,
            str(BACKEND_ROOT / "scripts" / "outbox_worker.py"),
            "--worker-id",
            worker_id,
            "--lease-seconds",
            str(lease_seconds),
            "--poll-seconds",
            "0.5",
        ],
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


def login_attempt(base_url: str, username: str, password: str, timeout: float = 15) -> httpx.Response:
    return httpx.post(
        f"{base_url}/api/auth/login",
        json={"username": username, "password": password},
        timeout=timeout,
    )


def seed_user(factory, username: str, password: str) -> None:
    db = factory()
    try:
        db.add(
            User(
                username=username,
                password_hash=get_password_hash(password),
                role="dispatcher",
                display_name=username,
                is_active=True,
            )
        )
        db.commit()
    finally:
        db.close()


def login(base_url: str, username: str = "admin", password: str = "123456") -> str:
    response = httpx.post(
        f"{base_url}/api/auth/login",
        json={"username": username, "password": password},
        timeout=30,
    )
    response.raise_for_status()
    body = response.json()
    if body.get("code") != 0:
        raise SystemExit(f"login failed: {body}")
    return body["data"]["access_token"]


def session_factory(database_url: str):
    url = resolve_database_url(database_url)
    engine = create_engine(url, **engine_create_kwargs(url))
    return engine, sessionmaker(autocommit=False, autoflush=False, bind=engine)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", default=str(DEFAULT_ARTIFACTS))
    parser.add_argument("--worker-a-url", default="http://127.0.0.1:18001")
    parser.add_argument("--worker-b-url", default="http://127.0.0.1:18002")
    parser.add_argument(
        "--database-url",
        default="",
    )
    args = parser.parse_args()
    artifacts = Path(args.artifacts)
    artifacts.mkdir(parents=True, exist_ok=True)
    database_url = args.database_url or __import__("os").environ.get("DATABASE_URL", "")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")

    summary = artifacts / "fault-summary.txt"
    lines = [
        "fault_checks=redis-pause-recover,login-rate-limit,worker-restart-idempotency,outbox-lease-reclaim,pg-pause-recover,pg-schema-dump",
        "data=synthetic",
    ]

    redis_id = docker_id("redis:7-alpine")
    postgres_id = docker_id("postgres:16-alpine")
    engine, factory = session_factory(database_url)

    run(["docker", "pause", redis_id])
    try:
        health = httpx.get(f"{args.worker_a_url}/api/health", timeout=10)
        health.raise_for_status()
        body = health.json()
        redis_status = (body.get("data") or {}).get("redis")
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
        time.sleep(3)

    recovered = None
    for _ in range(10):
        health = httpx.get(f"{args.worker_a_url}/api/health", timeout=10)
        recovered = (health.json().get("data") or {}).get("redis")
        if recovered == "available":
            break
        time.sleep(1)
    lines.append(f"redis_recovered_health={recovered}")
    if recovered != "available":
        raise SystemExit(f"redis did not recover: {recovered}")

    rl_suffix = uuid4().hex
    rl_user = f"p1-rl-{rl_suffix}"
    rl_other = f"p1-rl-other-{rl_suffix}"
    rl_probe = f"p1-rl-probe-{rl_suffix}"
    rl_password = f"P1-{rl_suffix}"
    seed_user(factory, rl_user, rl_password)
    seed_user(factory, rl_other, rl_password)
    seed_user(factory, rl_probe, rl_password)
    attempts = int(settings.LOGIN_RATE_LIMIT_ATTEMPTS)
    for index in range(attempts - 1):
        base = args.worker_a_url if index % 2 == 0 else args.worker_b_url
        response = login_attempt(base, rl_user, "wrong")
        body = response.json()
        if response.status_code != 200 or body.get("code") != 40100:
            raise SystemExit(f"shared fail login unexpected: {response.text[:300]}")
        if (body.get("meta") or {}).get("degraded"):
            raise SystemExit("login rate limit degraded before redis pause")

    run(["docker", "pause", redis_id])
    try:
        paused = login_attempt(args.worker_a_url, rl_user, "wrong", timeout=10)
        paused_body = paused.json()
        paused_meta = paused_body.get("meta") or {}
        if paused.status_code != 200 or paused_body.get("code") != 40100:
            raise SystemExit(f"paused login unexpected: {paused.text[:300]}")
        if paused_meta.get("degraded") is not True or paused_meta.get("degraded_reason") != "redis":
            raise SystemExit(f"paused login not degraded: {paused_meta}")
        lines.append("login_rate_limit_redis_paused_degraded=ok")
    finally:
        run(["docker", "unpause", redis_id])
        time.sleep(3)

    limiter_recovered = False
    for _ in range(10):
        probe = login_attempt(args.worker_a_url, rl_probe, "wrong")
        probe_body = probe.json()
        if (
            probe.status_code == 200
            and probe_body.get("code") == 40100
            and (probe_body.get("meta") or {}).get("degraded") is False
        ):
            limiter_recovered = True
            break
        time.sleep(1)
    if not limiter_recovered:
        raise SystemExit("login limiter did not recover shared redis")
    lines.append("login_rate_limit_redis_recovered=ok")

    threshold = login_attempt(args.worker_b_url, rl_user, "wrong")
    threshold_body = threshold.json()
    if threshold.status_code != 200 or threshold_body.get("code") != 40100:
        raise SystemExit(f"recover fail before lock unexpected: {threshold.text[:300]}")
    locked = login_attempt(args.worker_a_url, rl_user, rl_password)
    locked_body = locked.json()
    if locked.status_code != 429 or locked_body.get("code") != 42900:
        raise SystemExit(f"shared limiter did not lock after recover: {locked.text[:300]}")
    other_ok = login_attempt(args.worker_b_url, rl_other, rl_password)
    other_body = other_ok.json()
    if other_ok.status_code != 200 or other_body.get("code") != 0:
        raise SystemExit(f"other user blocked by shared limiter: {other_ok.text[:300]}")
    lines.append("cross_worker_login_rate_limit=ok")

    token = login(args.worker_a_url)
    suffix = uuid4().hex[:16]
    node_code = f"P1F{suffix.upper()}"
    payload = {
        "node_code": node_code,
        "name": "P1 fault storage center",
        "location": "synthetic-ci",
        "latitude": 30.5,
        "longitude": 114.3,
        "capacity": 500.0,
        "inventory": 0,
    }
    write_headers = {
        "Authorization": f"Bearer {token}",
        "X-Idempotency-Key": f"p1-fault-{suffix}",
    }
    first = httpx.post(
        f"{args.worker_a_url}/api/nodes/storage-centers",
        json=payload,
        headers=write_headers,
        timeout=30,
    )
    if first.status_code != 200 or first.json().get("code") != 0:
        raise SystemExit(f"first write failed: {first.text[:300]}")

    stop_pid(artifacts / "worker-a.pid")
    time.sleep(1)
    start_worker(18001, artifacts / "worker-a.log", artifacts / "worker-a.pid")
    wait_http([f"{args.worker_a_url}/api/health"])
    replay = httpx.post(
        f"{args.worker_b_url}/api/nodes/storage-centers",
        json=payload,
        headers=write_headers,
        timeout=30,
    )
    if replay.status_code != 200 or replay.json().get("code") != 0:
        raise SystemExit(f"replay failed: {replay.text[:300]}")
    if replay.json()["data"] != first.json()["data"]:
        raise SystemExit("idempotent replay mismatch after worker restart")
    db = factory()
    try:
        node_count = db.query(Node).filter(Node.node_code == node_code).count()
        if node_count != 1:
            raise SystemExit(f"duplicate node after replay: {node_count}")
        lines.append("worker_restart_idempotent_replay=ok")
    finally:
        db.close()

    db = factory()
    try:
        event = enqueue_outbox(
            db,
            dedup_key=f"p1-fault-outbox-{suffix}",
            event_type="p1.fault",
            payload={"scenario": "lease-reclaim"},
        )
        db.commit()
        event_id = event.id
        claimed = claim_outbox_batch(
            db, worker_id="killed-worker", limit=1, lease_seconds=2
        )
        if not claimed:
            raise SystemExit("failed to claim outbox event")
        old_token = claimed[0].claim_token
        stop_pid(artifacts / "outbox-worker.pid")
        time.sleep(3)
        reclaimed = claim_outbox_batch(
            db, worker_id="replacement-worker", limit=1, lease_seconds=30
        )
        if not reclaimed or reclaimed[0].claim_token == old_token:
            raise SystemExit("outbox lease was not reclaimed")
        stale = finalize_claimed_event(
            db,
            event_id=event_id,
            claim_token=old_token,
            worker_id="killed-worker",
            ok=True,
            error="",
            permanent_failure=False,
            max_retries=3,
            retry_delay_seconds=1,
        )
        if stale != "stale":
            raise SystemExit(f"stale token completed event: {stale}")
        delivered = finalize_claimed_event(
            db,
            event_id=event_id,
            claim_token=reclaimed[0].claim_token,
            worker_id="replacement-worker",
            ok=True,
            error="",
            permanent_failure=False,
            max_retries=3,
            retry_delay_seconds=1,
        )
        if delivered != "delivered":
            raise SystemExit(f"replacement worker failed to complete: {delivered}")
        lines.append("outbox_stale_token_blocked=ok")
        lines.append("outbox_lease_reclaimed=ok")
    finally:
        db.close()
        start_outbox(
            artifacts / "outbox-worker.log",
            artifacts / "outbox-worker.pid",
            "gha-p1-outbox",
            60,
        )

    run(["docker", "pause", postgres_id])
    try:
        try:
            failed = httpx.get(
                f"{args.worker_a_url}/api/orders",
                params={"page": 1, "page_size": 5},
                headers={"Authorization": f"Bearer {token}"},
                timeout=3,
            )
            failed_code = None
            try:
                failed_code = failed.json().get("code")
            except Exception:
                failed_code = failed.status_code
            lines.append(f"postgres_paused_orders_code={failed_code}")
            if failed.status_code == 200 and failed_code == 0:
                raise SystemExit("orders succeeded while postgres paused")
        except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as exc:
            lines.append(f"postgres_paused_orders_error={type(exc).__name__}")
    finally:
        run(["docker", "unpause", postgres_id])
        time.sleep(5)

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
        raise SystemExit(f"orders missing after postgres recover: {orders.text[:300]}")
    lines.append(f"orders_after_postgres_recover={total}")

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
    engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
