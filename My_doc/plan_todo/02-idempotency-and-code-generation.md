---
plan_id: "R2-02"
title: 原子幂等与业务编号生成
status: pending
priority: P0
owner: 待认领
created: 2026-08-25
updated: 2026-08-25
depends_on: ["R2-00", "R2-01"]
---

# R2-02 — 原子幂等与业务编号生成

## 来源证据与当前行为

参考路线图指出 `src/backend/middleware/idempotency.py` 与 `src/backend/utils/idempotency_store.py` 采用 check → execute → save，两个 worker 可同时执行。`src/backend/algorithms/global_schedule.py`、`packaging.py`、`route_planning.py`、`node_dispatch.py` 还需排查进程序号、`max + 1` 或 `count + 1` 编号方式。

## 问题与目标

建立跨进程原子的幂等状态机，并将业务编码交给数据库 sequence/identity、UUIDv7/ULID 或号段协议，消除并发重复和错误重放。

## 范围

- `不存在 → PROCESSING → SUCCEEDED/FAILED/EXPIRED` 的幂等记录和 payload hash。
- Redis NX 或 PostgreSQL 唯一索引/`ON CONFLICT` 的原子占位、处理中请求语义、超时恢复和响应重放。
- 调度、包裹、路线、批次等业务编码的生成、唯一约束和有限冲突重试。

## 非目标

- 不把幂等误称为 exactly-once；外部副作用需与 R2-03 的 outbox 一并定义。
- 不在没有容量证据时承诺具体并发规模。

## 依赖与进入条件

- R2-01 已明确状态转移成功点和副作用边界。
- 明确哪些 API 支持幂等键、响应保存期限和请求主体最大尺寸。

## 有序实施步骤

1. 盘点所有编码生成点、唯一索引和重试路径，写出冲突矩阵。
2. 选择 PostgreSQL 记录表或 Redis NX 作为占位事实源；同 key 不同 payload 返回冲突。
3. 处理 PROCESSING 的 409/202/等待策略、崩溃过期、原始 status/header/response 重放。
4. 用 sequence/ULID/号段替换进程计数和查询最大值；补唯一约束与确定性有限重试。
5. 使用 100 个相同 key 并发请求及至少 10 万编码生成测试，覆盖多进程/多 worker。
6. 更新中间件、错误码、指标和运行手册。

## 验收标准

- 同 key、同 payload 并发 100 次业务副作用只执行一次；不同 payload 必须拒绝。
- 进程崩溃后 PROCESSING 可恢复；重放保留约定的 HTTP status、业务 code 和必要 header。
- 多 worker 生成至少 10 万个编码无重复，唯一冲突不会变成未知 500。
- Redis 不可用时明确降级边界，不把不一致的进程内 dict 当分布式幂等存储。

## 验证命令

```bash
cd src/backend
python -m pytest -q tests/unit tests/api tests/integration
python -m pytest -q -p no:cacheprovider
```

Redis/PostgreSQL 多进程命令、原始响应和编码样本保存到第二轮实验目录；禁止只在 SQLite 单进程内验收。

## 文档与问题记录同步

更新幂等 API 说明、业务编码规范、错误码、运维恢复说明和第二轮 README；非平凡故障写入 `proced_problem/`。

## 回滚与恢复

先保留旧编码读取兼容和数据库唯一约束，再切换生成器；迁移失败从备份恢复。幂等协议回滚不得删除已写入的占位和结果记录。

## 完成记录

- 尚未开始。完成时填写协议选型、并发结果、编码数量、环境、Commit/PR 和遗留限制。
