# 第二轮优化计划

> **定位**：面向大厂后端校招 SP 的第二轮工程化优化路线；本目录是第二轮计划的唯一实时状态入口。
> **参考依据**：[大厂后端 SP 标准差距与优化路线图](../reference/大厂后端SP标准差距与优化路线图.md)。
> **决策基线**：[decisions.md](./decisions.md)（协议冻结 `v2026-08-25-r2-freeze`；治理增补 `v2026-08-25-r2-governance`）。冲突时：代码与验证证据 > 版本化决策 > 本 README > 单卡正文。
> **第一轮归档**：[第一轮优化计划](../post_plan/第一轮优化计划/)。第一轮文档只追溯，不承担第二轮实时状态。
> **修订日期**：2026-09-04。R2 **工程交付完成 / Closeout ready**。冻结记录：[20260904-R2-closeout.md](./20260904-R2-closeout.md)。最终文档冻结点为 `main` @ `df025fb`（PR #42）；不可变镜像验收基线仍为 PR #40 / `f9e08a4` / CD [33826520856](https://github.com/justtodo123/LogisticSystem_more/actions/runs/33826520856)，零 exception。生产验证与 P2 增强见 [post-r2-followups.md](./post-r2-followups.md)，不计入 R2 阻断项；交付与面试材料见 [../delivery/README.md](../delivery/README.md)。

## 阅读与状态规则

1. 先读本 README 和 [decisions.md](./decisions.md)，再读对应计划卡。
2. 第二轮只做“可验证闭环”：每个能力必须同时有实现、测试、运行环境和可复现实验记录；配置文件存在不等于验收完成。
3. 状态使用 `pending`、`in_progress`、`blocked`、`needs_decision`、`mitigated`、`done`；只有 `done` 计入完成。
4. **P0 不得**因本机无 Docker / PostgreSQL / Redis 标 `blocked`。**P1** 在外部拓扑未就绪时必须标 `blocked`，不得用 SQLite 结果替代。
5. 计划阶段不虚构吞吐、P95/P99、并发成功率、commit/PR 或生产拓扑结果；所有结果须附环境、数据规模、日期、命令和产物。
6. 正式 schema 由 R2-00A 建立的 Alembic 单一 head 管理；错误响应由 R2-04A 的 registry / envelope 管理，后续业务卡不得各建一套。

## 执行切分

| 层级 | 何时开始 | 环境 | 包含 |
|---|---|---|---|
| **治理基线** | **已完成** | Git + 文档审查 | `00`：My_doc 追踪、证据模板、计划依赖和真实发布记录 |
| **P0 基础** | **已完成** | Windows + Python 3.13 + SQLite + pytest | `00A` 与 `04A`：迁移单一真相源、错误/Session 基座 |
| **P0 协议** | `00A` + `04A` done 后 | 同上 | `01 → 02 → 03`；`04B` 可与主链并行 |
| **P1 外部拓扑** | P0 协议稳定，且 P1 环境三条路径之一就绪 | GHA Postgres/Redis（首选）或 Linux VM / 云主机 Docker Engine | `05`；随后 `06` |
| **P2** | 不阻塞面试材料 | 同上 | soak、Grafana、镜像安全扫描 |

P0 证明的是：迁移/错误基座、状态抢占、幂等状态机、编号、Saga/outbox **协议正确**。

P1 证明的是：同一协议在 PostgreSQL + Redis + 多 worker 下仍正确。

SQLite 100 并发 **不是** PostgreSQL 多 worker 证明。

## 计划总览

| ID | 层级 | 优先级 | 状态 | 计划 | 关键出口 |
|---|---|---|---|---|---|
| 00 | 治理 | P0 | done | [第二轮执行治理与证据基线](./00-execution-governance.md) | My_doc 追踪、证据和依赖已验证；PR #3 与 CI 证据已回填 |
| 00A | P0 基础 | P0 | done | [Alembic 迁移基线与 Schema 真相源治理](./00A-alembic-migration-baseline.md) | PR #5 / CI 通过并合并；fresh/legacy、单 head、schema parity 已验证 |
| 04A | P0 基础 | P0 | done | [领域错误、统一响应契约与数据库会话回滚](./04A-error-contract-and-db-session.md) | PR #6 / CI 通过并合并；registry、envelope、detail 兼容与 rollback 已验证 |
| 01 | P0 | P0 | done | [关键状态转移并发控制](./01-concurrency-state-transitions.md) | PR #8 / CI 通过并合并；并发确认最多一次成功且无重复副作用 |
| 02 | P0 | P0 | done | [原子幂等与业务编号](./02-idempotency-and-code-generation.md) | R2-02A/B 经 PR #10 / #11 / #12、CI 验证并合并；数据库幂等状态机与原子号段协议完成 |
| 03 | P0 | P0 | done | [重规划 Saga 与可靠通知](./03-replan-saga-and-outbox.md) | PR #15 / CI 通过并合并；Saga/outbox 协议与本地故障注入已验证 |
| 04B | P0 并行 | P0 | done | [RBAC、JWT 撤权与前端权限](./04B-rbac-jwt-and-frontend.md) | PR #16 / CI 通过并合并；权限矩阵、token version、前后端 can() 已验证 |
| 05 | P1 | P1 | done | [PostgreSQL、Redis 与故障韧性](./05-postgresql-redis-resilience.md) | PR #18/#20/#21/#23 已合并；main CI/CD 与 100k GHA scale run `33581256635` 已验证；PR #25 CI run 33589202969 四个 job 全绿 |
| 06 | P1/P2 | P1 | done | [可观测性、容量测试与交付证据](./06-observability-load-and-delivery.md) | P1：HTTP 观测基线 + 读混合 load/spike（run 33607612662）。写路径两次 5m load 可比（PR #31）。轻量 PR 正确性门禁已合入 PR #32（run 33715890853）。P2 soak smoke（run 33717505441）与 2h soak（run 33720629269）已跑通。P2 镜像发布扫描门禁已由 PR #40 / CD run 33826520856 验收通过，零 exception；backend 仅剩 MEDIUM CVE-2026-13346（pip 26.1.2，report-only）。Grafana / 跨 worker 指标仍未做 |

