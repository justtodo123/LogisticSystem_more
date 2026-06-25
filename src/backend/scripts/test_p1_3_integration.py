"""P1-3 联调 API 冒烟（integration/p1-3 · 正常流 + C/D 异常语义）"""
import json
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000/api"


def req(method: str, path: str, body=None, token: str | None = None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        BASE + path, data=data, headers=headers, method=method
    )
    with urllib.request.urlopen(request, timeout=120) as resp:
        return json.loads(resp.read())


def pick_pending_orders(token: str, count: int = 2) -> list[str]:
    result = req("GET", "/orders?status=pending&page=1&page_size=50", token=token)
    items = result["data"]["items"]
    codes = [o["order_code"] for o in items[:count]]
    if len(codes) < count:
        raise RuntimeError(f"pending 订单不足 {count} 条")
    return codes


def run_flow(token: str, order_codes: list[str], normal_all: bool) -> dict:
    preview = req(
        "POST",
        "/schedule/global",
        {"algorithm": "traditional", "preview": True, "order_codes": order_codes},
        token=token,
    )
    assert preview["code"] == 0, preview
    schedule_code = preview["data"]["schedule_code"]

    confirm = req("POST", f"/schedule/confirm/{schedule_code}", None, token=token)
    assert confirm["code"] == 0, confirm

    nd = req(
        "POST",
        "/schedule/node-dispatch",
        {"schedule_code": schedule_code, "demo_mode": False},
        token=token,
    )
    assert nd["code"] == 0, nd
    batch_code = nd["data"]["batch_code"]

    batch = req("GET", f"/schedule/batches/{batch_code}", token=token)
    dispatches = batch["data"]["dispatches"]
    l0_pkgs: list[str] = []
    l1_node = ""
    for d in dispatches:
        if d.get("level_phase") != 0:
            continue
        for task in d["tasks"]:
            if task.get("is_return"):
                continue
            codes = task.get("package_codes") or []
            if not codes and task.get("package_details"):
                codes = [p["package_code"] for p in task["package_details"]]
            for code in codes:
                l0_pkgs.append(code)
            if not l1_node and task.get("to_node_code"):
                l1_node = task["to_node_code"]

    if not l0_pkgs:
        raise RuntimeError("L0 调度无包裹")

    for pkg in l0_pkgs:
        deliver = req(
            "POST",
            "/simulation/deliver",
            {"package_code": pkg},
            token=token,
        )
        assert deliver["code"] == 0, deliver

    arrival = req(
        "GET",
        f"/simulation/arrival-packages?schedule_code={schedule_code}&node_code={l1_node}",
        token=token,
    )
    assert arrival["code"] == 0, arrival
    rows = arrival["data"]
    if not rows:
        raise RuntimeError(f"arrival-packages 为空 node={l1_node}")

    confirmations = []
    for i, row in enumerate(rows):
        is_normal = True if normal_all else (i == 0)
        item = {"package_code": row["package_code"], "is_normal": is_normal}
        if not is_normal:
            item["exception_subtype"] = "damaged"
        confirmations.append(item)

    batch_confirm = req(
        "POST",
        "/simulation/confirm-arrival-batch",
        {"schedule_code": schedule_code, "confirmations": confirmations},
        token=token,
    )
    assert batch_confirm["code"] == 0, batch_confirm

    nd2 = req(
        "POST",
        "/schedule/node-dispatch",
        {"schedule_code": schedule_code, "demo_mode": False},
        token=token,
    )
    assert nd2["code"] == 0, nd2

    in_transit = req(
        "GET", "/packages?status=in_transit&page=1&page_size=100", token=token
    )
    transit_codes = [p["package_code"] for p in in_transit["data"]["items"]]

    return {
        "schedule_code": schedule_code,
        "l1_node": l1_node,
        "l0_pkgs": l0_pkgs,
        "arrival_count": len(rows),
        "confirm": batch_confirm["data"],
        "transit_after_l1": transit_codes,
        "orders": order_codes,
    }


def main() -> int:
    try:
        login = req(
            "POST", "/auth/login", {"username": "dispatcher", "password": "123456"}
        )
        token = login["data"]["access_token"]
        print("login ok")

        orders_a = pick_pending_orders(token, 2)
        normal = run_flow(token, orders_a, normal_all=True)
        print("normal flow ok", json.dumps(normal, ensure_ascii=False))

        orders_b = pick_pending_orders(token, 2)
        mixed = run_flow(token, orders_b, normal_all=False)
        print("mixed flow ok", json.dumps(mixed, ensure_ascii=False))

        if mixed["confirm"].get("success_count", 0) < 1:
            print("mixed confirm failed")
            return 1

        print("ALL_P1_3_API_CHECKS_PASS")
        return 0
    except urllib.error.HTTPError as e:
        print("HTTP error", e.code, e.read().decode())
        return 1
    except Exception as e:
        print("FAIL", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
