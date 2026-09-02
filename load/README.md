# k6 load scripts (R2-06)

These scripts are the P1 load/spike harness. They are **not** a local Windows proof: this host has no k6/Docker/PostgreSQL.

- `helpers.js` — base URL, JSON headers, request IDs
- `load.js` — constant arrival-rate mix: health, login, `/api/auth/me`, orders list, `/metrics`
- `spike.js` — ramping arrival-rate on health + login + me

Run on GitHub Actions via workflow `P1 load and spike` (`workflow_dispatch`).

Example (Linux/GHA):

```bash
k6 run -e BASE_URL=http://127.0.0.1:18001 -e DURATION=5m -e RPS=8 load/k6/load.js
k6 run -e BASE_URL=http://127.0.0.1:18001 -e SPIKE_RPS=25 load/k6/spike.js
```

Relative gates after a real run: error rate <1%, no unexpected 5xx, P95 within 15% of that run's own warmup. Do not pre-fill absolute QPS.
