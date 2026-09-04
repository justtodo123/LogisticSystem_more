# 项目交付与面试展示包

> 当前材料面向后端校招 / SP 面试。应用代码以 `main @ df025fb` 为冻结基线；本目录只整理交付事实、证据和展示路径，不重新开启 R2 开发。

## 先看哪一份

| 目标 | 材料 | 建议时长 |
|---|---|---:|
| 招聘者快速了解 | [项目一页卡](01-project-one-pager.md) | 1–2 分钟 |
| 核验数字和边界 | [Claim-to-evidence 台账](02-claim-evidence-ledger.md) | 3–5 分钟 |
| 解释系统设计 | [架构与核心流程](03-architecture-and-flows.md) | 5–10 分钟 |
| 准备技术追问 | [STAR 故事](04-star-stories.md) | 10–20 分钟 |
| 现场产品演示 | [无 Docker 演示 Runbook](05-demo-runbook.md) | 5–10 分钟 |
| 组织汇报/PPT | [展示提纲](06-presentation-outline.md) | 5/10/15 分钟 |

## 当前事实优先级

1. 代码与带日期的实验、CI/CD 证据；
2. [R2 收口记录](../plan_todo/20260904-R2-closeout.md) 与 [R2 计划总览](../plan_todo/README.md)；
3. `docs/` 当前规范和启动说明；
4. `My_doc/pre-optimization/` 历史材料（只能借用结构，不能直接借用事实）。

## 冻结基线与边界

- R2-00～R2-06 已完成，工程交付状态为 **Closeout ready**。
- 文档冻结点为 `main @ df025fb`（PR #42 合入后的主干）；镜像安全验收仍以不可变批次 `f9e08a4` / CD [33826520856](https://github.com/justtodo123/LogisticSystem_more/actions/runs/33826520856) 为准。
- P1 GHA 已验证 PostgreSQL 16 + Redis 7 + 多 worker 协议和故障切片，但这不是生产部署或生产 SLA。
- 本机没有 Docker/WSL/PostgreSQL/Redis；未执行本机 Compose、第一轮 02B E2E、预发或生产拉起。生产验证单独见 [post-r2-followups.md](../plan_todo/post-r2-followups.md)。
- 不把 SQLite 并发结果外推为 PostgreSQL 容量；不把幂等或外部通知说成 exactly-once；不直接比较 read-mix、spike、write、confirm、soak 的 P95；2h soak 不推出永久无泄漏。

## 已验证与未验证

**已验证**：迁移 fail-closed 基座、CAS 状态抢占、数据库幂等状态机、原子编号、Saga/outbox 恢复、RBAC/JWT 撤权、Redis 降级与跨 worker 限流、HTTP trace 传播、读混合 load/spike、独立写路径和确认场景、2h soak 绝对值、SBOM/Trivy 发布门禁。

**未验证**：本机或真实生产 Compose、02B 业务 E2E、生产回滚演练、Grafana/Prometheus/OTel 全家桶、跨 worker 指标聚合、定时镜像扫描、完整写+读组合容量、永久无泄漏结论。

## 权威运行入口

- 本地开发和前端 Mock： [docs/06-启动说明.md](../../docs/06-启动说明.md)
- API/错误/权限契约： [docs/07-规范说明.md](../../docs/07-规范说明.md)
- R2 最终验收： [20260904-R2-closeout.md](../plan_todo/20260904-R2-closeout.md)
- 后续生产验证： [post-r2-followups.md](../plan_todo/post-r2-followups.md)

旧 PPT、旧面试报告和旧演示指南位于 `pre-optimization/`，包含过时技术栈、角色/状态、测试数字和未经当前证据支持的效率表述；本目录材料不直接复用这些事实。
