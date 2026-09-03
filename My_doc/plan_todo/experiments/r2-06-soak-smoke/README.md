# R2-06 P2 soak smoke evidence

Small redacted summaries from the first soak smoke.

This run only proves the sampler/k6/checker harness. It does not prove the
absence of leaks. Do not compare soak P95 with the 5-minute read-mix or
write-path P95.

## Run

- URL: https://github.com/justtodo123/LogisticSystem_more/actions/runs/33717505441
- Branch: main
- Commit: 66f2d845e6672fb241926f41d2405da6fb38cfb9
- Mode: smoke
- Duration: 8m
- Read-mix RPS: 4 plus 1 login RPS
- Topology: PostgreSQL 16, Redis 7, Uvicorn 2 workers, 1 outbox worker

## Result

- passed: true
- sample_count: 33
- health_ok: true
- error_rate_ok: true
- unexpected_5xx_ok: true
- dropped_iterations: 0
- RSS: 321172 KB -> 387180 KB (1.206x over 8m; not a leak conclusion)
- Postgres connections: 8 -> 13
- Redis clients: 4 -> 5
- mixed HTTP P95: 312.87 ms (login-heavy mix; do not compare with 5m 8 RPS read-mix P95 9.81 ms)
- p95_regression_ok: null

Keep large API logs in the 14-day CI artifact `r2-06-soak`.
