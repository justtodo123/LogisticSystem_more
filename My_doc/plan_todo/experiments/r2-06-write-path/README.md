# R2-06 write-path evidence

This directory holds small, redacted summaries after a real GHA write-path run.

## Current status

Smoke GHA run succeeded on 2026-09-03. This is a 30s low-traffic probe, not the 5-10 minute formal write-path load.

- Run: https://github.com/justtodo123/LogisticSystem_more/actions/runs/33709314507
- Branch: `feat/R2-06-end-to-end-trace-propagation`
- Commit: `c417ca365f21428090a5ed1a374aaf8485778578`
- Mode: smoke (`DURATION=30s`, `WRITE_RPS=1`, `CONFIRM_VUS=4`)
- Topology: PostgreSQL 16, Redis 7, Uvicorn 2 workers, 1 outbox worker
- Comparator mode: `establish_baseline` only. Do not claim relative P95 regression passed.
- Artifact: `r2-06-write-path` (14 days)

Do not:

- compare write-path P95 with the 2026-09-02 read-mix load/spike evidence
- copy these smoke summaries into `load/baselines/` as a 5-10 minute baseline
- bind this workflow to PRs until two comparable stable load runs exist

## Smoke numbers

Idempotency (30s, 1 RPS):

- `http_req_failed` 0, `unexpected_5xx` 0, `duplicate_side_effects` 0
- `idempotency_replay_rate` 1.0 (31/31)
- write P95 23.3 ms, write P99 30.3 ms
- DB: 31 unique `k6-node-*` storage centers, no leftover PROCESSING outbox

Confirm-conflict (4 VUs, 4 iterations):

- 1 success / 3 conflicts (`confirmation_conflict_rate` 0.75)
- `http_req_failed` 0 after treating 409 as expected
- confirm P95 843 ms; mixed HTTP P95 4.88 s includes setup/login
- schedule `GS20260903001` ended `active`

Trace probe:

- `trace_id=trc-write-path-probe` is stable across success, retry, and dead-letter
- each worker execution mints a new `request_id`
- `parent_request_id=req-write-path-probe`
- independent worker log is empty: the probe delivers in-process before the worker starts, and k6 writes did not enqueue extra outbox rows

## Files

- `idempotency-summary.json`
- `confirm-conflict-summary.json`
- `comparison-report.json`
- `invariants.json`
- `trace-probe.json`
- `env-report.json`

Keep large API/worker logs in the 14-day CI artifact `r2-06-write-path`.
