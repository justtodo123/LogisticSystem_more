---
plan_id: "R2-01"
title: 关键状态转移并发控制
status: pending
priority: P0
owner: 待认领
created: 2026-08-25
updated: 2026-08-25
depends_on: ["R2-00"]
---

# R2-01 — 关键状态转移并发控制

## 来源证据与当前行为

参考路线图指出调度确认、到货确认和 AI 建议仍存在“读取→判断→修改→提交”的竞态窗口，重点位置为 `src/backend/services/schedule_service.py`、`arrival_confirm_service.py`、`ai_suggestion_service.py`。第一轮只收口了 delivered 终态和订单六态，不等于并发安全。

## 问题与目标

让关键状态转移在独立数据库 Session/连接下具备明确的 CAS/乐观锁语义；并发失败返回稳定冲突结果，不产生重复包裹、事件、批次或通知。

## 范围

- draft 确认、到货确认、AI 建议确认/拒绝及其副作用。
- version 字段或条件更新、唯一约束、冲突业务码和审计记录。
- SQLite 行为与 PostgreSQL 行为差异及独立 Session 并发测试。

## 非目标

- 不在本卡实现 Saga、outbox 或完整压测；相关工作由 R2-03/R2-06 承担。
- 不在未确定冲突产品语义前擅自把所有冲突变成成功幂等。

## 依赖与进入条件

- R2-00 完成；第一轮订单/货物状态契约保持不变。
- 明确每个状态转移的允许前置状态和冲突响应语义。

## 有序实施步骤

1. 盘点服务、路由、模型、迁移和现有状态测试，绘制状态转移与副作用时序。
2. 优先用条件更新/CAS 抢占状态；必要时增加 `version` 和迁移，避免持锁调用外部服务。
3. 将副作用放在成功抢占之后，并为重复请求定义稳定响应和审计事件。
4. 用独立 Session、真实并发任务测试 20/100 请求确认同一 draft；补到货和 AI 建议边界。
5. 在 PostgreSQL 下复跑，覆盖锁等待、唯一冲突、事务取消和连接断开。
6. 更新 API/错误码/文档，记录实现前后副作用计数。

## 验收标准

- 100 个独立并发确认请求最多一个成功，其余得到同一可识别冲突语义。
- 不产生重复包裹、批次、事件、通知；delivered 仍受第一轮终态规则保护。
- SQLite 与 PostgreSQL 均有测试，不能用同一测试事务伪造并发。
- 进程取消/数据库异常不会留下“状态已改但副作用不可解释”的记录。

## 验证命令

```bash
cd src/backend
python -m pytest -q tests/unit/services tests/api tests/integration
python -m pytest -q -p no:cacheprovider
```

PostgreSQL 并发命令、连接数、数据规模和原始输出须写入实验报告；前端契约变更时另行执行 `npx vue-tsc --noEmit && npm run build`。

## 文档与问题记录同步

更新状态机、错误码、API 契约和第二轮 README；已有问题优先更新，不重复创建同一竞态记录。

## 回滚与恢复

迁移必须可逆；若 CAS 改造导致合法串行流程失败，先回滚实现但保留失败并发测试，禁止恢复无保护的旧竞态作为最终状态。

## 完成记录

- 尚未开始。完成时填写并发数据、数据库版本、测试结果、Commit/PR 和遗留冲突语义。
