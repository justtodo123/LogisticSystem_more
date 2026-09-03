# R2-06 write-path evidence

Small, redacted summaries from the first successful 5-minute GHA write-path load.

Do not compare these P95 values with the 2026-09-02 read-mix load/spike evidence.

## Current status

Formal load GHA run succeeded on 2026-09-03. Comparator mode is `establish_baseline` only.

- Load run: https://github.com/justtodo123/LogisticSystem_more/actions/runs/33710390070
- Smoke precursor: https://github.com/justtodo123/LogisticSystem_more/actions/runs/33709314507
- Branch: `feat/R2-06-end-to-end-trace-propagation`
- Commit: `b87db196fe0461429c35a55209b5a565ed57a71b`
- Mode: load (`DURATION=5m`, `WRITE_RPS=2`, `CONFIRM_VUS=8`)
- Topology: PostgreSQL 16, Redis 7, Uvicorn 2 workers, 1 outbox worker
- Python 3.13.15, k6 v2.2.0
- Artifact: `r2-06-write-path` (14 days)
- Repo copies: this directory and `load/baselines/*.json`

This first successful load only establishes a write-path baseline. It must not claim relative P95 regression passed. Do not bind the workflow to PRs until a second comparable load exists.

## Load numbers

Idempotency (5m, 2 RPS):

- `http_req_failed` 0, `unexpected_5xx` 0, `duplicate_side_effects` 0
- `idempotency_replay_rate` 1.0 (600/600)
- write P95 27.66 ms, write P99 73.16 ms
- DB: 600 unique `k6-node-*` storage centers, no leftover PROCESSING outbox

Confirm-conflict (8 VUs, 8 iterations):

- 1 success / 7 conflicts (`confirmation_conflict_rate` 0.875)
- `unexpected_5xx` 0, `duplicate_side_effects` 0
- confirm P95 836.7 ms (do not use mixed HTTP P95; setup/login dominates that)
- schedule `GS20260903001` ended `active` version 2

Trace probe:

- `trace_id=trc-write-path-probe` is stable across success, retry, and dead-letter
- each worker execution mints a new `request_id`
- `parent_request_id=req-write-path-probe`
- independent worker process log is empty: probe delivers in-process before the worker starts; k6 writes did not enqueue extra outbox rows

## Files

- `idempotency-summary.json`
- `confirm-conflict-summary.json`
- `comparison-report.json`
- `invariants.json`
- `trace-probe.json`
- `env-report.json`

Keep large API/worker logs in the 14-day CI artifact `r2-06-write-path`.
