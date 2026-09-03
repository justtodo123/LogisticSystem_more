# R2-06 write-path evidence

Small, redacted summaries from GHA write-path runs.

Do not compare these P95 values with the 2026-09-02 read-mix load/spike evidence.

## Current status

Two comparable 5-minute loads exist. The second run compared against `load/baselines` and passed.

- Baseline load: https://github.com/justtodo123/LogisticSystem_more/actions/runs/33710390070 (`b87db19`)
- Candidate load: https://github.com/justtodo123/LogisticSystem_more/actions/runs/33714192935 (`cca064e`)
- Independent worker trace: HTTP POST `/api/debug/write-path-probe` (`enqueue_source=http`, `worker_mode=independent`)
- HTTP-produced evidence: PR #36 merge `bf5c3a7`; main smoke https://github.com/justtodo123/LogisticSystem_more/actions/runs/33738039588
- Topology: PostgreSQL 16, Redis 7, Uvicorn 2 workers, 1 outbox worker
- Parameters: `DURATION=5m`, `WRITE_RPS=2`, `CONFIRM_VUS=8`

A 30s write-path PR correctness gate is live (PR #32, run 33715890853). It does not compare smoke P95 with this 5m pair. P2 soak smoke is a separate dispatch workflow; Grafana remains later.

## Candidate vs baseline

Idempotency:

- error_rate 0, unexpected_5xx 0, duplicate_side_effects 0
- replay 1.0, 600 unique nodes, 609 hashed idempotency rows, PROCESSING 0
- write P95 27.66 ms -> 26.35 ms (-4.7%)

Confirm-conflict:

- 1 success / 7 conflicts both runs
- confirm P95 836.7 ms -> 897.8 ms (+7.3%), under the 15% gate
- do not use mixed HTTP P95 (includes login/setup)

Independent worker trace (HTTP-produced):

- `POST /api/debug/write-path-probe` in the API process enqueues success/retry/dead-letter rows
- `enqueue_source=http`, `worker_mode=independent`, `passed=true`
- HTTP `trace_id=trc-write-path-probe` equals outbox `_trace.trace_id` and worker success/retry/dead-letter logs
- HTTP `request_id=req-write-path-probe` is not reused as the worker execution `request_id`
- retry uses two different execution `request_id`s; `parent_request_id` stays `req-write-path-probe`
- worker JSON log is non-empty (`write-outbox-worker.redacted.log`)
- do not treat this smoke as a 5-minute write-path candidate

## Files

- `idempotency-summary.json` / `confirm-conflict-summary.json` ? first load baseline copies
- `idempotency-candidate-summary.json` / `confirm-conflict-candidate-summary.json` ? second load
- `comparison-report.json`
- `invariants.json`
- `trace-probe.json`
- `env-report.json`

Keep large API/worker logs in the 14-day CI artifact `r2-06-write-path`.
