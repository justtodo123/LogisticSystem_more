# R2-06 write-path evidence

This directory holds small, redacted summaries after a real GHA write-path run.

Current status: workflow exists (`.github/workflows/p1-write-path.yml`, `workflow_dispatch` only). No formal GHA write-path run has been recorded yet.

Do not:

- compare write-path P95 with the 2026-09-02 read-mix load/spike evidence
- claim relative regression passed on the first successful run
- bind this workflow to PRs until two comparable stable runs exist

After a successful run, copy these files here if they are small and redacted:

- `idempotency-summary.json`
- `confirm-conflict-summary.json`
- `comparison-report.json`
- `invariants.json`
- `trace-probe.json`
- `env-report.json`

Keep large API/worker logs in the 14-day CI artifact `r2-06-write-path`.
