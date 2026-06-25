"""Phase 8 AI 集成测试脚本"""
import requests, json, time

BASE = "http://localhost:8000/api"
TOKEN = None

def login():
    global TOKEN
    r = requests.post(f"{BASE}/auth/login", json={"username":"dispatcher","password":"123456"})
    d = r.json()
    TOKEN = d["data"]["access_token"]
    print(f"[LOGIN] token={TOKEN[:40]}...")

def test(name, path, body, timeout=120):
    print(f"\n{'='*60}")
    print(f"[TEST] {name}")
    print(f"  POST {path}")
    print(f"  body: {json.dumps(body, ensure_ascii=False)[:200]}")
    t0 = time.time()
    try:
        r = requests.post(
            f"{BASE}{path}", json=body,
            headers={"Authorization": f"Bearer {TOKEN}"},
            timeout=timeout
        )
        elapsed = time.time() - t0
        print(f"  HTTP {r.status_code}  elapsed={elapsed:.1f}s")
        d = r.json()
        code = d.get("code", "N/A")
        msg = d.get("message", "N/A")
        meta = d.get("meta", {})
        degraded = meta.get("degraded", False)
        degraded_reason = meta.get("degraded_reason")
        
        print(f"  code={code}  message={msg}")
        print(f"  degraded={degraded}  reason={degraded_reason}")
        
        if d.get("data"):
            dd = d["data"]
            print(f"  mode={dd.get('mode')}  is_replan={dd.get('is_replan')}")
            print(f"  schedule_code={dd.get('schedule_code')}")
            if dd.get("algorithm_params"):
                ap = dd["algorithm_params"]
                for section in ap:
                    print(f"    {section}: {ap[section]}")
        
        return d
    except requests.Timeout:
        elapsed = time.time() - t0
        print(f"  TIMEOUT after {elapsed:.1f}s")
        return None
    except Exception as e:
        print(f"  ERROR: {e}")
        return None

def check_db():
    import sqlite3
    conn = sqlite3.connect("data/logistics.db")
    cur = conn.cursor()
    
    print("\n=== global_schedules (last 5) ===")
    cur.execute("SELECT schedule_code, is_replan, version, total_goods, total_distance FROM global_schedules ORDER BY id DESC LIMIT 5")
    for r in cur:
        print(f"  {r}")
    
    print("\n=== dispatch_batches (last 5) ===")
    cur.execute("SELECT batch_code, status, l0_l1_dispatch_count, l1_l2_dispatch_count FROM dispatch_batches ORDER BY id DESC LIMIT 5")
    for r in cur:
        print(f"  {r}")
    
    print("\n=== routes (last 5) ===")
    cur.execute("SELECT route_code, total_distance FROM routes ORDER BY id DESC LIMIT 5")
    for r in cur:
        print(f"  {r}")
    
    conn.close()

def main():
    login()
    
    # Test 1: dry-run (快速验证 AI 解析)
    test("T1: AI dry-run", "/ai/parse", {
        "message": "优先缩短距离，多用电车",
        "execute": "dry-run"
    }, timeout=30)
    
    # Test 2: AI 重规划 GS20260623001 (原 O006 方案)
    # 注意：O006 之前已经被完成，先查看是否 pending
    r = requests.get(f"{BASE}/orders?status=pending&page=1&page_size=5",
                     headers={"Authorization": f"Bearer {TOKEN}"})
    pending = r.json().get("data", {}).get("items", [])
    pending_codes = [o["order_code"] for o in pending]
    print(f"\n[INFO] pending orders: {pending_codes}")
    
    # 用 GS20260623008（O005 原方案，已验证可重规划）
    result = test("T2: AI replan GS20260623008", "/ai/parse", {
        "message": "优先时效，减少总时间",
        "schedule_codes": ["GS20260623008"]
    }, timeout=120)
    
    check_db()

if __name__ == "__main__":
    main()
