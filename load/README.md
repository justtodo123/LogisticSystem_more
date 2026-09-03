# k6 load scripts (R2-06)

These scripts are the P1 load/spike harness. They are **not** a local Windows proof: this host has no k6/Docker/PostgreSQL.

- `helpers.js` - base URL, JSON headers, request IDs, shared login helper
- `load.js` - setup() reuses one JWT; 8 RPS read mix (health, me, orders, metrics) plus 1 RPS login
- `spike.js` - same token reuse; ramping read mix to 25 RPS plus 1 RPS login
- `idempotency.js` - replay the same idempotency key; concurrent same-key writes must not create extra records
- `confirm-conflict.js` - several VUs confirm one draft schedule; at most one success, others 409/40901

Do not login on every iteration: bcrypt password checks block a single asyncio worker and inflate P95.

Run read-mix load/spike on GitHub Actions via workflow `P1 load and spike` (`workflow_dispatch`).

Run write-path smoke/load via a separate workflow `P1 write-path smoke and load` (`.github/workflows/p1-write-path.yml`, `workflow_dispatch` only). The 2026-09-03 5m load (GHA run 33710390070) established `load/baselines` for idempotency and confirm-conflict. Do not bind it to PRs until a second comparable load exists. Do not claim relative regression passed on this first baseline, and never compare write-path P95 with read-mix P95.

Example (Linux/GHA):

```bash
k6 run -e BASE_URL=http://127.0.0.1:18001 -e DURATION=5m -e RPS=8 -e LOGIN_RPS=1 load/k6/load.js
k6 run -e BASE_URL=http://127.0.0.1:18001 -e SPIKE_RPS=25 -e LOGIN_RPS=1 load/k6/spike.js
k6 run -e BASE_URL=http://127.0.0.1:18001 -e DURATION=30s -e WRITE_RPS=2 load/k6/idempotency.js
k6 run -e BASE_URL=http://127.0.0.1:18001 -e CONFIRM_VUS=8 load/k6/confirm-conflict.js
python src/backend/scripts/compare_k6_summaries.py artifacts/r2-06-load/load-summary.json candidate.json
python src/backend/scripts/compare_k6_summaries.py load/baselines/idempotency-summary.json artifacts/r2-06-write/idempotency-summary.json --scenario idempotency --json-output artifacts/r2-06-write/idempotency-comparison.json
python src/backend/scripts/compare_k6_summaries.py load/baselines/confirm-conflict-summary.json artifacts/r2-06-write/confirm-conflict-summary.json --scenario confirm-conflict --json-output artifacts/r2-06-write/confirm-conflict-comparison.json
```

Gates: error rate <1%, no unexpected 5xx, dropped iterations bounded. Absolute P95 is recorded from a real run, not pre-filled as a 2s SLO.

Write/confirm scenarios report their own P95 and conflict/replay rates instead of being folded into the read-mix P95. The comparator is executable now and is not a PR gate yet.
