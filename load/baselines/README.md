# Write-path k6 baselines

First successful 5-minute GHA write-path load (run 33710390070, 2026-09-03).

- Compare `idempotency-summary.json` only with another idempotency run.
- Compare `confirm-conflict-summary.json` only with another confirm-conflict run.
- Never compare these P95 values with the read-mix `load.js` / `spike.js` summaries.
- This first successful run only establishes a baseline. It must not claim relative regression passed.
- Source: https://github.com/justtodo123/LogisticSystem_more/actions/runs/33710390070
