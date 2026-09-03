# 20260903 R2-06 write-path baseline

## 元数据

- 日期：2026-09-03 Asia/Shanghai
- 执行人：Codex
- 层级：P1 增强（幂等写 / 并发确认 / outbox trace），不是读混合 load/spike 的替代
- Git 分支：feat/R2-06-end-to-end-trace-propagation
- Commit SHA：b87db196fe0461429c35a55209b5a565ed57a71b
- Workflow：`.github/workflows/p1-write-path.yml`（仅 `workflow_dispatch`）
- CI run URL：https://github.com/justtodo123/LogisticSystem_more/actions/runs/33710390070
- Smoke precursor：https://github.com/justtodo123/LogisticSystem_more/actions/runs/33709314507

## Schema 与数据来源

- Alembic：本卡无 schema 变更
- 数据库来源：GHA postgres:16-alpine + redis:7-alpine；init_users + init_demo_data
- 数据是否为合成/脱敏数据：是

## 环境

- GitHub Actions ubuntu-latest
- Python 3.13.15；k6 v2.2.0
- uvicorn `--workers 2 --no-access-log` on 127.0.0.1:18001
- 独立 outbox worker 1 个
- JWT_SECRET：CI-only placeholder；DB/Redis 示例口令 logistics/logistics

## 场景

- 短时 smoke（30s, 1 RPS, 4 confirm VUs）先排除脚本/数据问题
- 正式 load：5m，幂等写 2 RPS + 并发确认 8 VUs
- 服务端 Python 不变量：唯一节点、无重复确认成功、无残留 PROCESSING outbox
- 进程内 trace probe：success / 首次失败后 retry / dead-letter
- comparator 按场景分别比较；第一次成功只建立 baseline

## 命令

```text
gh workflow run p1-write-path.yml --ref feat/R2-06-end-to-end-trace-propagation -f mode=smoke
gh workflow run p1-write-path.yml --ref feat/R2-06-end-to-end-trace-propagation -f mode=load
```

## 原始结果与产物

- 成功 load run：33710390070，workflow_dispatch，2026-09-03T03:10:18Z，6m29s，conclusion success，head `b87db19`
- 产物名：`r2-06-write-path`（保留 14 天）
  - `idempotency-summary.json` 5272 B SHA-256 `aaa8360ecf484cd3f7cd492ac3156899d7b3659d209616908f6d3b4470bfea55`
  - `confirm-conflict-summary.json` 5351 B SHA-256 `54903f5eef4830e5ed4d6df39f383c5c10f8ca58f29b3ba3f2ed670bdbbe425f`
  - `comparison-report.json` 671 B SHA-256 `f954de6de55f078c5ca4298a72b18706076270a33c18d26176eee96a8c1f72d8`
  - `invariants.json` 554 B SHA-256 `e9654ea446cf8261917b89893265ef6be7aadab9aad86277c2bbff0cdc968491`
  - `trace-probe.json` 1730 B SHA-256 `d89822228bbd0b8f0c394d1e0f198882109496e76d2f72564cce93686a2030eb`
  - `write-api.redacted.log` 2313656 B SHA-256 `22b35e5b42267a47660b766bfe1e05e62fc7d89de283985871c8c6ce07647b56`
  - `write-outbox-worker.redacted.log` 0 B SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- 仓库小文件：`My_doc/plan_todo/experiments/r2-06-write-path/` 与 `load/baselines/`
- 幂等写（k6 write_duration，单位 ms）：iterations 600，replay 600/600，failed 0%，unexpected_5xx 0，duplicate_side_effects 0，P95 27.66，P99 73.16
- 并发确认：8 requests，1 success / 7 conflict，unexpected_5xx 0，confirm P95 836.7 ms；不要把含 login/setup 的混合 HTTP P95 4.88s/3.74s 当成确认 P95
- DB：600 个唯一 `k6-node-*`；schedule `GS20260903001` status=active version=2；outbox PROCESSING=0
- Trace：`trc-write-path-probe` 贯穿 success/retry/dead-letter；execution `request_id` 每次不同；`parent_request_id=req-write-path-probe`
- 先前失败（保留）：run 33708040433，confirm 409 被 k6 `http_req_failed` 计为失败，exit 99；已改为 expectedStatuses(200, 409)
- 脱敏检查：日志中的调用方幂等键为 SHA-256 指纹；依赖 label 不含 URL/token/user_id/order_id；大日志只留 CI artifact

## STAR 素材

1. 读混合容量：run 33607612662，8 RPS / spike 25 RPS，错误率 0%，混合 P95 9.81 ms / 9.63 ms。见 [20260902-R2-06-observability-baseline.md](./20260902-R2-06-observability-baseline.md)。
2. 幂等写：run 33710390070，5m / 2 RPS，600 次重放全部命中同一响应，DB 600 个唯一节点，无重复副作用。
3. 并发确认：同一 draft 8 个 contender，恰好 1 次成功、7 次 409/40901，schedule 最终 active。
4. Trace 连续性：同一 `trace_id` 覆盖 delivered / retry-then-delivered / dead-letter；HTTP `request_id` 与 worker execution `request_id` 不同。

## 结论

- 状态：写路径第一次 5m load 已建立 baseline。这不是相对回归通过，也不是读混合 load/spike 的替代证据。
- 已知限制：GHA ubuntu 单机回环，不是生产容量；`/metrics` 为进程内计数；独立 outbox worker 日志为空（probe 在 worker 启动前进程内投递，k6 写路径未追加 outbox）；本次 invariants 按 `idem-` 前缀查幂等行得到 0，业务无重复副作用以 600 个唯一节点为准。
- 未做：第二次可比 load、写路径 PR 门禁、跨 worker 指标聚合、soak、Grafana 全家桶、镜像安全扫描。
