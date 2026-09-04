# 智能物流调度平台：项目一页卡

## 30 秒项目介绍

我实现并工程化改造了一个 FastAPI + Vue 3 智能物流调度平台，覆盖订单、车辆、调度确认、异常重规划、AI 辅助、报表、ERP、权限和审计。第二轮优化重点不是继续堆功能，而是补齐后端一致性与交付能力：用 Alembic 治理 schema，用 CAS 避免并发重复确认，用数据库状态机实现跨 worker 幂等，用 Saga + transactional outbox 支撑失败恢复，并在 PostgreSQL、Redis、多 worker 的 GitHub Actions 拓扑中验证故障韧性。发布侧采用 SBOM + Trivy fail-closed 门禁，阻断漏洞修复后以零 exception 发布不可变 SHA 镜像。

## 90 秒项目介绍

这个项目的业务主线是“订单进入系统后，经过资源匹配、调度方案生成、人工确认、配送执行和异常重规划，最终形成报表、通知与审计记录”。技术栈是 FastAPI、SQLAlchemy 2.0、Pydantic v2、Vue 3、TypeScript、Element Plus 和 Vite；开发默认 SQLite，P1 验证使用 PostgreSQL 16、Redis 7、两个独立 Uvicorn worker 和一个独立 outbox worker；8 workers 只用于 100,000 次编号 claim 专项实验。

我在第二轮重点解决了五类工程问题。第一，清理多 Alembic head、运行时建表和历史库漂移，建立单一迁移真相源与 fail-closed release gate。第二，把确认类 read-check-write 改成条件更新 CAS，确保并发抢占先于副作用。第三，将进程内幂等升级为数据库 `PROCESSING/SUCCEEDED/FAILED/EXPIRED` 状态机，并用原子号段替换 `max+1`。第四，用持久化 Saga、lease、claim token、stale-token fencing 和 transactional outbox 支持重试、死信和 worker 恢复。第五，补齐 request/trace/task ID、结构化日志、负载与故障实验，以及“构建—SBOM—扫描—门禁—推送”的安全发布链路。

验证结果按场景记录：SQLite 独立 Session 下 20/100 个确认竞争者最多一个成功；P1 PostgreSQL 8 workers 完成 100,000 次唯一且连续的编号分配；独立写路径 600/600 幂等重放成功且无重复副作用；2 小时 soak 无请求错误且预热后 RSS 约 1.002x；镜像门禁在零 exception 下通过并发布固定 SHA tag。这些是工程验收证据，不等同于生产部署、生产 SLA 或 exactly-once 承诺。

## 业务与职责

### 业务范围

- 订单、车辆、司机、物流节点和调度计划管理；
- 可插拔调度策略、Top-K 候选与方案解释；
- 调度确认、到货确认、异常重规划和人工干预；
- AI 自然语言解析与安全降级；
- SLA、成本、异常和运力报表；
- 通知、ERP 导入导出、Webhook、审计与 RBAC。

### 我的主要工作

- 设计并落地数据库迁移、错误契约、事务和敏感信息脱敏基座；
- 解决确认流程并发竞争、跨 worker 幂等和业务编号冲突；
- 建立 Saga/outbox 的持久化恢复协议；
- 完成 JWT 撤权、细粒度权限和 Redis 登录限流；
- 在 PostgreSQL/Redis/多 worker 拓扑中进行故障、规模和恢复验证；
- 建立可观测性、负载回归、SBOM/Trivy 镜像门禁和可审计发布证据。

## 当前技术架构

| 层 | 技术与职责 |
|---|---|
| 前端 | Vue 3 + TypeScript + Element Plus + Vite；页面、composable、领域 API、权限 `can()`、Mock 开关 |
| API | FastAPI；统一 `{code, message, data, meta}` 契约、JWT/RBAC、request/trace/task ID |
| 业务 | services + algorithms；状态机、调度、重规划、AI 确认闸门、报表和 ERP |
| 一致性 | SQLAlchemy 2.0、CAS、数据库幂等状态机、原子号段、Saga、transactional outbox |
| 数据与缓存 | SQLite（开发）/ PostgreSQL 16（P1 验证）；Redis 7 用于普通缓存和共享登录限流，故障时可见降级；数据库幂等不依赖 Redis |
| 交付 | GitHub Actions、k6、CycloneDX SBOM、Trivy、版本化扫描 policy、GHCR SHA tag |

