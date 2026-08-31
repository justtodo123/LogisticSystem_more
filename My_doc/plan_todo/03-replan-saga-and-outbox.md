---
plan_id: "R2-03"
title: 重规划 Saga 与事务消息可靠性
status: pending
priority: P0
owner: justtodo123
created: 2026-08-25
updated: 2026-08-25
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

- 尚未开始。完成时填写状态机版本、故障注入矩阵、Commit/PR、仍需人工处理的边界。
