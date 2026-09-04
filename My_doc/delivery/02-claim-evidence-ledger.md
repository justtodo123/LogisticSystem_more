# Claim-to-evidence 台账

> 用途：面试、简历和汇报中的数字只从本表引用。每条结论必须同时保留“场景”和“边界”；没有来源的数字不写入公开材料。

## 使用规则

1. 先说问题、设计和取舍，再说数字；数字不能脱离环境、规模和场景。
2. `SQLite`、`PostgreSQL GHA`、`HTTP load`、`write`、`confirm`、`soak` 是不同证据层，不互相替代。
3. PR/CI/CD 证明某次自动化验收成功，不等同于真实生产部署或生产 SLA。
4. 幂等状态机减少重复执行，但业务副作用事务与最终 `mark_succeeded` 不是一个不可分割的 exactly-once 过程。
5. outbox 内部可以去重和 fencing；外部 SMTP/Webhook sender 无自身幂等能力时仍是 at-least-once。

## 核心工程结论

| ID | 面试可说结论 | 环境 / 规模 / 指标 | 主要证据 | 必须同时说明的边界 |
|---|---|---|---|---|
| MIG-01 | Alembic 收敛为单一正式 head，并建立 fresh、Alembic-managed legacy、known mixed SQLite、unknown/drift 等状态分类；release migration 对不支持状态 fail closed。 | SQLite fresh/legacy/parity 迁移测试；该阶段记录 `718 passed, 209 warnings`。 | [R2-00A 计划卡](../plan_todo/00A-alembic-migration-baseline.md)；`src/backend/alembic/versions/r2_00a_schema_convergence.py`；`src/backend/scripts/release_migrate.py`；PR [#5](https://github.com/justtodo123/LogisticSystem_more/pull/5)；CI `32932228092`。 | 这是迁移治理与自动化测试证据，不是本机 Docker 或生产数据库升级实演；禁止用 `stamp head` 掩盖未知状态。 |
| ERR-01 | 统一领域错误 registry、`{code,message,data,meta}` envelope、数据库 rollback/re-raise/close 和日志脱敏。 | HTTP/API/Session 测试；阶段性完整后端运行曾记录 `746 tests, 214 warnings`。 | [R2-04A 计划卡](../plan_todo/04A-error-contract-and-db-session.md)；`src/backend/core/errors.py`；PR [#6](https://github.com/justtodo123/LogisticSystem_more/pull/6)；CI `32948346709`、`32948669210`。 | 测试总数是带日期的阶段运行，不写成当前仓库固定总数；旧 `HTTPException.detail` 只是内部兼容输入。 |
| CAS-01 | 确认类流程采用 expected-state 条件更新，以 `rowcount` 判断抢占；CAS 先于包装、订单、事件和通知等副作用。 | SQLite 独立 Session；20 和 100 个 contender；最多一个成功，其余稳定冲突；无重复副作用。 | [R2-01 计划卡](../plan_todo/01-concurrency-state-transitions.md)；[并发实验](../plan_todo/experiments/20260827-R2-01-cas-state-transitions.md)；`src/backend/core/cas.py`；PR [#8](https://github.com/justtodo123/LogisticSystem_more/pull/8)；CI `33047947336`。 | SQLite 独立 Session 证明协议与副作用顺序，不是 PostgreSQL 多 worker 容量证明；不能直接称为生产并发验证。 |
| IDEM-01 | 幂等正确性由数据库状态机承担，Redis 只在成功提交后作 best-effort cache；支持 payload fingerprint、claim token 和 exact response replay。 | 20/100 个相同 key contender 仅一个 owner；同 key 不同 payload 返回 `40903`；处理中返回 `40902` + `Retry-After`。 | [R2-02 计划卡](../plan_todo/02-idempotency-and-code-generation.md)；[幂等实验](../plan_todo/experiments/20260828-R2-02A-idempotency-state-machine.md)；`src/backend/middleware/idempotency.py`；PR [#10](https://github.com/justtodo123/LogisticSystem_more/pull/10)、[#11](https://github.com/justtodo123/LogisticSystem_more/pull/11)；CI `33151979633`、`33157404527`。 | 不能称为 exactly-once；owner 执行业务副作用和最终成功标记之间仍需用恢复协议处理崩溃窗口。 |
| IDEM-02 | 独立 HTTP 写路径验证了幂等重放、无重复副作用和无残留处理中 outbox。 | PostgreSQL 16 + Redis 7 + 2 Uvicorn workers；5 分钟独立 write 场景；600/600 replay；写 P95 `27.66 ms`、P99 `73.16 ms`；DB 600 个唯一节点；unexpected 5xx 为 0。 | [写路径实验](../plan_todo/experiments/20260903-R2-06-write-path-baseline.md)；[R2-06 计划卡](../plan_todo/06-observability-load-and-delivery.md)；baseline run `33710390070`。 | write 指标不能与包含登录的 read-mix P95 或 confirm P95 直接比较；GHA 拓扑不是生产流量。 |
| CODE-01 | 使用 `code_ranges` 条件更新分配业务编号，替代进程内序号、LIKE prefix 和 `max+1`。 | SQLite 20/100 并发唯一；顺序 200 个 package code 唯一连续。P1 PostgreSQL 16、8 workers、100,000 claims：516.578 s、193.6 claims/s、P95 158.342 ms、P99 294.859 ms，unique/contiguous/resume 均通过。 | `src/backend/core/code_allocation.py`；[R2-02 计划卡](../plan_todo/02-idempotency-and-code-generation.md)；[R2-05 计划卡](../plan_todo/05-postgresql-redis-resilience.md)；GHA run [33581256635](https://github.com/justtodo123/LogisticSystem_more/actions/runs/33581256635)。 | 这是特定 GHA 数据库号段实验，不等于完整订单写链路吞吐或生产容量。 |
| SAGA-01 | 重规划任务持久化 step state、retry、manual-required、lease 和 claim token；stale-token fencing 防止旧 worker 恢复后覆盖新结果。 | focused HTTP/recovery、integration、outbox claim/lease 和 replan concurrency 测试覆盖 rollback、compensation、lease reclaim、stale claim rejection。 | [R2-03 计划卡](../plan_todo/03-replan-saga-and-outbox.md)；[Saga/outbox 实验](../plan_todo/experiments/20260829-R2-03-replan-saga-outbox.md)；`src/backend/services/replan_task_service.py`。 | 测试矩阵证明恢复协议，不代表真实生产 worker 重启或生产外部服务已验证。 |
| OUTBOX-01 | transactional outbox 与业务事务共同提交，独立 worker 使用短 Session、lease、token fencing、retry/dead-letter 和重复投递抑制。 | 记录有 101 个 outbox claim/lease focused tests、24 个 replan concurrency tests；完整阶段运行曾记录 908 backend tests。 | `src/backend/services/outbox_service.py`；`src/backend/scripts/outbox_worker.py`；[R2-03 计划卡](../plan_todo/03-replan-saga-and-outbox.md)。 | 内部 outbox 语义不等于外部 exactly-once；发送端无幂等 key 时，SMTP/Webhook 仍可能至少一次投递。 |
| AUTH-01 | 中央权限矩阵、`require_permission`、前端 `can()` 与 JWT `token_version` 共同实现权限控制和旧 token 撤权；未知角色 fail closed。 | Redis 健康时跨 worker 共享登录限流；pause 时安全降级并带 degraded metadata；恢复后重新共享。参数：5 attempts / 60 s，Redis 7 + 2 workers。 | [R2-04B 计划卡](../plan_todo/04B-rbac-jwt-and-frontend.md)；[跨 worker 限流实验](../plan_todo/experiments/20260902-R2-05-cross-worker-login-rate-limit.md)；PR [#16](https://github.com/justtodo123/LogisticSystem_more/pull/16)、[#25](https://github.com/justtodo123/LogisticSystem_more/pull/25)；CI [33589202969](https://github.com/justtodo123/LogisticSystem_more/actions/runs/33589202969)。 | Redis 故障时 fallback 是进程内计数，不能声称降级期间仍保持跨 worker 全局强一致限流。 |
| P1-01 | P0 协议在 PostgreSQL 16 + Redis 7 + 两个独立 Uvicorn worker + 独立 outbox worker 的 GHA service topology 中复跑，并覆盖重启、断连、超时和恢复切片。 | migration、CAS/idempotency/Saga、worker restart replay、outbox lease reclaim、Redis pause/recovery、deadlock/serialization 有限重试、pool timeout、PostgreSQL 短暂断连、备份恢复。 | [R2-05 计划卡](../plan_todo/05-postgresql-redis-resilience.md)；[故障恢复实验](../plan_todo/experiments/20260901-R2-05-fault-recovery.md)；PR [#25](https://github.com/justtodo123/LogisticSystem_more/pull/25)；main CI [33590407219](https://github.com/justtodo123/LogisticSystem_more/actions/runs/33590407219)；CD [33590735173](https://github.com/justtodo123/LogisticSystem_more/actions/runs/33590735173)。 | GHA service topology 是生产近似验证环境，不是预发/生产部署，也不能推出生产 RTO/RPO 或 SLA。 |

## 观测与性能场景

| 场景 | 环境与参数 | 结果 | 证据 | 正确解释 |
|---|---|---|---|---|
| Read mix | PostgreSQL 16 + Redis 7 + 2 workers；约 5 分钟；8 RPS reads + 1 RPS login | 9,906 requests；aggregate 32.95 req/s；失败 0%；混合 P95 9.81 ms；login JSON P95 约 290.18 ms | [观测基线实验](../plan_todo/experiments/20260902-R2-06-observability-baseline.md)；GHA run `33607612662` | 这是给定请求分布下的 HTTP 混合结果；aggregate request 数包含 k6 请求，不把 9 RPS 直接等同 aggregate 指标。 |
| Spike | 同一 P1 拓扑；约 5 分钟；峰值约 25 RPS reads + 1 RPS login | 13,529 requests；约 45 aggregate req/s；失败 0%；混合 P95 9.63 ms | 同上 | 只说明该 spike 脚本下没有失败/丢弃，不能称为系统峰值上限。 |
| Write | 同一 P1 拓扑；约 5 分钟；幂等写与 replay | 600/600 replay；失败 0；unexpected 5xx 0；P95 27.66 ms；P99 73.16 ms | [写路径基线](../plan_todo/experiments/20260903-R2-06-write-path-baseline.md)；run `33710390070` | 独立写路径，不并入 read-mix P95。 |
| Confirm contention | 同一 P1 拓扑；8 contenders | 1 success / 7 conflicts；unexpected 5xx 0；confirm P95 836.7 ms；最终 schedule active | 同上 | 冲突是预期业务结果；confirm P95 不能与 read/write P95 横比。 |
| Comparable candidate | 与 write baseline 相同参数 | write P95 27.66 → 26.35 ms（-4.7%）；confirm P95 836.7 → 897.8 ms（+7.3%）；均未超过 15% 相对回归阈值 | candidate run `33714192935`；PR correctness gate run `33715890853` | 只做同脚本、同参数候选对比；不是绝对性能 SLA。 |
| Trace probe | HTTP → outbox → 独立 worker success/retry/dead-letter | `trace_id=trc-write-path-probe` 贯穿；每次 execution 新 request ID；parent request ID 稳定 | PR [#36](https://github.com/justtodo123/LogisticSystem_more/pull/36)；main smoke `33738039588` | 证明应用级关联字段传播；不等同于完整 OpenTelemetry tracing。 |
| 8m soak smoke | P1 拓扑；8 分钟；4 RPS | 33 samples；error rate 0；unexpected 5xx 0；RSS 1.206x | run `33717505441` | 只证明采样器可执行，不把它作为 soak baseline。 |
| 2h soak | PostgreSQL 16 + Redis 7 + 2 workers；2 小时；4 RPS read + 1 RPS login | 158,402 checks；errors 0；unexpected 5xx 0；dropped 0；480 samples；预热后 RSS 387,864 KB → 388,464 KB，约 1.002x | [2h soak 实验](../plan_todo/experiments/20260903-R2-06-p2-soak.md)；run `33720629269` | 只能登记该 2h 窗口的绝对值；不能推出永久无泄漏，也不与 5 分钟场景 P95 比较。 |

## 镜像安全与发布

| Claim | 验证结果 | 证据 | 边界 |
|---|---|---|---|
| 发布链路先构建、生成 CycloneDX SBOM、执行 Trivy、按版本化 policy fail closed，门禁成功后才推 GHCR。 | policy `2026-09-03.1`；Trivy `0.56.2`；Docker `28.0.4`；CRITICAL/HIGH blocking，UNKNOWN/scanner error/missing report fail。 | `.github/workflows/cd.yml`；`security/image-scan-policy.json`；[镜像扫描实验](../plan_todo/experiments/20260904-R2-06-image-scan.md)。 | 这是发布时门禁，不是定时扫描或运行时防护。 |
| 初始阻断由基础镜像 OS 包造成，先升级/切换基础层而不是放宽 policy 或直接登记 exception。 | backend 初始 3 CRITICAL / 15 HIGH；frontend 2 CRITICAL / 35 HIGH；第一轮 OS upgrade 后 backend 因 trixie no-dsa/postponed 仍阻断；最终切换 forky / Alpine 3.24。 | [阻断证据与修复计划](../../docs/镜像扫描门禁-阻断证据与修复计划.md)；PR [#39](https://github.com/justtodo123/LogisticSystem_more/pull/39)、[#40](https://github.com/justtodo123/LogisticSystem_more/pull/40)。 | 不能把重复 `apt upgrade` 描述为可修复上游尚无 fixed package 的 CVE。 |
| 最终镜像门禁零 exception 通过并发布同批次 SHA tag。 | CD [33826520856](https://github.com/justtodo123/LogisticSystem_more/actions/runs/33826520856) success；backend Debian forky/sid，MEDIUM 1，blocked `[]`；frontend Alpine 3.24.1，无漏洞；exception `[]`。 | [R2 收口记录](../plan_todo/20260904-R2-closeout.md)；artifact `image-scan-f9e08a499ba50987505e32d58b545a37c9543ef4`（14 天）。 | backend 残留 CVE-2026-13346（pip 26.1.2 → 26.2.0）是 MEDIUM report-only，不是 exception；扫描通过不等于 Compose/生产验证。 |
| 审计、回滚和未来生产验证使用不可变 SHA tag。 | backend/frontend 均发布 `f9e08a499ba50987505e32d58b545a37c9543ef4`。 | [R2 收口记录](../plan_todo/20260904-R2-closeout.md)。 | `latest` 只是便利标签，后续文档合入会重建推进，不能作为审计批次。 |

## 禁止夸大的表述

| 不要说 | 建议说法 |
|---|---|
| “系统实现 exactly-once” | “数据库幂等状态机、claim token 和 replay 降低重复执行；外部通知在 sender 无幂等能力时仍是 at-least-once。” |
| “已经生产部署/生产级验证” | “在 GitHub Actions 的 PostgreSQL 16 + Redis 7 + 多 worker 生产近似拓扑完成协议与故障验证；生产部署另行验收。” |
| “100 并发证明 PostgreSQL 性能” | “SQLite 独立 Session 证明 CAS/幂等协议；PostgreSQL 规模结果单独引用 100,000 号段实验。” |
| “系统 P95 是 9.81 ms” | “在约 5 分钟、8 RPS reads + 1 RPS login 的 read-mix 场景，混合 P95 为 9.81 ms。” |
| “2 小时证明没有内存泄漏” | “2 小时窗口预热后 RSS 约 1.002x，未观察到明显持续增长；更长时间仍需验证。” |
| “Trivy 已清零所有漏洞” | “阻断项为 0、exception 为 0；backend 仍有 1 个 MEDIUM report-only。” |
| “镜像扫描持续运行” | “发布流水线有 fail-closed 扫描门禁；定时扫描尚未实现。” |
| “前端演示证明真实后端链路” | “Mock 演示展示产品流程；一致性和故障能力由后端测试、GHA 与实验记录证明。” |

## 基线说明

- 应用与文档最终冻结点：`main @ df025fb`，来自 PR [#42](https://github.com/justtodo123/LogisticSystem_more/pull/42)。
- 镜像安全验收批次：`f9e08a499ba50987505e32d58b545a37c9543ef4`，来自 PR #40 / CD `33826520856`。
- 两者用途不同，不应把 `df025fb` 写成原始镜像修复批次，也不应把后续 `latest` 重建替代不可变镜像审计证据。