## 依赖主链

```text
R2-00 (done)
├── R2-00A (done)
└── R2-04A (done)

R2-00A + R2-04A -> R2-01 (done) -> R2-02 (done) -> R2-03 (done)
R2-00A + R2-04A -> R2-04B (done)
R2-00A + R2-01 + R2-02 + R2-03 -> R2-05 (done)
R2-04B + R2-05 -> R2-06 (done)
```

## 第二轮收口

**工程交付完成 / Closeout ready（2026-09-04）**：R2-00～R2-06 均为 `done`。最终基线见 [20260904-R2-closeout.md](./20260904-R2-closeout.md)。P2 镜像发布扫描门禁已在 `main` 上真实 CD 通过，未登记 exception。本机无 Docker 不等于 R2 未完成。

**R2 已关闭。** 后续只走 [post-r2-followups.md](./post-r2-followups.md)（生产验证、可选 P2），不回写为本轮未完成。不要把 soak P95 与读混合/写路径 P95 比较，不要把 8m smoke 当成 soak baseline。

生产验证与可选 P2 的完整待办已迁到 [post-r2-followups.md](./post-r2-followups.md)，不再作为本 README 的 R2 未完成项。

## 当前证据边界

- 已有 SQLite、本地 HTTP smoke、单元/API/集成测试和路线查询次数回归；这些不等价于 PostgreSQL 多 worker 容量证明。
- 本机（2026-08-25）：Win11 家庭版，Ryzen 7 7840H，16GB（空闲曾约 1.6GB），Python 3.13.3，Node v24.12.0，Git 2.49；**无** Docker / WSL / PostgreSQL / Redis / k6 / Locust。
- R2-00A 已完成 Alembic 单 head、正式启动 migration gate、运行时 DDL 移除和 SQLite schema parity。R2-05 第一刀至第三刀已合入 PR #18 / #20 / #21 / #23：PostgreSQL 协议复跑、双进程 HTTP、Redis pause/恢复、worker 重启幂等重放、outbox lease reclaim、deadlock/serialization 有限重试、连接池超时、Postgres 短暂断连、专用库备份恢复。100,000 编号已由 `workflow_dispatch` run `33581256635` 实测通过，跨 worker 登录限流已由 PR #25 CI 验证：Redis 共享计数、pause 降级与恢复后重新共享。
- 第一轮 02B Docker E2E 仍为 `mitigated`，不是本轮 R2 阻断条件；生产环境验证仍按 [post-r2-followups.md](./post-r2-followups.md) 单独登记。
- `My_doc/` 已正式纳入追踪；小型脱敏报告可入库，预览、依赖目录、数据库、日志、原始 CI 输出、待脱敏 Office 二进制、可再生成的历史演示输出与实验大产物继续忽略。

## 阶段出口与交付物

- 治理（00）：追踪边界、版本化 decisions、实验模板、无环依赖、真实 commit/PR 记录。
- P0 基础（00A/04A）：Alembic fresh/legacy/parity 证据；错误 registry、兼容 envelope、rollback/脱敏测试。
- P0 协议（01～03）：独立 Session 并发/故障注入测试、实验记录。
- P0 并行（04B）：PR #16 / CI 通过并合并；权限矩阵、`/me` 权限、token version 与前端 `can()` 已验证。
- P1（05）：PostgreSQL + Redis + 多 worker 集成报告（GHA 或 VM/云）。
- P1/P2（06）：request/trace/task ID、load/spike 报告；STAR 故事引用真实验证。P2 镜像发布扫描门禁已通过（PR #40 / CD 33826520856，零 exception）。生产部署验证与 Grafana 全家桶未做。

每次完成一个小目标，按 [Git 协作规范](../../docs/Git协作规范.md) 创建分支并独立提交；完成后回写本 README 和对应计划卡的真实完成记录。未经明确授权不自动 stage、commit、push 或创建 PR。
