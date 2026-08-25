---
plan_id: "R2-06"
title: 可观测性、容量测试与交付证据
status: pending
priority: P1/P2
owner: 待认领
created: 2026-08-25
updated: 2026-08-25
depends_on: ["R2-04", "R2-05"]
---

# R2-06 — 可观测性、容量测试与交付证据

## 来源证据与当前行为

参考路线图确认仓库目前缺少统一 request/trace/task ID、业务指标、告警和系统级 HTTP 负载证据；已有 SQLite 分页/N+1 回归不能证明 RPS、P95/P99、峰值或长稳。CI 也需要补充 PostgreSQL/Redis 集成、迁移、镜像 smoke、安全扫描和定期性能门禁。

## 问题与目标

建立从一次请求到 SQL、Redis、外部调用、Saga/outbox 步骤的可观测链路，并用可复现的 load/stress/spike/soak 实验量化容量、瓶颈、优化收益和发布风险。

## 范围

- request ID/trace ID、用户/权限上下文、幂等 key、replan task ID、结构化 JSON 日志和敏感字段脱敏。
- OpenTelemetry（HTTP/SQLAlchemy/Redis/httpx）、Prometheus 指标、Dashboard、SLO/告警。
- Locust 或 k6 场景：认证、高频读、常规写、并发确认、全局调度、重规划、Redis 故障、AI 超时、spike、2～8 小时 soak。
- CI/CD 静态检查、依赖/secret scan、迁移、集成测试、镜像安全、部署后健康检查和性能定时任务。
- 架构图、Saga/状态机时序图、压测报告、故障演练报告和三份 STAR 故事。

## 非目标

- 不先编造绝对 QPS 或“生产级”结论；门禁必须来自基线实测。
- 不因接入监控就宣称业务正确性已完成；正确性依赖 R2-01～05。

## 依赖与进入条件

- R2-04 的身份/错误上下文和 R2-05 的 PostgreSQL + Redis 多 worker 拓扑可运行。
- 明确测试数据规模、硬件规格、请求分布、预热、持续时间和允许降级。

## 有序实施步骤

1. 统一日志字段和 trace propagation；为调度、重规划、幂等、通知和缓存定义核心指标。
2. 建立 Dashboard 与告警：错误率、P50/P95/P99、连接池、慢查询、锁等待、缓存命中/降级、任务积压/死信、AI 超时。
3. 选择 k6 或 Locust，保存脚本、配置、种子数据、原始 JSON/CSV 和报告。
4. 先做 baseline，再做 load/stress/spike/soak；每次只改变一个主要变量，定位 1～2 个真实瓶颈并复测。
5. 设置相对门禁：错误率 <1%、无未预期 5xx、P95 相比基线退化不超过 15%、无重复副作用、soak 无持续 RSS/连接泄漏；绝对值待实测后确定。
6. 将轻量门禁接入 PR，将完整性能和镜像/安全检查放入定时或发布流水线；输出面试证据材料。

## 验收标准

- 单次失败请求可按 request/trace/task ID 追到 SQL、外部调用、状态变化和补偿/死信。
- 报告完整记录环境、数据量、worker、请求分布、预热、持续时间、RPS、P95/P99、错误率和资源曲线。
- load/stress/spike/soak 至少各有一份可复现实验；结论明确已知限制，不夸大容量。
- CI 包含测试、迁移、镜像启动 smoke、依赖/secret scan；发布后有健康检查或回滚证据。
- 至少三份 STAR 故事引用真实数字、故障场景、设计权衡和链接产物。

## 验证命令

```bash
cd src/backend
python -m pytest -q -p no:cacheprovider
cd ../frontend
npm run build
# 负载工具命令、环境变量、阈值和报告路径写入实验记录
```

## 文档与问题记录同步

更新 `docs/` 监控/启动/发布说明、根 README 的真实能力表述、CI/CD 文档和第二轮 README；性能回归或故障注入问题按 `proced_problem` 记录。

## 回滚与恢复

观测组件异常不得阻塞核心业务（除明确安全审计场景）；性能门禁失败阻止发布但保留原始结果。删除实验资源前导出报告和日志。

## 完成记录

- 尚未开始。完成时填写工具版本、环境、各类测试结果、瓶颈优化前后数据、流水线链接、Commit/PR 和尚未覆盖的场景。
