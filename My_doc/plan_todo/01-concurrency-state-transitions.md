---
plan_id: "R2-01"
title: 关键状态转移并发控制
status: in_progress
priority: P0
owner: justtodo123
created: 2026-08-25
updated: 2026-08-27
depends_on: ["R2-00A", "R2-04A"]
---

# R2-01 — 关键状态转移并发控制

## 来源证据与当前行为

`schedule_service.confirm_schedule`、`arrival_confirm_service`、`ai_suggestion_service` 仍是读取→判断→修改→提交。重点文件：`src/backend/services/schedule_service.py`、`arrival_confirm_service.py`、`ai_suggestion_service.py`。第一轮只收口了 delivered 终态和订单六态，不等于并发安全。

冲突与幂等语义已冻结：[D-R2-CONFLICT](./decisions.md)、[D-R2-IDEM](./decisions.md)。迁移从 [R2-00A](./00A-alembic-migration-baseline.md) 的唯一 head 派生，`40901` 使用 [R2-04A](./04A-error-contract-and-db-session.md) 的错误 registry 与统一 envelope。

## 状态转移与副作用时序

以下为实施前盘点。R2-01 把“改变主状态”前移为条件更新抢占；抢占失败不得进入打包、事件和通知。

### 1. 调度方案确认 `confirm_schedule`

| 步骤 | 当前实现 | R2-01 目标 |
|---|---|---|
| 读 draft | `status == draft` 查询 | 先按编号读取；非 draft 视为冲突 |
| 校验订单 | 失败则删除 draft 并 commit | 抢占成功后再校验；失败删除 draft |
| 改变主状态 | 打包与写包裹之后才 `draft → active` | **先** `UPDATE ... SET status=active, version=version+1 WHERE status=draft` |
| 创建包裹 | F021 `packaging()` 后 `db.add` | 仅抢占成功后执行 |
| 订单/货物 | `update_orders_after_f007` / `update_goods_after_f021` | 仅抢占成功后、同一事务 |
| 批次 | 本路径不创建（F005 才写批次） | 保持 |
| 事件 | 无业务事件表写入 | 保持 |
| 通知 | **commit 之后** `send_notification` | 保持：不持锁打外部通知 |
| commit 边界 | 包裹+订单/货物+status 一次 commit；通知在其后 | 抢占+本地副作用一次 commit；通知仍在 commit 后 |

锁持有点：CAS 到本地 DB 副作用结束。打包是 CPU + SQLite 读，允许留在同一短事务；禁止在未 commit 前等待外部 HTTP。

### 2. 到货确认 `confirm_arrival`

| 步骤 | 当前实现 | R2-01 目标 |
|---|---|---|
| 读包裹 | 按 `package_code` 读取 | 保持 |
| 改变主状态 | `transition_package_status` 直接改 ORM | **先** `UPDATE packages SET status=? WHERE id=? AND status=expected` |
| 正常路径期望 | `in_transit → delivered` | 行数为 0（含重复确认）→ `DomainError(40901)` |
| 异常路径期望 | `in_transit/delivered → exception` | 已是 exception → `40901` |
| 货物/订单 | 状态机更新；正常路径可能 `_trigger_repacking` 新建 L1→L2 包裹 | 仅抢占成功后 |
| 事件 | 异常路径写 `exception_events` | 仅抢占成功后 |
| 通知 | 正常路径 `send_notification_fire_and_forget`（commit 前触发，失败忽略） | 仅抢占成功后；不因通知持锁 |
| commit 边界 | 服务不 commit，API 成功后 commit | 保持；CAS 与本地副作用同事务 |

### 3. AI 建议确认/拒绝

| 步骤 | 当前实现 | R2-01 目标 |
|---|---|---|
| 读建议 | 按 id 读取，`status != pending` 返回 40003 | 非 pending 改为 `40901` |
| 改变主状态 | 先可能 `confirm_schedule`（其内部会 commit），再改 suggestion | **先** `UPDATE ai_suggestions SET status=? WHERE id=? AND status=pending` |
| 调度副作用 | suggestion/action + related draft 时调用 `confirm_schedule` | 抢占建议后调用，且 `commit=False`，与建议写入同一事务 |
| 事件 | `log_events` 审计 | 仅抢占成功后 |
| 通知 | 若应用 draft，复用调度确认的 commit 后通知 | 共享事务提交后再通知 |
| commit 边界 | `confirm_schedule` 可能先提交，再提交建议 | 建议抢占 + 可选调度副作用 + 审计一次提交 |

