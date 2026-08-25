---
plan_id: "R2-02"
title: 原子幂等与业务编号生成
status: pending
priority: P0
owner: justtodo123
created: 2026-08-25
updated: 2026-08-25
depends_on: ["R2-01"]
---

# R2-02 — 原子幂等与业务编号生成

## 来源证据与当前行为

`middleware/idempotency.py` 与 `utils/idempotency_store.py` 为 check → execute → save；Redis 不可用时降级进程内 dict。`IdempotencyRecord` 模型仍在，但中间件已不把它当真相源。`algorithms/global_schedule.py`、`packaging.py`、`route_planning.py`、`node_dispatch.py` 使用 `LIKE prefix` 后取最大号。

协议已冻结：[D-R2-IDEM](./decisions.md)、[D-R2-CODE](./decisions.md)。表结构从 [R2-00A](./00A-alembic-migration-baseline.md) 的唯一 head 派生；`40902` / `40903` 由 [R2-04A](./04A-error-contract-and-db-session.md) 统一登记和映射。

## 问题与目标

建立**数据库唯一约束**上的幂等状态机；业务编码改为号段条件更新，消除并发重复和错误重放。

## 范围（P0）

- `不存在 → PROCESSING → SUCCEEDED/FAILED/EXPIRED`，含 payload hash。
- 以 `idempotency_records` 为真相源；同 key 不同 payload 返回 `40903`；PROCESSING 返回 `40902`。
- 调度/包裹/路线/批次号段表 + 已有唯一约束 + 有限冲突重试。
- 强制幂等键的 API 列表见 decisions；缺 key 返回明确 4xx。

## 非目标

- 不把幂等称为 exactly-once；外部副作用与 R2-03 outbox 一起定义。
- **不**要求 Redis NX、10 万编码跨多 worker、PostgreSQL 多进程作为本卡 `done` 条件。
- 不改对外编号形态为 ULID。

## 依赖与进入条件

- R2-01 已明确状态转移成功点和副作用边界；其前置 R2-00A/R2-04A 已提供迁移与错误契约基线。
- 强制幂等 API、TTL=24h、body≤1MB 已在 decisions 冻结。

## 有序实施步骤

1. 盘点编码生成点、唯一索引和重试路径，写出冲突矩阵。
2. 扩展 `idempotency_records`（Alembic）：`status`、`payload_hash`、`http_status`、header 子集；`INSERT` 抢占。
3. 中间件改为：抢占 → 执行 → 回写 SUCCEEDED/FAILED；异常不得把 PROCESSING 永久卡住（超时 EXPIRED + 可恢复）。
4. 用号段表替换进程计数和 `max+1`；保留前缀；唯一冲突有限重试。
5. 本机测：100 个相同 key 并发副作用一次；不同 payload 拒绝；缺 key 的强制接口 4xx。编号生成至少覆盖现有前缀的并发抢号（规模可小于 10 万，记录实际 N）。
6. 明确 Redis 只读成功缓存；Redis 关闭时仍走数据库。更新错误码、运行说明。

## 验收标准（P0）

- 同 key、同 payload 并发 100 次业务副作用只执行一次；不同 payload 必须 `40903`。
- PROCESSING 崩溃后可按 TTL/超时恢复；重放保留原始 HTTP status、业务 code 和必要 header。
- 强制列表接口无 `X-Idempotency-Key` 不得执行副作用。
- 号段抢号 + 唯一约束下无重复编码；冲突不变成未知 500。
- 关闭 Redis 时协议仍成立（打 DB），进程内 dict **不得**作为幂等存储。

## P1 复跑（不阻塞本卡 done）

多 worker + PostgreSQL 下 10 万编码、Redis 故障边界：在 R2-05 做。

## 验证命令

```bash
cd src/backend
python -m pytest -q tests/unit tests/api tests/integration -p no:cacheprovider
```

并发与编码样本写入 `experiments/`。禁止把“只开 Redis 的单进程缓存命中”写成跨进程幂等。

## 文档与问题记录同步

更新幂等 API 说明、业务编码规范、错误码、运维恢复说明和第二轮 README。

## 回滚与恢复

先保留旧编码读取兼容和数据库唯一约束，再切换生成器。幂等协议回滚不得删除已写入的占位和结果记录。

## 完成记录

- 尚未开始。完成时填写并发结果、编码数量、Redis 关闭验证、Commit/PR。
