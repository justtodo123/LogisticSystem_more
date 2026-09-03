# 20260902-R2-06-observability-baseline

## 元数据

- 计划 ID：R2-06
- 计划/决策版本：D-R2-OBS / D-R2-CI
- 日期与时区：2026-09-02 Asia/Shanghai
- 执行人：Codex
- 层级：P1（观测基线 + GHA load/spike）
- Git 分支：main
- Commit SHA：3b4a273c7b1a4fa04a730107e1222dba89cb2903
- PR URL：https://github.com/justtodo123/LogisticSystem_more/pull/29
- CI run URL：https://github.com/justtodo123/LogisticSystem_more/actions/runs/33607612662

## Schema 与数据来源

- Alembic：本卡无 schema 变更
- 数据库来源：GHA postgres:16-alpine + redis:7-alpine；init_users + init_demo_data
- 数据是否为合成/脱敏数据：是

## 环境

- GitHub Actions ubuntu-latest
- Python 3.13；k6 via grafana/setup-k6-action
- uvicorn `--workers 2 --no-access-log` on 127.0.0.1:18001
- JWT_SECRET：CI-only placeholder；DB/Redis 示例口令 logistics/logistics

## 场景

- 统一 X-Request-ID / X-Trace-ID / X-Task-ID
- JSON 日志 + 敏感字段脱敏 + SQL 注释
- `/metrics` 核心计数
- k6 load：setup JWT 复用；8 RPS 读混合（health/me/orders/metrics）+ 1 RPS login；5m
- k6 spike：读混合升到 25 RPS + 1 RPS login；约 5m

## 命令

```text
gh workflow run p1-load.yml --ref main -f load_duration=5m -f load_rps=8 -f spike_rps=25
```

## 原始结果与产物

- 成功 run：33607612662，workflow_dispatch，2026-09-02T08:13:55Z，10m55s，conclusion success，head `3b4a273`
- 产物名：`r2-06-load-spike`（保留 14 天）
  - `load-summary.json` 5550 B SHA-256 `6560f108a14fed69934f1afb8bede19c50eba4f68532369b87d89ac763f0638d`
  - `spike-summary.json` 4115 B SHA-256 `0b02defff181431c8bfa344d3ed21da447f0ce24b5d006a158f95120ab0dce83`
  - `load-api.log` 4090012 B SHA-256 `1ad51f0bc2b982c417c6b53f22e2e1e1b944219a2bcd39165fc6df6d7df8f780`
- Load（k6 混合 HTTP，单位 ms）：http_reqs 9906（32.95/s），iterations 2702（8.99/s），failed 0%，dropped 0，checks 12607/12607，P50 3.29，P95 9.81，max 371.07
- Spike（k6 混合 HTTP，单位 ms）：http_reqs 13529（45.00/s），iterations 4710（15.67/s），failed 0%，dropped 0，checks 4409/4409，P50 3.31，P95 9.63，max 299.73
- 应用 JSON 日志分路径（load+spike 合计，ms）：login n=604 P50 282.61 P95 290.18 P99 298.15；`/api/auth/me` n=6810 P95 13.19 P99 15.68；`/api/orders` n=6810 P95 12.37 P99 14.85
- 先前失败（保留）：run 33598168488 每迭代 bcrypt 登录，混合 P95 10.15s，exit 99；run 33604463684 setup() `__ITER` ReferenceError，exit 107
- 脱敏检查：脚本不含真实凭据；GHA 使用示例口令

## STAR 素材

1. 并发确认冲突：R2-01 CAS，同 draft 第二次确认 HTTP 409 / 40901，PR #8。
2. 幂等重放：R2-02A 数据库状态机，同 key 重放原响应，PR #10/#12。
3. P1 编号规模：100,000 claims，GHA run 33581256635，P95 158.342 ms，193.6 claims/s。
4. P1 HTTP load/spike：run 33607612662，读混合 8 RPS / spike 25 RPS，错误率 0%，k6 混合 P95 9.81 ms / 9.63 ms；login 路径 P95 290 ms（bcrypt）。不把混合 P95 说成登录 P95。

## 结论

- 状态：`R2-06 P1 done：完成 HTTP 观测基线及读混合 load/spike 证据；端到端 outbox trace、依赖级观测、写入/并发确认压测和跨 worker 指标聚合列为后续增强，不宣称已完成完整端到端观测与业务全路径容量验证。`
- 已知限制：GHA ubuntu 单机回环，不是生产容量；`/metrics` 为进程内计数；k6 默认摘要当时无 p(99)，P99 来自应用 JSON 日志；混合 P95 被 health/metrics 拉低。本文件只记录读混合 load/spike。HTTP -> outbox -> worker 同一 `trace_id`、幂等写与并发确认是独立写路径证据，见 [20260903-R2-06-write-path-baseline.md](./20260903-R2-06-write-path-baseline.md)，不可与本文件读混合 P95 比较。
- P2 未做：soak、Grafana 全家桶、镜像安全扫描。
