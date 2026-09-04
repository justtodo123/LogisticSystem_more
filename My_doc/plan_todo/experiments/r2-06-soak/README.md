# R2-06 P2 2h soak evidence

First 2-hour soak. This is not a relative P95 pass and is not comparable
to the 5-minute read-mix or write-path P95.

Do not treat the 8-minute soak smoke as this run's baseline.

## Run

- URL: https://github.com/justtodo123/LogisticSystem_more/actions/runs/33720629269
- Branch: main
- Commit: 845a89568bc0b11be2d79e20a3948362ecc0f2cd
- Mode: soak
- Duration: 2h
- Read-mix RPS: 4 plus 1 login RPS
- Topology: PostgreSQL 16, Redis 7, Uvicorn 2 workers, 1 outbox worker
- Samples: 480 at 15s (2026-09-03T05:52:20Z to 2026-09-03T07:52:25Z)

## Result

- passed: true
- health_ok: true
- error_rate_ok: true
- unexpected_5xx_ok: true
- dropped_iterations: 0
- k6 iterations: 36001; checks 158402/158402
- RSS: 317872 KB -> 388464 KB (1.222x overall)
- After warmup (~5 min): 387864 KB -> 388464 KB (1.002x, 600 KB band)
- Postgres connections: 8 -> 13 and then stable at 13
- Redis clients: 5 stable
- mixed HTTP P95: 279.11 ms (login-heavy mix; do not compare with 5m 8 RPS read-mix P95 9.81 ms)
- p95_regression_ok: null

This does not prove the absence of all leaks. It shows no unbounded RSS or
connection growth at 4 RPS over 2 hours after warmup.

Keep the 19 MB API log in the 14-day CI artifact `r2-06-soak`.

Image scanning and the scan-before-push release gate are complete. Grafana/Prometheus/OTel deployment, cross-worker metric aggregation, and scheduled image scanning remain follow-up work.
