---
plan_id: "R2-03"
title: 重规划 Saga 与事务消息可靠性
status: pending
priority: P0
owner: justtodo123
created: 2026-08-25
updated: 2026-08-31
depends_on: ["R2-01", "R2-02"]
---

# R2-03 — 重规划 Saga 与事务消息可靠性

## 来源证据与当前行为

`replan_service.py` 长链路可能经过创建、确认、版本记录、旧实体标记、节点调度和路径规划，底层多次 `commit` 会造成部分成功。通知存在 fire-and-forget、复用请求 Session；SMTP 同步阻塞（`services/notification/email.py`）。

补偿边界已冻结：[D-R2-SAGA](./decisions.md)。任务表与 outbox migration 必须基于 [R2-00A](./00A-alembic-migration-baseline.md) 的唯一 head；失败响应复用 [R2-04A](./04A-error-contract-and-db-session.md)。

## 问题与目标

将重规划升级为可恢复的短事务 + Saga 状态机；通知改为 transactional outbox，业务提交成功后事件不丢，重复消费可控。

## 范围（P0）

- `replan_tasks`（或等价表）、步骤状态、幂等键、重试次数、错误、版本号、`manual_required` 入口。
- F007 / F021 / F005 / F006 的前置检查、成功持久化、补偿或人工状态；进程重启后可扫描继续。
- outbox 表与业务同行提交；独立 Session 的投递循环（线程或后台 task 即可，不必上独立进程）。
- 测试内注入：commit 前/后异常、重复触发同一 replan key。

## 非目标

- 不引入 Kafka。
- 不重写调度/路线算法质量。
- **不**把真实 SMTP、Docker worker 重启、PostgreSQL 故障注入当作本卡 `done` 条件（R2-05）。

## 依赖与进入条件

- R2-01 状态抢占与 R2-02 幂等/编号协议已可运行；其 schema 均基于 R2-00A 单一 head。
- 补偿表以 decisions 为准：F021 已提交不自动拆包。

## 有序实施步骤

1. 画出当前重规划 `commit` 点与外部 I/O，按 D-R2-SAGA 切短事务。
2. 增加任务表和唯一幂等键；每步可重复执行、前置可检查、成功可落库。
3. 已提交且不可逆的步骤进入 `manual_required`；实现重启扫描（测试里用显式 `resume(task_id)` 即可）。
4. 主事务同时写业务数据和 outbox；提交后由独立 Session worker 投递；区分可重试/不可重试。
5. 去掉请求 Session 复用和请求路径上的同步 SMTP；最大重试、死信、消费幂等、审计。
6. 对每个阶段做测试级故障注入，保存任务状态转移；真实 worker 重启留给 R2-05。

## 验收标准（P0）

- F007/F021/F005/F006 任一阶段失败后无不可解释半成品；任务可继续、补偿或 `manual_required`。
- 同一任务重试不重复创建包裹、路线、批次或通知；旧方案和 delivered 保持第一轮不变量。
- 业务提交成功而通知失败时 outbox 仍在；重复投递不产生重复业务副作用。
- 可查询 pending / retry / dead-letter 与人工状态。

## P1 复跑（不阻塞本卡 done）

PostgreSQL + 独立 worker 进程重启、外部超时、SMTP 真实失败：在 R2-05 做。

## 验证命令

```bash
cd src/backend
python -m pytest -q tests/unit/services tests/integration -p no:cacheprovider
```

每次实验记录任务 ID、步骤、数据库快照路径到 `experiments/`。

## 文档与问题记录同步

更新重规划时序图、事务边界、通知运维说明和第二轮 README。已有部分成功问题只更新证据。

## 回滚与恢复

迁移保留旧数据。若某步不具备可靠补偿，必须保留 `manual_required`，不得回退为静默多次 commit。

## 完成记录

> 当前状态仍为 `pending`：以下是功能分支上的实现与本地验证证据，不代表 PR、CI、合并或发布已完成。

### 已实现状态机与事务边界

- Alembic 当前唯一 head：`r2_03_replan_task_claims`；迁移链依次包含 `r2_03_replan_tasks`、`r2_03_outbox_events`、`r2_03_outbox_claims` 与 `r2_03_replan_task_claims`。
- `replan_tasks` 以唯一 `idempotency_key` 记录 `F007 → F021 → F005 → F006 → NOTIFICATION → COMPLETED`、重试、错误、版本及 `manual_required`。
- `replan_tasks` 增加 `claim_token` / `claimed_by` / `claimed_step` / `claimed_at` / `lease_until`。步骤执行先按条件更新抢占租约，再用 claim token fencing 推进、补偿或转人工；默认租约 300 秒，过期可回收，过期后的旧 token 不能 finalize 或提交业务写入。
- `redispatch()` 非 draft 主链通过 `start()` 与 `resume_async()` 按持久化 `current_step` 推进；F007/F021/F005/F006 下层调用使用 `commit=False`，业务写入与 task 步骤由编排层逐步提交。
- `reroute()` 通过 `start(initial_step="F006", initial_status="RUNNING")` 与 `resume_async()` 直接从 F006 初始化并推进 NOTIFICATION；route 下层使用 `commit=False`，重复 key 重放完成结果。
- `NOTIFICATION` 将任务完成与唯一 outbox 事件同行提交；请求路径不执行 SMTP/Webhook，独立 Session worker 负责 retry、delivered、dead-letter。
- D-R2-SAGA 已覆盖：F007 draft 可补偿；F021 提交后转人工；F005 未发车可作废、`in_transit` 转人工；F006 未执行可删、已执行转人工。

