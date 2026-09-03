# Write-path k6 baselines

This directory is empty until a successful GHA write-path run is copied here.

- Compare `idempotency-summary.json` only with another idempotency run.
- Compare `confirm-conflict-summary.json` only with another confirm-conflict run.
- Never compare these P95 values with the read-mix `load.js` / `spike.js` summaries.
- The first successful run only establishes a baseline. It must not claim relative regression passed.
