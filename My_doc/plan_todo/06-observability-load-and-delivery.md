---
plan_id: "R2-06"
title: 可观测性、容量测试与交付证据
status: done
priority: P1
owner: justtodo123
created: 2026-08-25
updated: 2026-09-03
depends_on: ["R2-04B", "R2-05"]
---

# R2-06 — 可观测性、容量测试与交付证据

## 来源证据与当前行为

仓库已有 HTTP request/trace/task ID、结构化 JSON 日志、`/metrics` 核心计数，以及 PostgreSQL + Redis + 双 worker 上的读混合 load/spike 证据。本分支开始落地 outbox/worker 同 `trace_id`、依赖级观测、幂等写/并发确认脚本与 baseline comparator；跨 worker 指标聚合、Grafana 全家桶仍不在 P1 完成口径内。观测裁剪已冻结：[D-R2-OBS](./decisions.md)、[D-R2-CI](./decisions.md)。

## 问题与目标

先闭合 HTTP 观测基线与可复现的读混合 load/spike；outbox/worker 追踪、依赖级观测和写入/并发确认容量验证按后续增强推进。不在本卡承诺绝对 QPS，也不宣称已完成完整端到端观测与业务全路径容量验证。

## 范围（P1 最小集）

- request ID / trace ID / 用户与权限上下文 / 幂等 key / replan task ID；结构化 JSON 日志；敏感字段脱敏。
- 核心计数（错误率、确认冲突、幂等命中、outbox 积压/死信、缓存命中/降级）。可用 `/metrics` 或日志聚合，**不强制** Grafana。
- k6 或 Locust：认证、高频读、常规写、并发确认；一份 load + 一份 spike，各 5～15 分钟。
- CI：P1 环境上的测试 + 迁移；PR 上轻量门禁。
- 三份 STAR 故事引用 P0/P1 真实验证。

## 非目标（P2，不阻塞本卡 done）

- 2～8 小时 soak、完整 OpenTelemetry Collector + Prometheus + Grafana 全家桶、镜像安全扫描定时任务。
- 不编造绝对 QPS 或“生产级”结论。

## 依赖与进入条件

- R2-04B 身份/权限上下文与 R2-04A 错误上下文可用；R2-05 拓扑可运行（否则本卡不能标 `done`）。
- 明确测试数据规模、硬件规格、请求分布、预热、持续时间。

## 有序实施步骤

1. 统一日志字段和 ID 传播；为调度、重规划、幂等、通知、缓存打点。
2. 暴露核心指标；Dashboard/告警若环境不够则记录“日志可查 + 指标端点”，不强上 Grafana。
3. 选定 k6 或 Locust，保存脚本、种子、原始 JSON/CSV。
4. 先 baseline，再 load、再 spike；每次只改一个主要变量。
5. 相对门禁：错误率 <1%、无未预期 5xx、P95 相对基线退化不超过 15%、无重复副作用。绝对值待实测后写，不预填。
6. 轻量门禁进 PR；输出 STAR 材料。soak 单独立项为 P2。

## 验收标准（P1）

- HTTP 失败请求可按 request/trace/task ID 关联响应与日志；outbox/worker 的同一 `trace_id` 由集成测试覆盖到 retry/dead-letter。不把 Grafana 全链路或跨 worker 聚合当作已完成。
- load 与 spike 各有一份可复现读混合实验，含环境、数据量、worker、RPS、P95/P99、错误率。幂等写/并发确认是独立场景，不并入混合 P95。
- 结论写明已知限制，不夸大容量，不宣称已完成完整端到端观测与业务全路径容量验证。
- CI 在 P1 拓扑上跑测试/迁移（与 R2-05 可同一流水线）；baseline comparator 可执行，PR 性能门禁另议。
- 至少三份 STAR 引用真实数字和产物链接。

## 验证命令

```bash
cd src/backend
python -m pytest -q -p no:cacheprovider
cd ../frontend
npm run build
# 负载工具命令、阈值、报告路径写入 experiments/
```

