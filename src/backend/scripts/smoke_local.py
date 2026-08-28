"""02A/02B seed-db HTTP smoke.

02A one-click (temp SQLite + uvicorn, no Docker)::

    python scripts/smoke_local.py --self-host

02B / already-running server::

    python scripts/smoke_local.py --base-url http://127.0.0.1:8000

Never points DATABASE_URL at src/backend/data/logistics.db.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


BACKEND_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_ROOT.parent.parent
DEFAULT_DEV_DB = (BACKEND_ROOT / "data" / "logistics.db").resolve()
DEFAULT_BASE_URL = "http://127.0.0.1:18000"
DEFAULT_PORT = 18000
DEFAULT_PASSWORD = "123456"
FORBIDDEN_ORDER_STATUS = "pending"
ROLES = ("admin", "dispatcher", "manager")


class SmokeFailed(Exception):
    """A smoke assertion failed."""


@dataclass
class HttpResult:
    status: int
    body: Any
    raw: str


@dataclass
class SmokeContext:
    base_url: str
    password: str
    tokens: dict[str, str] = field(default_factory=dict)
    schedule_code: str | None = None
    batch_code: str | None = None
    order_codes: list[str] = field(default_factory=list)
    deliver_package: str | None = None
    confirm_package: str | None = None
    notes: list[str] = field(default_factory=list)


def log(message: str) -> None:
    print(message, flush=True)


def sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.resolve().as_posix()}"


def parse_sqlite_path(database_url: str) -> Path | None:
    if not database_url.startswith("sqlite:///"):
        return None
    raw = database_url[len("sqlite:///"):]
    if raw.startswith(":memory:") or "mode=memory" in raw:
        return None
    return Path(raw).resolve()


def file_signature(path: Path) -> tuple[int, int] | None:
    if not path.exists():
        return None
    stat = path.stat()
    return (stat.st_mtime_ns, stat.st_size)


def assert_not_dev_db(path: Path, label: str) -> None:
    if path.resolve() == DEFAULT_DEV_DB:
        raise SmokeFailed(f"{label} refuses to use the development db: {DEFAULT_DEV_DB}")


def request_json(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: Any = None,
    timeout: float = 60,
) -> HttpResult:
    headers = {"Accept": "application/json"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            parsed = json.loads(raw) if raw else None
            return HttpResult(status=resp.status, body=parsed, raw=raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            parsed = None
        return HttpResult(status=exc.code, body=parsed, raw=raw)
    except urllib.error.URLError as exc:
        raise SmokeFailed(f"{method} {url} connection failed: {exc}") from exc


def api_url(base_url: str, path: str, params: dict[str, Any] | None = None) -> str:
    url = base_url.rstrip("/") + "/" + path.lstrip("/")
    if params:
        query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        url = f"{url}?{query}"
    return url


def require_json(result: HttpResult, step: str) -> dict[str, Any]:
    if result.status >= 500:
        raise SmokeFailed(f"{step}: unexpected {result.status}: {result.raw[:500]}")
    if not isinstance(result.body, dict):
        raise SmokeFailed(f"{step}: response is not JSON object: {result.raw[:500]}")
    return result.body


def require_ok(result: HttpResult, step: str) -> dict[str, Any]:
    body = require_json(result, step)
    if result.status != 200:
        raise SmokeFailed(f"{step}: HTTP {result.status}: {result.raw[:500]}")
    if body.get("code") not in (0, None):
        raise SmokeFailed(f"{step}: business code={body.get('code')} message={body.get('message')}")
    return body


def record_degraded(ctx: SmokeContext, step: str, body: dict[str, Any]) -> None:
    meta = body.get("meta") if isinstance(body.get("meta"), dict) else {}
    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    reasons = []
    if meta.get("degraded"):
        reasons.append(str(meta.get("degraded_reason") or "meta.degraded"))
    ai_service = data.get("ai_service")
    if ai_service and ai_service != "available":
        reasons.append(f"ai_service={ai_service}")
    if reasons:
        note = f"{step}: degraded ({', '.join(reasons)})"
        ctx.notes.append(note)
        log(f"    {note}")


def list_items(
    ctx: SmokeContext,
    path: str,
    token: str,
    *,
    page_size: int = 100,
    extra: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], int, dict[str, Any]]:
    items: list[dict[str, Any]] = []
    page = 1
    last_body: dict[str, Any] = {}
    total = 0
    while True:
        params = {"page": page, "page_size": page_size}
        if extra:
            params.update(extra)
        result = request_json("GET", api_url(ctx.base_url, path, params), token=token, timeout=60)
        body = require_ok(result, f"GET {path} page={page}")
        last_body = body
        data = body.get("data") or {}
        page_items = data.get("items") or []
        total = int(data.get("total") or 0)
        items.extend(page_items)
        if not page_items or len(items) >= total:
            break
        page += 1
        if page > 50:
            raise SmokeFailed(f"GET {path} paginated too many pages")
    return items, total, last_body


def count_pending_orders_sql(db_path: Path) -> int:
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE status = ?",
            (FORBIDDEN_ORDER_STATUS,),
        )
        return int(cur.fetchone()[0])
    finally:
        conn.close()


def count_table(db_path: Path, table: str) -> int:
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.execute(f"SELECT COUNT(*) FROM {table}")
        return int(cur.fetchone()[0])
    finally:
        conn.close()


def run_http_smoke(ctx: SmokeContext, *, persist_only: bool = False) -> None:
    dispatcher = ctx.tokens.get("dispatcher")
    if persist_only:
        _step_health(ctx)
        _step_login_roles(ctx)
        _step_reload_entities(ctx)
        return

    _step_health(ctx)
    _step_login_roles(ctx)
    dispatcher = ctx.tokens["dispatcher"]
    _step_seed_inspection(ctx, dispatcher)
    _step_schedule_draft(ctx, dispatcher)
    _step_confirm_pack(ctx, dispatcher)
    _step_node_dispatch(ctx, dispatcher)
    _step_routes(ctx, dispatcher)
    _step_deliver_and_arrival(ctx, dispatcher)


def _step_health(ctx: SmokeContext) -> None:
    log("[01] GET /api/health")
    result = request_json("GET", api_url(ctx.base_url, "/api/health"), timeout=15)
    body = require_ok(result, "GET /api/health")
    data = body.get("data") or {}
    if data.get("status") != "ok":
        raise SmokeFailed(f"health status is not ok: {data}")
    record_degraded(ctx, "health", body)
    log("    OK")


def _step_login_roles(ctx: SmokeContext) -> None:
    log("[02] POST /api/auth/login + GET /api/auth/me")
    for role in ROLES:
        result = request_json(
            "POST",
            api_url(ctx.base_url, "/api/auth/login"),
            body={"username": role, "password": ctx.password},
            timeout=30,
        )
        body = require_ok(result, f"login {role}")
        data = body.get("data") or {}
        token = data.get("access_token")
        if not token:
            raise SmokeFailed(f"login {role}: missing access_token")
        if data.get("role") != role:
            raise SmokeFailed(f"login {role}: role={data.get('role')}")
        ctx.tokens[role] = token
        me = request_json(
            "GET",
            api_url(ctx.base_url, "/api/auth/me"),
            token=token,
            timeout=15,
        )
        me_body = require_ok(me, f"GET /api/auth/me {role}")
        me_data = me_body.get("data") or {}
        if me_data.get("username") != role or me_data.get("role") != role:
            raise SmokeFailed(f"/me {role} mismatch: {me_data}")
        log(f"    {role} OK")


def _step_seed_inspection(ctx: SmokeContext, token: str) -> None:
    log("[03] seed inspection")
    orders, order_total, _ = list_items(ctx, "/api/orders", token)
    goods, goods_total, _ = list_items(ctx, "/api/goods", token)
    packages, package_total, _ = list_items(ctx, "/api/packages", token)
    vehicles, vehicle_total, _ = list_items(ctx, "/api/vehicles", token)
    nodes, node_total, _ = list_items(ctx, "/api/nodes", token)

    pending = [item for item in orders if item.get("status") == FORBIDDEN_ORDER_STATUS]
    if pending:
        codes = ", ".join(str(item.get("order_code")) for item in pending[:8])
        raise SmokeFailed(f"illegal order status pending count={len(pending)} sample={codes}")
    if order_total < 1 or goods_total < 1 or vehicle_total < 1 or node_total < 1:
        raise SmokeFailed(
            "seed entities missing: "
            f"orders={order_total} goods={goods_total} packages={package_total} "
            f"vehicles={vehicle_total} nodes={node_total}"
        )

    ctx.order_codes = [
        item["order_code"]
        for item in orders
        if item.get("status") == "unassigned" and item.get("order_code")
    ]
    log(
        f"    orders={order_total} goods={goods_total} packages={package_total} "
        f"vehicles={vehicle_total} nodes={node_total} unassigned={len(ctx.order_codes)} pending=0"
    )


def _step_schedule_draft(ctx: SmokeContext, token: str) -> None:
    log("[04] F007 POST /api/schedule/global")
    if len(ctx.order_codes) < 3:
        raise SmokeFailed(f"need at least 3 unassigned orders, got {len(ctx.order_codes)}")
    selected = ctx.order_codes[:8]
    result = request_json(
        "POST",
        api_url(ctx.base_url, "/api/schedule/global"),
        token=token,
        body={"algorithm": "traditional", "preview": True, "order_codes": selected},
        timeout=180,
    )
    body = require_ok(result, "POST /api/schedule/global")
    record_degraded(ctx, "schedule/global", body)
    data = body.get("data") or {}
    code = data.get("schedule_code")
    if not code:
        raise SmokeFailed(f"schedule missing schedule_code: {data}")
    if data.get("status") != "draft":
        raise SmokeFailed(f"schedule status is not draft: {data.get('status')}")
    ctx.schedule_code = code
    ctx.order_codes = list(data.get("order_codes") or selected)
    log(f"    schedule_code={code} status=draft orders={len(ctx.order_codes)}")


def _step_confirm_pack(ctx: SmokeContext, token: str) -> None:
    log("[05] F021 POST /api/schedule/confirm/{schedule_code}")
    if not ctx.schedule_code:
        raise SmokeFailed("confirm: missing schedule_code")
    result = request_json(
        "POST",
        api_url(ctx.base_url, f"/api/schedule/confirm/{ctx.schedule_code}"),
        token=token,
        timeout=180,
    )
    body = require_ok(result, "POST /api/schedule/confirm")
    data = body.get("data") or {}
    if data.get("status") != "active":
        raise SmokeFailed(f"confirm status is not active: {data.get('status')}")
    if int(data.get("package_count") or 0) < 1:
        raise SmokeFailed(f"confirm produced no packages: {data}")
    packages, package_total, _ = list_items(ctx, "/api/packages", token)
    if package_total < 1:
        raise SmokeFailed("packages still empty after confirm")
    log(f"    status=active package_count={data.get('package_count')} listed={len(packages)}")


def _step_node_dispatch(ctx: SmokeContext, token: str) -> None:
    log("[06] F005 POST /api/schedule/node-dispatch")
    result = request_json(
        "POST",
        api_url(ctx.base_url, "/api/schedule/node-dispatch"),
        token=token,
        body={"schedule_code": ctx.schedule_code, "demo_mode": False},
        timeout=180,
    )
    body = require_ok(result, "POST /api/schedule/node-dispatch")
    record_degraded(ctx, "node-dispatch", body)
    data = body.get("data") or {}
    batch = data.get("batch_code")
    if not batch:
        raise SmokeFailed(f"node-dispatch missing batch_code: {data}")
    ctx.batch_code = batch
    detail = request_json(
        "GET",
        api_url(ctx.base_url, f"/api/schedule/batches/{batch}"),
        token=token,
        timeout=60,
    )
    detail_body = require_ok(detail, "GET /api/schedule/batches/{batch}")
    dispatches = (detail_body.get("data") or {}).get("dispatches") or []
    in_transit: list[str] = []
    for dispatch in dispatches:
        for task in dispatch.get("tasks") or []:
            for pkg in task.get("package_details") or []:
                code = pkg.get("package_code")
                if code and code not in in_transit:
                    in_transit.append(code)
    if not in_transit:
        # fallback: list packages with in_transit
        packages, _, _ = list_items(ctx, "/api/packages", token, extra={"status": "in_transit"})
        in_transit = [item.get("package_code") for item in packages if item.get("package_code")]
    if not in_transit:
        raise SmokeFailed("no in_transit packages after node-dispatch")
    ctx.deliver_package = in_transit[0]
    ctx.confirm_package = in_transit[1] if len(in_transit) > 1 else None
    log(f"    batch={batch} in_transit_packages={len(in_transit)}")


def _step_routes(ctx: SmokeContext, token: str) -> None:
    log("[07] F006 POST /api/routes/plan + GET /api/routes")
    result = request_json(
        "POST",
        api_url(ctx.base_url, "/api/routes/plan"),
        token=token,
        body={"batch_code": ctx.batch_code},
        timeout=180,
    )
    body = require_ok(result, "POST /api/routes/plan")
    record_degraded(ctx, "routes/plan", body)
    listed = request_json(
        "GET",
        api_url(
            ctx.base_url,
            "/api/routes",
            {"batch_code": ctx.batch_code, "page": 1, "page_size": 20},
        ),
        token=token,
        timeout=60,
    )
    listed_body = require_ok(listed, "GET /api/routes")
    data = listed_body.get("data") or {}
    for field_name in ("items", "total", "page", "page_size"):
        if field_name not in data:
            raise SmokeFailed(f"GET /api/routes missing pagination field {field_name}")
    if int(data.get("total") or 0) < 1:
        raise SmokeFailed("GET /api/routes returned no routes")
    log(f"    routes total={data.get('total')} page={data.get('page')} page_size={data.get('page_size')}")


def _step_deliver_and_arrival(ctx: SmokeContext, token: str) -> None:
    log("[08] POST /api/simulation/deliver + confirm-arrival")
    if not ctx.deliver_package:
        raise SmokeFailed("missing package for simulation/deliver")

    deliver = request_json(
        "POST",
        api_url(ctx.base_url, "/api/simulation/deliver"),
        token=token,
        body={"package_code": ctx.deliver_package},
        timeout=120,
    )
    deliver_body = require_ok(deliver, "POST /api/simulation/deliver")
    delivered = (deliver_body.get("data") or {}).get("delivered_package_codes") or []
    if ctx.deliver_package not in delivered:
        raise SmokeFailed(f"deliver did not include {ctx.deliver_package}: {deliver_body.get('data')}")

    manager_denied = request_json(
        "POST",
        api_url(ctx.base_url, "/api/simulation/confirm-arrival"),
        token=ctx.tokens["manager"],
        body={
            "schedule_code": ctx.schedule_code,
            "package_code": ctx.confirm_package or ctx.deliver_package,
            "is_normal": True,
        },
        timeout=30,
    )
    if manager_denied.status != 403:
        raise SmokeFailed(
            f"manager confirm-arrival should be 403, got {manager_denied.status}: {manager_denied.raw[:300]}"
        )
    log("    manager confirm-arrival 403 OK")

    confirm_package = ctx.confirm_package
    if not confirm_package:
        packages, _, _ = list_items(ctx, "/api/packages", token, extra={"status": "in_transit"})
        leftover = [
            item.get("package_code")
            for item in packages
            if item.get("package_code") and item.get("package_code") != ctx.deliver_package
        ]
        if leftover:
            confirm_package = leftover[0]
            ctx.confirm_package = confirm_package
    if not confirm_package:
        raise SmokeFailed(
            "need a second in_transit package for confirm-arrival; "
            "deliver and confirm-arrival cannot share one package "
            "(delivered -> delivered is not a legal transition)"
        )

    confirm = request_json(
        "POST",
        api_url(ctx.base_url, "/api/simulation/confirm-arrival"),
        token=token,
        body={
            "schedule_code": ctx.schedule_code,
            "package_code": confirm_package,
            "is_normal": True,
        },
        timeout=120,
    )
    confirm_body = require_ok(confirm, "POST /api/simulation/confirm-arrival")
    confirm_data = confirm_body.get("data") or {}
    if confirm_data.get("status") not in {"delivered", "exception"} and confirm_data.get("package_code") != confirm_package:
        raise SmokeFailed(f"confirm-arrival unexpected payload: {confirm_data}")
    log(f"    deliver={ctx.deliver_package} confirm={confirm_package} status={confirm_data.get('status')}")


def _step_reload_entities(ctx: SmokeContext) -> None:
    log("[09] restart persistence check")
    token = ctx.tokens["dispatcher"]
    if ctx.schedule_code:
        result = request_json(
            "GET",
            api_url(ctx.base_url, f"/api/schedule/global/{ctx.schedule_code}"),
            token=token,
            timeout=60,
        )
        body = require_ok(result, "GET /api/schedule/global/{code} after restart")
        data = body.get("data") or {}
        if data.get("schedule_code") != ctx.schedule_code:
            raise SmokeFailed(f"schedule {ctx.schedule_code} missing after restart: {data}")
        packages = data.get("packages") or []
        if not packages and int(data.get("package_count") or 0) < 1:
            raise SmokeFailed(f"schedule {ctx.schedule_code} has no packages after restart")
        listed = request_json(
            "GET",
            api_url(ctx.base_url, "/api/schedule/global", {"status": "active", "page": 1, "page_size": 20}),
            token=token,
            timeout=30,
        )
        listed_body = require_ok(listed, "GET /api/schedule/global?status=active after restart")
        codes = [item.get("schedule_code") for item in ((listed_body.get("data") or {}).get("items") or [])]
        if ctx.schedule_code not in codes:
            raise SmokeFailed(f"active schedule list after restart missing {ctx.schedule_code}: {codes}")
        log(f"    schedule {ctx.schedule_code} persisted packages={len(packages) or data.get('package_count')}")
    if ctx.deliver_package:
        result = request_json(
            "GET",
            api_url(ctx.base_url, f"/api/packages/{ctx.deliver_package}"),
            token=token,
            timeout=30,
        )
        body = require_ok(result, "GET delivered package after restart")
        status = (body.get("data") or {}).get("status")
        log(f"    package {ctx.deliver_package} status={status}")
    orders, _, _ = list_items(ctx, "/api/orders", token)
    pending = [item for item in orders if item.get("status") == FORBIDDEN_ORDER_STATUS]
    if pending:
        raise SmokeFailed(f"pending orders reappeared after restart: {len(pending)}")
    log("    pending=0 after restart")


def run_cmd(args: list[str], env: dict[str, str], cwd: Path) -> None:
    log(f"    $ {' '.join(args)}")
    completed = subprocess.run(args, cwd=str(cwd), env=env, check=False, text=True)
    if completed.returncode != 0:
        raise SmokeFailed(f"command failed ({completed.returncode}): {' '.join(args)}")


def wait_health(base_url: str, timeout: float = 60) -> None:
    deadline = time.time() + timeout
    last_error = "not started"
    while time.time() < deadline:
        try:
            result = request_json("GET", api_url(base_url, "/api/health"), timeout=5)
            if result.status == 200 and isinstance(result.body, dict) and result.body.get("code") in (0, None):
                return
            last_error = f"HTTP {result.status} {result.raw[:200]}"
        except SmokeFailed as exc:
            last_error = str(exc)
        time.sleep(0.5)
    raise SmokeFailed(f"server did not become healthy: {last_error}")


def start_uvicorn(env: dict[str, str], port: int, log_path: Path) -> subprocess.Popen[bytes]:
    args = [
        sys.executable,
        "-m",
        "uvicorn",
        "main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]
    log(f"    start uvicorn :{port}")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(log_path, "ab")
    return subprocess.Popen(
        args,
        cwd=str(BACKEND_ROOT),
        env=env,
        stdout=handle,
        stderr=subprocess.STDOUT,
    )


def stop_uvicorn(proc: subprocess.Popen[bytes] | None) -> None:
    if proc is None:
        return
    handle = proc.stdout
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
    if handle:
        try:
            handle.close()
        except OSError:
            pass


def bootstrap_database(env: dict[str, str], db_path: Path) -> None:
    log("[00] alembic upgrade + dual init")
    run_cmd(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            str(BACKEND_ROOT / "alembic.ini"),
            "upgrade",
            "head",
        ],
        env,
        BACKEND_ROOT,
    )
    for round_no in (1, 2):
        log(f"    init round {round_no}")
        run_cmd([sys.executable, "scripts/init_users.py"], env, BACKEND_ROOT)
        run_cmd([sys.executable, "scripts/init_demo_data.py"], env, BACKEND_ROOT)
    users = count_table(db_path, "users")
    orders = count_table(db_path, "orders")
    pending = count_pending_orders_sql(db_path)
    if users < 3:
        raise SmokeFailed(f"expected >=3 users after dual init, got {users}")
    if orders != 100:
        raise SmokeFailed(f"expected 100 orders after dual init, got {orders}")
    if pending != 0:
        raise SmokeFailed(f"expected 0 pending orders after dual init, got {pending}")
    log(f"    users={users} orders={orders} pending={pending}")


def run_self_host(args: argparse.Namespace) -> int:
    smoke_root = Path(args.temp_dir) if args.temp_dir else Path(os.environ.get("TEMP", str(REPO_ROOT))) / "logistics-02a"
    smoke_root.mkdir(parents=True, exist_ok=True)
    db_path = (smoke_root / "logistics.db").resolve()
    assert_not_dev_db(db_path, "--self-host")
    if db_path.exists() and not args.reuse_temp:
        db_path.unlink()

    dev_before = file_signature(DEFAULT_DEV_DB)
    env = os.environ.copy()
    env["ENV"] = "dev"
    env["REDIS_ENABLED"] = "false"
    env["DATABASE_URL"] = sqlite_url(db_path)
    env["REQUEST_TIMEOUT_SECONDS"] = "300"
    env["IDEMPOTENCY_PROCESSING_LEASE_SECONDS"] = "360"
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    # Keep Windows from inheriting a user site that shadows project deps.
    env["PYTHONPATH"] = str(BACKEND_ROOT)

    base_url = f"http://127.0.0.1:{args.port}"
    ctx = SmokeContext(base_url=base_url, password=args.password)
    server: subprocess.Popen[bytes] | None = None
    try:
        bootstrap_database(env, db_path)
        server = start_uvicorn(env, args.port, smoke_root / "uvicorn.1.log")
        wait_health(base_url, timeout=90)
        if server.poll() is not None:
            stop_uvicorn(server)
            raise SmokeFailed("uvicorn exited early; see uvicorn.1.log")
        run_http_smoke(ctx)
        stop_uvicorn(server)
        server = None
        if not db_path.exists():
            raise SmokeFailed("temp sqlite disappeared after first uvicorn stop")
        server = start_uvicorn(env, args.port, smoke_root / "uvicorn.2.log")
        wait_health(base_url, timeout=90)
        run_http_smoke(ctx, persist_only=True)
        log("ALL_02A_SMOKE_CHECKS_PASS")
        if ctx.notes:
            log("notes:")
            for note in ctx.notes:
                log(f"  - {note}")
        return 0
    finally:
        stop_uvicorn(server)
        dev_after = file_signature(DEFAULT_DEV_DB)
        if dev_before != dev_after:
            raise SmokeFailed(
                f"development db was rewritten: before={dev_before} after={dev_after} path={DEFAULT_DEV_DB}"
            )
        log(f"dev db unchanged: {DEFAULT_DEV_DB}")
        log(f"temp db: {db_path}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed-db HTTP smoke for 02A/02B")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Server origin, no trailing path")
    parser.add_argument("--db", default=None, help="Optional sqlite URL/path for pending-order SQL check")
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    parser.add_argument("--self-host", action="store_true", help="02A: temp sqlite + uvicorn + restart")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--temp-dir", default=None)
    parser.add_argument("--reuse-temp", action="store_true")
    parser.add_argument("--keep-logs", action="store_true")
    return parser.parse_args(argv)


def optional_sql_check(db_value: str | None) -> None:
    if not db_value:
        return
    db_path = parse_sqlite_path(db_value) if db_value.startswith("sqlite:") else Path(db_value).resolve()
    if db_path is None:
        log(f"skip SQL pending check for non-file db: {db_value}")
        return
    if not db_path.exists():
        raise SmokeFailed(f"--db file does not exist: {db_path}")
    pending = count_pending_orders_sql(db_path)
    if pending != 0:
        raise SmokeFailed(f"SQL pending orders={pending} in {db_path}")
    log(f"SQL pending=0 in {db_path}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    started = datetime.now().isoformat(timespec="seconds")
    log(f"smoke_local start {started} python={sys.version.split()[0]} cwd={Path.cwd()}")
    try:
        if args.self_host:
            return run_self_host(args)
        ctx = SmokeContext(base_url=args.base_url, password=args.password)
        optional_sql_check(args.db)
        run_http_smoke(ctx)
        log("ALL_02A_SMOKE_CHECKS_PASS")
        if ctx.notes:
            log("notes:")
            for note in ctx.notes:
                log(f"  - {note}")
        return 0
    except SmokeFailed as exc:
        log(f"FAIL {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