### 故障注入矩阵

| 场景 | 本地测试结果 |
|---|---|
| 同一 idempotency key 重复触发 | 返回同一 task，不重复创建方案、批次、路线或 outbox |
| F007 真实写入后、commit 前异常 | 业务写入与 task 推进 rollback，task 保持 F007 |
| F021 commit 后异常 | task 进入 `manual_required`，不自动拆包或继续 |
| 通知投递失败 | 业务/task 保持完成，outbox 保留为 retry；耗尽后 dead-letter |
| 重复 deliver | delivered 事件不再调用 sender，不重复外部副作用 |
| worker Session | 使用独立 Session，不复用请求 Session |
| reroute 重复 idempotency key | 返回同一 task，不重复创建 route/outbox |
| reroute route 写入后、commit 前异常 | 新 route rollback，task 停留 F006 |
| reroute 已执行后异常 | task 进入 `manual_required` |
| 活跃 task lease | 第二 worker 无法抢占同一当前步骤 |
| 过期 task lease | 可被回收，新 token 继续执行 |
| 过期后的旧 claim token | 不能 finalize 步骤，也不能提交业务写入 |
| 并发 resume 同一步骤 | 仅执行一次 |
| 并发 NOTIFICATION | 只创建一条 outbox 事件 |

### 分层验证证据

聚焦测试与完整后端测试是不同层级的证据，数字不得合并：

1. `3965855`（第一优先）：HTTP 幂等贯通、补偿后 `current_step` 恢复、任务产物引用、redispatch 版本链 `1→2→3`；聚焦测试 **114 passed**。
2. `ffba2f0`（第二优先）：`tests/integration/test_exception_replan.py` 已无 TODO/空 `pass`，覆盖真实 HTTP + `X-Idempotency-Key`；该文件与 `test_exceptions.py` 合计 **20 passed**。
3. `71e7506`（第三优先）：outbox 增加 `processing` / `claim_token` / lease、原子 claim、租约回收，以及独立 Session worker `src/backend/scripts/outbox_worker.py`；聚焦测试 **101 passed**；Alembic head 推进为 `r2_03_outbox_claims`。
4. `ffec6bb`（第四优先）：`test_release_migrate.py` 的期望 head 更新为 `r2_03_outbox_claims`；当时完整后端命令结果为 **899 passed, 269 warnings in 173.43s**；当时 `alembic heads` 唯一输出 `r2_03_outbox_claims (head)`。
5. `ea4415a` / `c7f49aa`（第五优先）：`replan_tasks` 增加 leased execution claims 与 token fencing；`reroute()` 直接从 F006 初始化；Alembic head 推进为 `r2_03_replan_task_claims`。并发/任务聚焦测试 **24 passed**（`test_replan_task_service.py` 17 项 + `test_replan_task_concurrency.py` 7 项）。完整后端命令 `python -m pytest -q -p no:cacheprovider tests` 结果为 **908 passed, 271 warnings in 184.88s**；`alembic heads` 唯一输出 `r2_03_replan_task_claims (head)`。

完整后端测试中的 908 passed 不替代上述各组聚焦测试的场景说明；聚焦测试数字也不声称等同于完整回归。SQLite 结果只辅助验证 P0 schema、幂等和租约协议，不代表 PostgreSQL、多 worker 或生产并发能力。

详细记录：[20260829-R2-03-replan-saga-outbox.md](./experiments/20260829-R2-03-replan-saga-outbox.md)。

### 功能分支提交（`87190d2` 之后，oldest → newest）

- `e8f3203` — `feat: add R2-03 replan task skeleton`
- `9aeabe4` — `feat: add replan task recovery orchestration`
- `f652947` — `feat: add transactional outbox delivery`
- `8b8bc61` — `feat: route replan notifications through outbox`
- `e7ad8ff` — `feat: wire replan saga short transactions`
- `fa716dc` — `docs: record R2-03 saga implementation evidence`
- `9e78068` — `feat: wire reroute through replan saga`
- `3965855` — `fix: harden replan saga recovery`
- `ffba2f0` — `test: add real replan saga integration coverage`
- `71e7506` — `fix: add leased outbox delivery claims`
- `ffec6bb` — `test: update release migration head expectation`
- `17b4f73` — `docs: record R2-03 implementation evidence`
- `ea4415a` — `feat: add replan task execution claims`
- `c7f49aa` — `test: cover concurrent replan task execution`

远程分支已存在：`origin/feat/R2-03-replan-saga-outbox` @ `ffec6bb`；本地相对远程 ahead 4。当前尚无 R2-03 PR，未执行 push。

### 语义边界与剩余缺口

- `redispatch(draft_only=True)` 仍走旧路径，不属于当前 Saga 主链。
- outbox 的数据库去重、claim 与 lease 控制内部并发和重放；若外部邮件/Webhook 不支持幂等令牌，进程在“外部已接收、数据库尚未写回 delivered”之间崩溃时只能保证 **at-least-once**，不得声称 exactly-once。
- 真实 PostgreSQL、独立 worker 进程重启、外部超时、真实 SMTP/Webhook 失败仍归 R2-05；当前环境未执行，因此 R2-05 保持 `blocked`，SQLite 结果不替代 P1 证据。
- R2-03 计划卡保持 `pending`，直到获得授权创建 PR，并完成 CI 与 merge；当前下一动作仅是待授权后创建 R2-03 PR，不开始 R2-04B。未获明确授权前不执行 `git push` 或创建 GitHub PR。
