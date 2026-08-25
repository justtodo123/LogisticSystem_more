---
plan_id: "R2-03"
title: 重规划 Saga 与事务消息可靠性
status: pending
priority: P0
owner: 待认领
created: 2026-08-25
updated: 2026-08-25
depends_on: ["R2-01", "R2-02"]
---

# R2-03 — 重规划 Saga 与事务消息可靠性

## 来源证据与当前行为

参考路线图指出 `src/backend/services/replan_service.py` 的长链路可能经过创建、确认、版本记录、旧实体标记、节点调度和路径规划，底层服务自行 commit 会造成部分成功。后台通知还可能 fire-and-forget、复用请求 Session，SMTP 阻塞事件循环。

## 问题与目标

将重规划从不可解释的多次提交升级为可恢复的短事务 + Saga 状态机；将通知改为 transactional outbox，使业务提交成功后事件不丢、重复消费可控。

## 范围

- `replan_tasks`（或等价任务表）、步骤状态、幂等键、重试次数、错误、版本号和人工处理入口。
- F007/F021/F005/F006 各阶段的前置状态、成功记录、补偿动作和进程重启恢复。
- outbox 事件表、独立 worker Session、指数退避、死信、重放和通知指标。

## 非目标

- 不引入 Kafka 等重型中间件作为前置条件；优先 PostgreSQL outbox + worker。
- 不在本卡重写调度算法质量或路线优化算法。

## 依赖与进入条件

- R2-01 的状态抢占和 R2-02 的幂等/编码协议已冻结。
- 产品明确旧方案、部分成功和人工处理的可见状态。

## 有序实施步骤

1. 画出现有重规划提交点和外部 I/O，选择短事务边界与 Saga 状态机。
2. 增加任务表和唯一幂等键；每一步做到可重复执行、前置状态可检查、成功可持久化。
3. 为已提交步骤定义补偿或 `manual_required`，实现重启扫描、继续执行和人工重试。
4. 在主事务中同时写业务数据和 outbox；提交后由独立 worker 投递，分类可重试/不可重试错误。
5. 移除请求 Session 复用和同步 SMTP 阻塞；实现最大重试、死信、幂等消费和审计。
6. 对每个阶段注入异常、commit 前后崩溃、外部超时、worker 重启，保存状态转移和恢复耗时。

## 验收标准

- F007/F021/F005/F006 任一阶段失败后无不可解释半成品；任务可继续、补偿或明确进入人工状态。
- 同一任务重试不重复创建包裹、路线、批次或通知；旧方案和 delivered 终态保持第一轮不变量。
- 主业务提交成功而通知暂时失败时 outbox 不丢；worker 重启后可继续，重复消费不产生重复业务副作用。
- 可查询 pending、retry、dead-letter、最大延迟和恢复结果。

## 验证命令

```bash
cd src/backend
python -m pytest -q tests/unit/services tests/integration
python -m pytest -q -p no:cacheprovider
```

另在 PostgreSQL/Redis 目标环境执行故障注入和 worker 重启脚本；每次实验记录任务 ID、步骤、数据库快照和日志。

## 文档与问题记录同步

更新重规划时序图、事务边界、通知运维手册、审计说明和第二轮 README；已有部分成功问题记录只更新证据，不重复建档。

## 回滚与恢复

迁移保留旧数据；worker 切换采用双读/停机 drain 方案。若 Saga 某步不具备可靠补偿，必须保留 `manual_required`，不得回退为静默多次 commit。

## 完成记录

- 尚未开始。完成时填写状态机版本、故障注入矩阵、恢复结果、Commit/PR 和仍需人工处理的边界。
