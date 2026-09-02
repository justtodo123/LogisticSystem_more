---
plan_id: "R2-06"
title: 可观测性、容量测试与交付证据
status: in_progress
priority: P1
owner: justtodo123
created: 2026-08-25
updated: 2026-09-02
depends_on: ["R2-04B", "R2-05"]
---

# R2-06 — 可观测性、容量测试与交付证据

## 来源证据与当前行为

仓库缺少统一 request/trace/task ID、业务指标和系统级 HTTP 负载证据。CI 仅 SQLite pytest + 前端构建。观测裁剪已冻结：[D-R2-OBS](./decisions.md)、[D-R2-CI](./decisions.md)。

## 问题与目标

打通一次请求到 SQL/Redis/外部调用/Saga 步骤的追踪；用可复现的 load/spike 量化瓶颈与发布风险。不在本卡承诺绝对 QPS。

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

- 单次失败请求可按 request/trace/task ID 追到 SQL 或状态变化/补偿/死信。
- load 与 spike 各有一份可复现实验，含环境、数据量、worker、RPS、P95/P99、错误率。
- 结论写明已知限制，不夸大容量。
- CI 在 P1 拓扑上跑测试/迁移（与 R2-05 可同一流水线）。
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

- 状态：`in_progress`（2026-09-02）。第一刀已实现 request/trace/task ID、JSON 日志、SQL 注释、`/metrics`、k6 脚本与 `P1 load and spike` workflow。
- 本机：无 Docker / k6；load/spike **未执行**，不得标 `done`。
- 验证命令待本机 pytest 记录；GHA load 需 `workflow_dispatch`。
- P2 未做：soak、Grafana 全家桶、镜像安全扫描。
