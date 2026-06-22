"""Phase 8 全链路验证：F007 → F021 → F005 → F006"""
import sqlite3

DB = "data/logistics.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

print("=" * 60)
print("GS20260623010 (AI replan) 全链路验证")
print("=" * 60)

# F007: global_schedule
cur.execute("SELECT * FROM global_schedules WHERE schedule_code='GS20260623010'")
cols = [d[0] for d in cur.description]
gs = cur.fetchone()
if gs:
    d = dict(zip(cols, gs))
    print("\n[F007] global_schedule: OK")
    print(f"  version={d['version']}  is_replan={d['is_replan']}  parent_id={d['parent_id']}")
    print(f"  total_goods={d['total_goods']}  total_distance={d['total_distance']}  total_time={d['total_time']}")
    print(f"  replan_reason={d['replan_reason']}")
    gs_id = d['id']
else:
    print("\n[F007] global_schedule: NOT FOUND!")
    gs_id = None

# F021: packages
cur.execute("SELECT package_code, status, from_node_id, to_node_id FROM packages WHERE schedule_id=?", (gs_id,))
pkgs = cur.fetchall()
print(f"\n[F021] packages: {len(pkgs)} created")
for p in pkgs:
    # get node codes
    cur.execute("SELECT node_code, node_type FROM nodes WHERE id=?", (p[2],))
    fn = cur.fetchone()
    cur.execute("SELECT node_code, node_type FROM nodes WHERE id=?", (p[3],))
    tn = cur.fetchone()
    print(f"  {p[0]}  status={p[1]}  {fn[0]}({fn[1]}) -> {tn[0]}({tn[1]})")

# F005: dispatch_batches
cur.execute("SELECT batch_code, status, l0_l1_dispatch_count, l1_l2_dispatch_count FROM dispatch_batches WHERE global_schedule_id=?", (gs_id,))
batches = cur.fetchall()
print(f"\n[F005] dispatch_batches: {len(batches)}")
for b in batches:
    print(f"  {b[0]}  status={b[1]}  L0->L1={b[2]}  L1->L2={b[3]}")
    cur.execute("SELECT id FROM dispatch_batches WHERE batch_code=?", (b[0],))
    batch_id = cur.fetchone()[0]

# F005: node_dispatches
for b in batches:
    cur.execute("SELECT id FROM dispatch_batches WHERE batch_code=?", (b[0],))
    batch_id = cur.fetchone()[0]
    cur.execute("SELECT dispatch_code, level_phase, vehicle_id, total_distance FROM node_dispatches WHERE dispatch_batch_id=?", (batch_id,))
    nds = cur.fetchall()
    print(f"\n[F005] node_dispatches for {b[0]}: {len(nds)}")
    for nd in nds:
        print(f"  {nd[0]}  phase={nd[1]}  vehicle_id={nd[2]}  dist={nd[3]}")

# F006: routes
for b in batches:
    cur.execute("SELECT id FROM dispatch_batches WHERE batch_code=?", (b[0],))
    batch_id = cur.fetchone()[0]
    cur.execute("SELECT nd.id FROM node_dispatches nd WHERE nd.dispatch_batch_id=?", (batch_id,))
    dispatch_ids = [r[0] for r in cur.fetchall()]
    for did in dispatch_ids:
        cur.execute("SELECT route_code, total_distance, total_time FROM routes WHERE dispatch_id=?", (did,))
        routes = cur.fetchall()
        print(f"\n[F006] routes for dispatch_id={did}: {len(routes)}")
        for rt in routes:
            print(f"  {rt[0]}  dist={rt[1]}  time={rt[2]}")

# 对比: GS20260623008 vs GS20260623010
print("\n" + "=" * 60)
print("版本对比: GS20260623008 (v1) vs GS20260623010 (v?)")
cur.execute("SELECT schedule_code, version, total_distance, total_time, score FROM global_schedules WHERE schedule_code IN ('GS20260623008','GS20260623010') ORDER BY id")
for r in cur.fetchall():
    print(f"  {r[0]}  v{r[1]}  dist={r[2]}  time={r[3]}  score={r[4]}")

# goods status check
print("\n=== goods status 分布 ===")
cur.execute("SELECT status, count(*) FROM goods GROUP BY status")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

conn.close()
