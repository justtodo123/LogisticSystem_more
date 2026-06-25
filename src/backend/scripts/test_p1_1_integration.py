"""P1-1 联调 API 冒烟测试（integration/p1-1）"""
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


def main() -> int:
    try:
        login = req("POST", "/auth/login", {"username": "dispatcher", "password": "123456"})
        token = login["data"]["access_token"]
        print("login ok")

        created = req("POST", "/schedule/global", {"algorithm": "traditional"}, token=token)
        code = created["data"]["schedule_code"]
        print("schedule", code, "score_display", created["data"].get("score_display"))

        detail = req("GET", f"/schedule/global/{code}", token=token)
        goods_schedules = detail["data"].get("goods_schedules") or []
        gs = goods_schedules[0] if goods_schedules else {}
        path = gs.get("path", [])
        if not (path and isinstance(path[0], dict) and path[0].get("node_code")):
            print("path format fail")
            return 1
        print("path object ok")

        packages = detail["data"].get("packages") or []
        print("packages count", len(packages))

        nd = req(
            "POST",
            "/schedule/node-dispatch",
            {"schedule_code": code, "demo_mode": True},
            token=token,
        )
        batch = nd["data"]["batch_code"]
        print("batch", batch)

        bd = req("GET", f"/schedule/batches/{batch}", token=token)
        dispatches = bd["data"].get("dispatches") or []
        task = dispatches[0]["tasks"][0]
        if not task.get("from_node_name"):
            print("missing from_node_name")
            return 1
        if not task.get("package_details"):
            print("missing package_details")
            return 1
        print("dispatch dto ok")

        vehicle = dispatches[0]["vehicle_code"]
        route = req("GET", f"/routes/by-vehicle/{vehicle}/coordinates", token=token)
        print("route nodes", len(route["data"].get("nodes") or []))

        pkg_code = task["package_details"][0]["package_code"]
        sim = req("POST", "/simulation/deliver", {"package_code": pkg_code}, token=token)
        print("simulation deliver ok", sim["data"].get("package_code", pkg_code))

        if gs.get("goods_code"):
            req("GET", f"/goods/{gs['goods_code']}", token=token)
        if gs.get("order_code"):
            req("GET", f"/orders/{gs['order_code']}", token=token)

        print("ALL_P1_1_API_CHECKS_PASS")
        return 0
    except urllib.error.HTTPError as e:
        print("HTTP error", e.code, e.read().decode())
        return 1
    except Exception as e:
        print("FAIL", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