## 问题与目标

让关键状态转移在**独立数据库 Session** 下具备 CAS/条件更新语义；并发失败者得到稳定 `40901`，不产生重复包裹、事件、批次或通知。

## 范围（P0）

- draft 确认、到货确认、AI 建议确认/拒绝及其副作用。
- 条件更新（`UPDATE ... WHERE status = :expected`）或 `version` 字段；冲突业务码 `40901` 和审计。
- 独立 Session 的 20/100 并发测试（SQLite 可跑，报告必须写写锁限制）。
- 引擎创建改为方言安全，避免 P1 切换 PostgreSQL 时 `check_same_thread` 炸。

## 非目标

- 不在本卡实现 Saga、outbox、完整压测（R2-03 / R2-06）。
- **不**把 PostgreSQL 锁等待、多 worker 复跑当作本卡 `done` 条件（那是 R2-05）。
- 不把所有冲突变成成功幂等（无 key 的第二次确认必须 409）。

## 依赖与进入条件

- R2-00A 与 R2-04A 已完成：迁移单 head、错误码和数据库会话契约可用。
- 第一轮订单/货物状态契约保持不变。

## 有序实施步骤

1. 盘点服务、路由、模型、迁移和现有状态测试，画出状态转移与副作用时序（确认流程里打包算法在 CAS 之前还是之后）。
2. 用条件更新抢占状态；必要时加 `version` 与 Alembic。**先 CAS 再跑 CPU 打包**，避免持锁跑外部 HTTP；本地 packing 若必须在事务内，保持短事务并记录锁持有点。
3. 副作用只在抢占成功之后发生；无幂等键的重复确认返回 `409` + `40901`。
4. 用独立 Session、真实并发任务测 20/100 请求确认同一 draft；补到货和 AI 建议。禁止共享同一个测试事务伪造并发。
5. 修复 `create_engine`：仅 SQLite 传 `check_same_thread`。不在本卡引入 psycopg 或 Compose。
6. 更新 API/错误码/文档；把命令、副作用计数写入 `experiments/`。

## 验收标准（P0）

- 100 个独立并发确认请求最多一个成功；其余为同一 `40901` 语义（SQLite 下若因写锁排队导致串行，仍必须零重复副作用，并在报告注明不能外推 PostgreSQL）。
- 不产生重复包裹、批次、事件、通知；delivered 仍受第一轮终态保护。
- CAS 事务内发生异常时状态与本地数据库副作用一并 rollback；进程崩溃后的跨步骤恢复由 R2-03 验收，不在本卡虚构 Saga 能力。
- 方言安全：非 SQLite URL 不再带 `check_same_thread`。

## P1 复跑（不阻塞本卡 done）

在 R2-05 环境复跑：锁等待、唯一冲突、事务取消、连接断开。结果挂到 R2-05 实验记录并回链本卡。

## 验证命令

```bash
cd src/backend
python -m pytest -q tests/unit/services tests/api tests/integration -p no:cacheprovider
```

并发用例的文件名、数据规模、原始输出写入 `experiments/`。前端契约变更时另跑 `npx vue-tsc --noEmit && npm run build`。

## 文档与问题记录同步

更新状态机、错误码、API 契约和第二轮 README；已有竞态问题优先更新，不重复建档。

## 回滚与恢复

迁移必须可逆；若 CAS 导致合法串行流程失败，先回滚实现但保留失败并发测试，禁止恢复无保护的旧竞态作为最终状态。

## 完成记录

- 本地实施中，状态：`in_progress`。Commit SHA / PR / CI：尚无。
- 实验记录：[experiments/20260827-R2-01-cas-state-transitions.md](./experiments/20260827-R2-01-cas-state-transitions.md)
- 定向 pytest（含新增回归）：47 passed / 35 warnings / 23.84s。
- 完整后端 pytest：772 passed / 216 warnings / 238.32s。
- 迁移/parity 子集：49 passed / 15.91s；无新增 Alembic revision，head 仍为 `r2_00a_schema_convergence`。
- SQLite 限制：20/100 独立 Session 线程在 NullPool + busy_timeout=30s 下本地通过；不能外推 PostgreSQL 多 worker。
- 本地默认 SQLite 不在 head：release_migrate 拒绝原地修改（exit 2），未触碰业务库。
