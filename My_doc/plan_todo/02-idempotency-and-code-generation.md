---
plan_id: "R2-02"
title: 原子幂等与业务编号生成
status: in_progress
priority: P0
owner: justtodo123
created: 2026-08-25
updated: 2026-08-28
depends_on: ["R2-01"]
---

# R2-02 — 原子幂等与业务编号生成

## 当前进度

- **R2-02A 数据库幂等状态机：本机实现与验证完成，待 Commit / PR / CI / merge。**
- **R2-02B 业务编号号段：pending，明确不在当前分支实施。**
- 本卡在 R2-02B 完成前保持 `in_progress`，不得因 R2-02A 完成而把整个 R2-02 标为 `done`。

## 来源证据与当前行为

R2-02A 已将 `middleware/idempotency.py` 与 `utils/idempotency_store.py` 从 check → execute → cache 改为数据库 claim/finalize 状态机。`idempotency_records` 是正确性来源；Redis 只在数据库提交 `SUCCEEDED` 后作为 best-effort 成功响应旁路缓存，进程内 dict 不参与幂等正确性。

R2-02B 的编码生成点仍位于 `algorithms/global_schedule.py`、`packaging.py`、`route_planning.py`、`node_dispatch.py` 等位置，现有 `LIKE prefix` 后取最大号的行为留待独立 slice 替换。

协议已冻结：[D-R2-IDEM](./decisions.md)、[D-R2-CODE](./decisions.md)。R2-02A schema 从 [R2-00A](./00A-alembic-migration-baseline.md) 的唯一 head 派生；`40902` / `40903` 使用统一错误登记和映射。

## 问题与目标

1. R2-02A：建立数据库唯一约束上的幂等状态机，消除并发请求的 TOCTOU 重复执行窗口，并保真重放成功响应。
2. R2-02B：业务编码改为号段条件更新，消除并发重复编号。该目标尚未实施。

## R2-02A 已完成范围

- `不存在 → PROCESSING → SUCCEEDED/FAILED/EXPIRED`，包含 payload fingerprint 与 claim-token fencing。
- 以 `idempotency_records` 为真相源；同 key 不同 payload 返回 `40903`；未过期 PROCESSING 返回 `40902` 与 `Retry-After: 1`。
- 保存并重放原始响应 bytes、HTTP status、media type 与安全 header；重新生成 Content-Length。
- 八个冻结端点强制 `X-Idempotency-Key`；认证失败保持 401 优先，已认证但无权限保持 403 优先。
- 其他认证写接口（POST/PUT/PATCH/DELETE）有 key 时采用同一协议，无 key 时保持兼容；公开登录和 logout 按冻结策略排除。
- client key 按认证用户 namespace；同一 client key 可由不同用户独立使用。
- 请求体捕获上限为 1 MiB；超限返回 `41300`。
- keyed 流式响应在返回前完整 materialize；background task 仅首次 owner 执行，重放不重复。
- PROCESSING lease 必须严格大于全局请求 timeout；当前无 heartbeat。
- Redis 关闭或写入失败不影响数据库重放；幂等路径不使用通用内存 fallback。
- 成功终态写入失败时不把可能已提交副作用的 owner 释放为 FAILED；记录保留 PROCESSING 隔离即时重试。
- HTTP 200 且 JSON code != 0 的错误信封视为失败并释放 claim，不写入 SUCCEEDED；非 JSON 的 2xx（如导出文件）仍保真重放。

## R2-02B pending 范围

- 调度/包裹/路线/批次号段表。
- 用号段条件更新替换现有 `max+1` / 前缀扫描。
- 已有唯一约束下的有限冲突重试、耗尽错误与并发编号证据。
- 编号生成量、无重复统计和后续 PostgreSQL 拓扑复跑。

## 非目标与边界

- 不把 R2-02A 称为 exactly-once。业务 side effect transaction 与 `mark_succeeded` 是独立事务；lease 到期后的最终重复风险需要 R2-03 outbox/事务边界继续收口。
- R2-02A 不要求 Redis NX、PostgreSQL 多进程或 10 万编码作为完成条件；P1 拓扑验证归 R2-05。
- 不改对外编号形态为 ULID。
- 当前不设置响应捕获大小上限：若业务已提交后因本地阈值拒绝持久化，会造成不安全重试语义。部署应避免对 keyed 写接口返回无界内容。

## R2-02A 验收结果

- 同一 key/hash 的 20 与 100 个独立 Session contender：均只有 1 个 `OWNED`，其余为 `IN_PROGRESS`。
- 同 key 不同 payload：HTTP 409 / `40903`。
- PROCESSING：HTTP 409 / `40902`，含 `Retry-After: 1`，下游不执行。
- 成功重放：下游只执行一次；原始 status/body/media type/安全 header 保真。
- Redis disabled 与写入异常：数据库重放仍成立，进程内无 `idem:` key。
- FAILED/EXPIRED reclaim（含过期后新 payload）、stale owner fencing、取消/超时歧义隔离与成功终态失败即时隔离均通过测试；HTTP 200 错误信封释放后同 key 可重试。
- 八个强制端点的 missing-key、401、403 优先级矩阵通过。
- fresh migration、Alembic check、release gate、downgrade/schema 测试通过。

## 验证证据

详见 [20260828-R2-02A-idempotency-state-machine.md](./experiments/20260828-R2-02A-idempotency-state-machine.md)。本机实际结果：

- R2-02A 定向：82 passed, 70 warnings，退出码 0。
- 完整后端：834 passed, 258 warnings，退出码 0。
- migration/release 测试：33 passed，退出码 0。
- fresh SQLite：唯一 head `r2_02a_idempotency_state`；Alembic check 无漂移；release gate passed。
- 前端：`npx vue-tsc --noEmit` 与 `npm run build` 退出码 0；构建转换 1925 modules。

SQLite 结果只证明本机 P0 协议辅助验证，不能外推 PostgreSQL、Redis 或多 worker 的锁行为与容量。

## 后续有序步骤

1. 完成 R2-02A diff/status/敏感文件检查。
2. 创建 R2-02A Commit / PR，等待 CI，并在真实合并后回填证据。
3. 从更新后的 main 创建独立 R2-02B slice。
4. 实施号段表、迁移、有限冲突重试与编号并发证据。
5. R2-02B 完成后才将整个 R2-02 标记为 `done`。

## 完成记录

- R2-02A Commit SHA：尚无。
- R2-02A PR URL：尚无。
- R2-02A CI run URL：尚无。
- R2-02A merge SHA：尚无。
- R2-02B：尚未开始。
