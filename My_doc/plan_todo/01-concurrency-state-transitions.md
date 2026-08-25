---
plan_id: "R2-01"
title: 关键状态转移并发控制
status: pending
priority: P0
owner: justtodo123
created: 2026-08-25
updated: 2026-08-25
depends_on: ["R2-00A", "R2-04A"]
---

# R2-01 — 关键状态转移并发控制

## 来源证据与当前行为

`schedule_service.confirm_schedule`、`arrival_confirm_service`、`ai_suggestion_service` 仍是读取→判断→修改→提交。重点文件：`src/backend/services/schedule_service.py`、`arrival_confirm_service.py`、`ai_suggestion_service.py`。第一轮只收口了 delivered 终态和订单六态，不等于并发安全。

冲突与幂等语义已冻结：[D-R2-CONFLICT](./decisions.md)、[D-R2-IDEM](./decisions.md)。迁移从 [R2-00A](./00A-alembic-migration-baseline.md) 的唯一 head 派生，`40901` 使用 [R2-04A](./04A-error-contract-and-db-session.md) 的错误 registry 与统一 envelope。

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

- 尚未开始。完成时填写并发数据、SQLite 限制说明、测试结果、Commit/PR。