## 简历成果表述

以下表述均可从[证据台账](02-claim-evidence-ledger.md)追溯：

- 治理 SQLAlchemy/Alembic schema 漂移问题，收敛多 head、运行时 DDL 和混合 SQLite 历史状态，建立单一 head、数据库状态分类与 fail-closed release migration gate。
- 将调度/到货/AI 确认由 read-check-write 改造为条件更新 CAS；在 20/100 个独立 Session 竞争场景下均保持最多一个成功者，且失败请求不产生重复副作用。
- 设计数据库幂等状态机与 payload fingerprint/claim token/exact response replay，独立写路径完成 600/600 重放且数据库仅产生 600 个唯一业务节点，无残留 `PROCESSING` outbox。
- 用条件更新号段替代进程内序号和 `max+1`；在 PostgreSQL 16、8 workers 的编号专项实验下完成 100,000 次唯一、连续、可恢复分配，吞吐 193.6 claims/s，P95 158.342 ms；该数字不代表完整服务容量。
- 实现持久化重规划 Saga 与 transactional outbox，通过 lease、token fencing、retry/dead-letter 和独立 worker Session 覆盖故障恢复；外部发送端无幂等能力时明确保持 at-least-once 语义。
- 建立 request/trace/task ID 与结构化脱敏日志、相对性能回归门禁，以及 SBOM + Trivy fail-closed 镜像发布门禁；修复基础镜像阻断项后以零 exception 发布 backend/frontend 固定 SHA 镜像。

## 面试可重点展开的五个问题

1. 为什么 Alembic `stamp head` 会掩盖风险，如何分类 fresh/legacy/mixed/drift 数据库？
2. 为什么 CAS 必须发生在通知、事件和关联对象更新之前？
3. 为什么 Redis 不能承担幂等正确性，exact response replay 如何落库？
4. Saga/outbox 如何处理 lease 超时、旧 worker 恢复和外部重复投递？
5. 如何区分 load、spike、write、confirm、soak，并避免用 CI 结果冒充生产容量？

详见[架构与核心流程](03-architecture-and-flows.md)和[STAR 故事](04-star-stories.md)。

## 已验证 / 未验证边界

| 已验证 | 未验证或不能外推 |
|---|---|
| R2-00～R2-06 工程实现和自动化验收 | 本机 Compose、第一轮 02B E2E、预发或生产拉起 |
| PostgreSQL 16 + Redis 7 + 多 worker GHA 拓扑 | 真实生产流量、生产 SLA 和生产数据库迁移实演 |
| 分场景的 CAS、幂等、编号、故障、load/spike/write/confirm/soak 结果 | 完整读写混合业务容量；不同场景 P95 的直接比较 |
| outbox 内部去重、租约回收与 stale-token fencing | 外部 SMTP/Webhook exactly-once 投递 |
| 2h soak 的错误率和 RSS 绝对值 | 永久无内存泄漏 |
| 发布时 SBOM/Trivy 门禁和零 exception 发布 | 定时扫描、Grafana/Prometheus/OTel、跨 worker 指标聚合 |

## 当前交付状态

- 应用代码冻结点：`main @ df025fb`。
- R2 镜像验收批次：`f9e08a499ba50987505e32d58b545a37c9543ef4`。
- backend 镜像：`ghcr.io/justtodo123/logisticsystem_more-backend:f9e08a499ba50987505e32d58b545a37c9543ef4`。
- frontend 镜像：`ghcr.io/justtodo123/logisticsystem_more-frontend:f9e08a499ba50987505e32d58b545a37c9543ef4`。
- 镜像扫描：backend 仅 1 个 MEDIUM report-only，frontend 无漏洞，blocked `[]`，exception `[]`。

完整冻结结论见 [R2 收口记录](../plan_todo/20260904-R2-closeout.md)。