## 文档与问题记录同步

更新 `docs/` 监控/启动说明、根 README 真实能力表述、CI 文档和第二轮 README。

## 回滚与恢复

观测组件异常不得阻塞核心业务。性能门禁失败阻止发布但保留原始结果。删除实验资源前导出报告。

## 完成记录

- 状态：`R2-06 P1 done：完成 HTTP 观测基线及读混合 load/spike 证据；HTTP 产生的独立 worker trace、依赖级观测、写入/并发确认压测已有证据；跨 worker 指标聚合仍列为后续增强，不宣称已完成完整端到端观测与业务全路径容量验证。`（2026-09-02）。观测基线 PR #27/#28/#29；成功 load/spike GHA run 33607612662，head `3b4a273`。
- Load 5m / 8 RPS 读混合 + 1 RPS login：http_req_failed 0%，dropped 0，k6 混合 P95 9.81 ms；login 路径 P95 290 ms。
- Spike 约 5m / 峰值 25 RPS：http_req_failed 0%，dropped 0，k6 混合 P95 9.63 ms。
- 产物：`r2-06-load-spike` artifact；详见 [20260902-R2-06-observability-baseline.md](./experiments/20260902-R2-06-observability-baseline.md)。
- P2：2h soak 已登记（run 33720629269）；Grafana 全家桶、镜像安全扫描仍未做。
- 写路径是独立场景，不并入 2026-09-02 读混合 P95。第一次 5m load 建立 baseline（run 33710390070）。第二次相同参数 candidate（run 33714192935）相对回归通过：幂等写 P95 -4.7%，确认 P95 +7.3%。独立 worker 日志证明同一 `trace_id` 覆盖 success/retry/dead-letter。不宣称业务全路径容量验证。
- 幂等写：http_req_failed 0，unexpected_5xx 0，重放 600/600，写 P95 27.66 ms / P99 73.16 ms；DB 600 个唯一 `k6-node-*`，无重复副作用，无残留 PROCESSING outbox。
- 并发确认：8 个 contender，1 次成功 / 7 次冲突，unexpected_5xx 0；confirm P95 836.7 ms（不要用含 login 的混合 HTTP P95）；schedule `GS20260903001` 最终 active。
- Trace probe：HTTP POST `/api/debug/write-path-probe` 产生 outbox（`enqueue_source=http`）；独立 worker 消费 success/retry/dead-letter。HTTP `trace_id=trc-write-path-probe` 贯穿 API、outbox `_trace` 与 worker 日志；每次 execution 新 `request_id`；`parent_request_id=req-write-path-probe`。证据：PR #36 merge `bf5c3a7`，main smoke run 33738039588。
- 写路径产物：artifact `r2-06-write-path`（14 天）；小文件见 [r2-06-write-path](./experiments/r2-06-write-path/README.md) 与 [20260903-R2-06-write-path-baseline.md](./experiments/20260903-R2-06-write-path-baseline.md)。跨 worker 指标聚合、Grafana 全家桶仍未完成。轻量 PR 门禁已合入 PR #32（merge 4f29d1a），首次 PR smoke run 33715890853 通过：mode=pr_correctness，p95_regression_ok=null，独立 worker trace_id=trc-write-path-probe。P2 soak smoke 已在 main 上跑通：run 33717505441，8m / 4 RPS，33 个样本，error_rate 0，unexpected_5xx 0，RSS 1.206x。这只证明采样器可跑，不断言无泄漏，不把 soak P95 与 5m 读混合或写路径 P95 比较。2 小时 soak 已跑通：run 33720629269，2h / 4 RPS，480 个样本，error_rate 0，unexpected_5xx 0，dropped 0；预热后 RSS 387864 KB -> 388464 KB（1.002x）。不断言永久无泄漏，不把 soak P95 与 5m 读混合或写路径 P95 比较。Grafana 全家桶、镜像扫描、跨 worker 指标聚合仍未做。小文件见 experiments/r2-06-soak/ 与 20260903-R2-06-p2-soak.md。
