# k6 load scripts (R2-06)

These scripts are the P1 load/spike harness. They are **not** a local Windows proof: this host has no k6/Docker/PostgreSQL.

- `helpers.js` ? base URL, JSON headers, request IDs, shared login helper
- `load.js` ? setup() reuses one JWT; 8 RPS read mix (health, me, orders, metrics) plus 1 RPS login
- `spike.js` ? same token reuse; ramping read mix to 25 RPS plus 1 RPS login

Do not login on every iteration: bcrypt password checks block a single asyncio worker and inflate P95.

Run on GitHub Actions via workflow `P1 load and spike` (`workflow_dispatch`).

Example (Linux/GHA):

```bash
k6 run -e BASE_URL=http://127.0.0.1:18001 -e DURATION=5m -e RPS=8 -e LOGIN_RPS=1 load/k6/load.js
k6 run -e BASE_URL=http://127.0.0.1:18001 -e SPIKE_RPS=25 -e LOGIN_RPS=1 load/k6/spike.js
```

Gates: error rate <1%, no unexpected 5xx, dropped iterations bounded. Absolute P95 is recorded from a real run, not pre-filled as a 2s SLO.
