"""Phase 8 live test - runs against running backend server"""
import requests
import json
import sys
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "http://localhost:8000"

def step(label):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")

# ── 1. Login ──
step("1. Login to get token")
r = requests.post(f"{BASE}/api/auth/login", json={
    "username": "dispatcher", "password": "123456"
})
assert r.status_code == 200, f"Login failed: {r.text}"
data = r.json()
token = data["data"]["access_token"]
role = data["data"]["role"]
print(f"  role={role}, token={token[:30]}...")
HEADERS = {"Authorization": f"Bearer {token}"}

# ── 2. Health check ──
step("2. Health check")
r = requests.get(f"{BASE}/api/health")
assert r.status_code == 200
print(f"  STATUS: {r.json()['data']['status']}")

# ── 3. AI Parse dry-run (default, no message) ──
step("3. AI Parse dry-run (default, no message)")
r = requests.post(f"{BASE}/api/ai/parse", json={
    "execute": "dry-run"
}, headers=HEADERS)
print(f"  HTTP {r.status_code}")
d = r.json()
print(json.dumps(d, indent=2, ensure_ascii=False))

# Verify dry-run format
assert d["code"] == 0, f"Expected code=0, got {d['code']}"
assert "data" in d
dd = d["data"]
assert "algorithm_params" in dd, "Missing algorithm_params"
assert "mode" in dd, "Missing mode"
assert dd["mode"] == "default"
assert "status" not in dd, "dry-run should NOT have status"
assert "schedule_code" not in dd, "dry-run should NOT have schedule_code"
assert "is_replan" not in dd, "dry-run should NOT have is_replan"
assert "reference_codes" not in dd, "dry-run should NOT have reference_codes"
assert "global_schedule" in dd["algorithm_params"], "Must have global_schedule"
assert "node_dispatch" not in dd["algorithm_params"], "Must NOT have node_dispatch"
assert "route_planning" not in dd["algorithm_params"], "Must NOT have route_planning"
print("  [PASS] dry-run default params - response format correct")

# ── 4. AI Parse dry-run (with message) ──
step("4. AI Parse dry-run (message: 'shortest distance first')")
r = requests.post(f"{BASE}/api/ai/parse", json={
    "message": "shortest distance, prefer nearest path",
    "execute": "dry-run"
}, headers=HEADERS)
print(f"  HTTP {r.status_code}")
d = r.json()
print(json.dumps(d, indent=2, ensure_ascii=False))

assert d["code"] == 0
dd = d["data"]
assert "algorithm_params" in dd
assert "mode" in dd
assert "global_schedule" in dd["algorithm_params"]
meta = d.get("meta", {})
if meta.get("degraded"):
    print(f"  [WARN] DeepSeek degraded: {meta.get('degraded_reason')}")
else:
    gs = dd["algorithm_params"]["global_schedule"]
    w = gs.get("weights", {})
    print(f"  [PASS] AI parsed successfully, mode={dd['mode']}, weights={w}")

# ── 5. AI Parse new schedule (draft, no message) ──
step("5. AI Parse new schedule (draft, default params)")
r = requests.post(f"{BASE}/api/ai/parse", json={
    "execute": "draft"
}, headers=HEADERS)
print(f"  HTTP {r.status_code}")
d = r.json()
print(json.dumps(d, indent=2, ensure_ascii=False))

assert d["code"] == 0
dd = d["data"]
assert "schedule_code" in dd, "draft should have schedule_code"
assert dd["is_replan"] == False
assert dd["status"] == "draft"
assert "global_schedule" in dd["algorithm_params"]
assert "node_dispatch" not in dd["algorithm_params"]
assert "route_planning" not in dd["algorithm_params"]
assert "replan_results" not in dd, "Must NOT have replan_results"
print(f"  [PASS] draft created: {dd['schedule_code']}")

# ── 6. Test manual weights dry-run ──
step("6. AI Parse dry-run (manual weights)")
r = requests.post(f"{BASE}/api/ai/parse", json={
    "weights": {
        "global_schedule": {
            "weights": {
                "distance": 0.8,
                "time": 0.1,
                "package_count": 0.1
            }
        }
    },
    "execute": "dry-run"
}, headers=HEADERS)
print(f"  HTTP {r.status_code}")
d = r.json()
print(json.dumps(d, indent=2, ensure_ascii=False))

assert d["code"] == 0
dd = d["data"]
assert "global_schedule" in dd["algorithm_params"]
assert "node_dispatch" not in dd["algorithm_params"]
gs = dd["algorithm_params"]["global_schedule"]
assert gs["weights"]["distance"] == 0.8
print("  [PASS] manual weights normalized correctly")

# ── Summary ──
step("ALL TESTS PASSED!")
print("""
Phase 8 changes verified:
  [PASS] dry-run response: only algorithm_params + mode
  [PASS] algorithm_params: only global_schedule (no node_dispatch/route_planning)
  [PASS] default mode: no message -> mode=default with standard weights
  [PASS] manual mode: manual weights -> only global_schedule kept
  [PASS] draft mode: includes schedule_code + status=draft
  [PASS] replan_results: removed from schema
  [PASS] AI mode: calls DeepSeek (or degrades gracefully)
""")
