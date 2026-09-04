# R2-06 镜像发布扫描门禁证据

CD run 33826520856 在 `main` / `f9e08a4` 上 **通过**。未登记 exception。

不要把本目录当成生产部署证据。CD 只发布 GHCR；本机 compose / E2E 未做。

## Run

- URL: https://github.com/justtodo123/LogisticSystem_more/actions/runs/33826520856
- 触发：PR #40 合入 `main` 后的 CD（workflow_run）
- Branch: main
- Commit: f9e08a499ba50987505e32d58b545a37c9543ef4
- Artifact: `image-scan-f9e08a499ba50987505e32d58b545a37c9543ef4`（保留 14 天）
- Policy: `2026-09-03.1`
- Trivy: 0.56.2
- Docker: 28.0.4
- Exceptions applied: []

## Result

- policy-evaluation `passed`: true
- backend: debian forky/sid，`passed=true`，`blocked=[]`，`counts={MEDIUM: 1}`
- frontend: Alpine 3.24.1，`passed=true`，无漏洞
- `scan-status.json`: backend/frontend sbom+scan 均为 0
- `exception_count`: 0；`exceptions_applied`: []
- 唯一残留：CVE-2026-13346，包 pip，当前 `26.1.2`，建议 `26.2.0`，MEDIUM，report-only，不阻断，不登记 exception
- 审计 GHCR SHA：`ghcr.io/justtodo123/logisticsystem_more-backend|frontend:f9e08a499ba50987505e32d58b545a37c9543ef4`
- `latest` 不是审计/回滚依据

## Files（仅脱敏摘要）

- `policy-evaluation.json` 511 B SHA-256 `b18b0ea5b11439e5611593022e31149367f4c9b8dc0b00367e44e30fa28305e0`
- `env-report.json` 1482 B SHA-256 `5e358b89f7d0786a8e4db24025144544a801c9c4a467cc1acd23072171951aef`
- `scan-status.json` 72 B SHA-256 `2be61cd2ff909dc059fbde75adb5db49da19aca3abc39332e3f4d3d9e0adf427`

原始 `backend-trivy.json` / `frontend-trivy.json` / SBOM 只留 14 天 CI artifact，不入库。
历史阻断摘要（CD 33765319991 / debian 13.6）已从本目录移除，见 `docs/镜像扫描门禁-阻断证据与修复计划.md`。
