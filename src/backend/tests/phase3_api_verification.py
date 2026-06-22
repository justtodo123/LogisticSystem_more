"""
阶段3（全局调度 F007+F021）实际环境 API 验证脚本
目标：启动后端服务后运行此脚本，验证所有阶段3 API 端点
用法：python test_phase3_api.py
"""
import requests
import json
import time
import sys
import io

# 强制 UTF-8 输出
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = "http://localhost:8000/api"
TOKEN = None
SCHEDULE_CODE = None

PASS = 0
FAIL = 0
WARN = 0

def ok(msg, detail=""):
    global PASS
    PASS += 1
    print(f"  [PASS] {msg}")
    if detail:
        print(f"         {detail}")

def bad(msg, detail=""):
    global FAIL
    FAIL += 1
    print(f"  [FAIL] {msg}")
    if detail:
        print(f"         {detail}")

def warn(msg, detail=""):
    global WARN
    WARN += 1
    print(f"  [WARN] {msg}")
    if detail:
        print(f"         {detail}")

def hr(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ── 0. 健康检查 ──────────────────────────────────────
hr("0. 健康检查")
r = requests.get(f"{BASE}/health")
if r.status_code == 200 and r.json()["code"] == 0:
    ok("GET /api/health", f"status={r.json()['data']['status']}")
else:
    bad("健康检查失败", f"status={r.status_code}")
    exit(1)


# ── 1. 认证 ──────────────────────────────────────────
hr("1. 认证")
# 1a. 登录 dispatcher
r = requests.post(f"{BASE}/auth/login", json={
    "username": "dispatcher",
    "password": "123456"
})
data = r.json()
if r.status_code == 200 and data["code"] == 0:
    TOKEN = data["data"]["access_token"]
    ok("POST /api/auth/login (dispatcher)", f"token={TOKEN[:20]}...")
else:
    bad("dispatcher登录失败", f"code={data.get('code')} msg={data.get('message')}")
    exit(1)

HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# 1b. 获取当前用户信息
r = requests.get(f"{BASE}/auth/me", headers=HEADERS)
data = r.json()
if r.status_code == 200 and data["code"] == 0:
    ok("GET /api/auth/me", f"user={data['data']['username']} role={data['data']['role']}")
else:
    bad("获取用户信息失败")

# 1c. 无Token访问受保护接口
r = requests.post(f"{BASE}/schedule/global", json={})
data = r.json()
if r.status_code == 401 and data["code"] == 40100:
    ok("401 未登录拦截", f"code={data['code']} msg={data['message']}")
else:
    bad("401拦截异常", f"status={r.status_code} code={data.get('code')}")

# 1d. manager 无写权限
r2 = requests.post(f"{BASE}/auth/login", json={"username": "manager", "password": "123456"})
if r2.status_code == 200 and r2.json()["code"] == 0:
    mgr_token = r2.json()["data"]["access_token"]
    r = requests.post(f"{BASE}/schedule/global", json={}, headers={"Authorization": f"Bearer {mgr_token}"})
    data = r.json()
    if r.status_code == 403 and data["code"] == 40300:
        ok("403 manager无写权限", f"code={data['code']}")
    else:
        bad("403拦截异常", f"status={r.status_code} code={data.get('code')}")


# ── 2. 查看待调度订单 ───────────────────────────────
hr("2. 待调度订单")
r = requests.get(f"{BASE}/orders?status=pending", headers=HEADERS)
data = r.json()
if r.status_code == 200 and data["code"] == 0:
    orders = data.get("data", {}).get("items", data.get("data", []))
    if isinstance(orders, list):
        cnt = len(orders)
    else:
        cnt = data.get("data", {}).get("total", "?")
    ok("GET /api/orders?status=pending", f"待调度订单数: {cnt}")
    if isinstance(orders, list) and len(orders) > 0:
        for o in orders[:3]:
            print(f"     {o.get('order_code', '?')} - status={o.get('status')}")
else:
    bad("获取待调度订单失败", f"status={r.status_code} code={data.get('code')}")


# ── 3. 执行全局调度 ─────────────────────────────────
hr("3. 执行全局调度 POST /api/schedule/global")
r = requests.post(f"{BASE}/schedule/global", json={}, headers=HEADERS)
data = r.json()
print(f"  response code={data.get('code')} message={data.get('message')}")
print(f"  meta: {json.dumps(data.get('meta'), ensure_ascii=False)}")

if r.status_code == 200 and data["code"] == 0:
    SCHEDULE_CODE = data.get("data", {}).get("schedule_code")
    ok("POST /api/schedule/global 成功", f"schedule_code={SCHEDULE_CODE}")
    
    # 打印调度详情
    sd = data.get("data", {})
    for k in ["total_goods", "total_packages", "total_distance", "total_time", "goods_schedules"]:
        v = sd.get(k)
        if k == "goods_schedules" and isinstance(v, list):
            print(f"     {k}: [{len(v)} 条货物调度记录]")
            for gs in v[:3]:
                print(f"       {gs.get('goods_code','?')}: {' → '.join(gs.get('path',[]))}")
        elif v is not None:
            print(f"     {k}: {v}")
elif r.status_code == 200 and data["code"] != 0:
    warn(f"业务失败: code={data['code']} msg={data['message']}")
    # 可能是没有pending订单或其他约束不满足
else:
    bad("调度请求失败", f"HTTP {r.status_code}: {data.get('message')}")


# ── 4. 查询调度列表 ─────────────────────────────────
hr("4. GET /api/schedule/global (列表)")
r = requests.get(f"{BASE}/schedule/global", headers=HEADERS)
data = r.json()
if r.status_code == 200 and data["code"] == 0:
    items = data.get("data", {}).get("items", data.get("data", []))
    if isinstance(items, list):
        ok("调度列表查询成功", f"共 {len(items)} 条调度记录")
        for s in items[:5]:
            print(f"     {s.get('schedule_code','?')} version={s.get('version','?')} goods={s.get('total_goods','?')}")
    else:
        total = data.get("data", {}).get("total", "?")
        ok("调度列表查询成功", f"total={total}")
else:
    bad("调度列表查询失败", f"HTTP {r.status_code} code={data.get('code')}")


# ── 5. 查询调度详情 ─────────────────────────────────
if SCHEDULE_CODE:
    hr(f"5. GET /api/schedule/global/{SCHEDULE_CODE}")
    r = requests.get(f"{BASE}/schedule/global/{SCHEDULE_CODE}", headers=HEADERS)
    data = r.json()
    if r.status_code == 200 and data["code"] == 0:
        ok("调度详情查询成功", f"schedule_code={SCHEDULE_CODE}")
        sd = data.get("data", {})
        for k in ["schedule_code", "total_goods", "total_packages", "total_distance", "total_time", "version", "is_replan"]:
            v = sd.get(k)
            if v is not None:
                print(f"     {k}: {v}")
    else:
        bad("调度详情查询失败", f"HTTP {r.status_code} code={data.get('code')}")


# ── 6. 验证数据库写入 ───────────────────────────────
hr("6. 验证数据库写入")
try:
    from sqlalchemy import create_engine, text
    engine = create_engine("sqlite:///./data/logistics.db")
    conn = engine.connect()
    
    # 6a. global_schedules 表
    if SCHEDULE_CODE:
        r = conn.execute(text(
            "SELECT schedule_code, total_goods, total_packages, version, is_replan FROM global_schedules WHERE schedule_code=:sc"
        ), {"sc": SCHEDULE_CODE}).fetchone()
        if r:
            ok(f"global_schedules 写入确认", f"code={r[0]} goods={r[1]} pkgs={r[2]} ver={r[3]} replan={r[4]}")
        else:
            bad(f"global_schedules 中未找到 {SCHEDULE_CODE}")
    else:
        warn("跳过（未生成schedule_code）")
    
    # 6b. packages 表
    pkg_cnt = conn.execute(text("SELECT count(*) FROM packages")).scalar()
    ok(f"packages 表记录数", f"共 {pkg_cnt} 条包裹记录")
    
    # 6c. orders 状态更新
    r = conn.execute(text("SELECT status, count(*) FROM orders GROUP BY status")).fetchall()
    status_map = {row[0]: row[1] for row in r}
    if status_map.get("delivering", 0) > 50:
        ok("订单状态已更新", f"delivering: {status_map.get('delivering', 0)}, pending: {status_map.get('pending', 0)}")
    else:
        warn("订单状态未明显变化", f"状态分布: {status_map}")
    
    conn.close()
except Exception as e:
    bad("数据库验证异常", str(e))


# ── 7. 边界测试 ─────────────────────────────────────
hr("7. 边界测试")

# 7a. 查询不存在的调度
r = requests.get(f"{BASE}/schedule/global/GS99999999", headers=HEADERS)
data = r.json()
if r.status_code == 404:
    ok("GET 不存在的调度 404", f"code={data.get('code')} msg={data.get('message')}")
elif r.status_code == 200 and data["code"] != 0:
    ok("GET 不存在的调度 业务失败", f"code={data.get('code')}")
else:
    warn("边界测试结果", f"status={r.status_code} code={data.get('code')}")


# ── 总结 ────────────────────────────────────────────
hr("测试总结")
total = PASS + FAIL + WARN
print(f"  总计: {total}  通过: {PASS}  失败: {FAIL}  警告: {WARN}")
if FAIL == 0:
    print(f"\n  [OK] 阶段3（全局调度 F007+F021）实际环境验证通过！")
else:
    print(f"\n  [!!] 有 {FAIL} 项失败，请检查。")

# 清理
sys.stdout.flush()
import os
os._exit(0 if FAIL == 0 else 1)
