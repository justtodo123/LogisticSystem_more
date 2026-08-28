---
name: 20260828-r2-02a-idempotency-state-machine
description: R2-02A database-backed idempotency state machine, replay fidelity, failure recovery, and SQLite concurrency evidence
metadata:
  type: project
---

# R2-02A 实验与验证记录

## 元数据

- 计划 ID：R2-02A
- 计划/决策版本：`v2026-08-25-r2-freeze` / `D-R2-IDEM`
- 本地完成时间：2026-08-28，Asia/Shanghai
- 执行人：justtodo123
- 层级：P0 本机协议
- Git 分支：`feat/R2-02-idempotency-state-machine`
- Commit SHA：`889a70ac232f0958624cf677c82375feb51bc5d9`
- PR URL：https://github.com/justtodo123/LogisticSystem_more/pull/10
- CI run URL：https://github.com/justtodo123/LogisticSystem_more/actions/runs/33151979633
- Merge SHA：`c1020a44d69b050c3b0ce80554ba2198cea039ee`

## Schema 与数据来源

- Alembic 当前 revision：`r2_02a_idempotency_state`
- Alembic heads：唯一 head `r2_02a_idempotency_state`
- 数据库来源：fresh 临时 SQLite；迁移测试中的 Alembic-managed legacy；API fixture SQLite
- 升级前 revision / schema 指纹：`r2_00a_schema_convergence`；迁移测试验证 legacy 行被诚实标为 `EXPIRED`，不伪造 payload hash
- 数据规模与种子方式：合成 pytest fixture；并发用例分别使用 20、100 个独立 Session 竞争同一 key
- 数据是否为合成/脱敏数据：是

## 环境

- OS：Windows 11 Home China 10.0.26200，win32
- Python：3.13.3
- Node：仓库当前本机 Node/npm 环境；本次未单独记录版本号
- 数据库：SQLite；并发用例为文件 SQLite、`NullPool`、`check_same_thread=False`、busy timeout、每个 contender 独立 Session
- Redis：未启动真实 Redis；覆盖关闭与写入异常两种故障模式
- 应用 worker / 后台 worker 数：单进程 pytest；并发协议用线程池模拟独立数据库会话
- 关键依赖或容器镜像版本：仓库当前依赖；未使用容器

## 场景

- 目标与不变量：数据库唯一键只产生一个 `PROCESSING` owner；同 fingerprint 的成功响应可保真重放；未过期记录的不同 fingerprint 为 `40903`；处理中为 `40902`；失败可重试；TTL/lease 过期后可用新 fingerprint fenced reclaim；Redis 不影响正确性
- 请求分布 / 并发客户端：同一 key、同一 payload hash，20/100 contender
- 预热 / 持续时间：无
- 故障注入点：Redis disabled、Redis `setex` 抛错、业务异常、成功终态数据库写入失败、PROCESSING lease 过期、请求取消、stale owner finalize、流式响应与 background task、HTTP 200 错误信封
- 对照组 / 基线：无 key 的可选写接口保持原有非去重行为；登录明确排除

## 命令

```text
cd src/backend

python -m pytest -q -p no:cacheprovider tests/unit/core/test_idempotency_middleware.py tests/unit/core/test_settings.py tests/api/test_idempotency.py tests/api/test_export.py tests/unit/core/test_idempotency_store.py tests/unit/services/test_cache.py

python -m pytest -q -p no:cacheprovider

# DATABASE_URL 指向 fresh 临时 SQLite，逐条执行
python -m alembic -c alembic.ini heads
python -m alembic -c alembic.ini upgrade head
python -m alembic -c alembic.ini check
python scripts/release_migrate.py
python -m pytest -q -p no:cacheprovider tests/migration/test_schema_management.py tests/unit/scripts/test_release_migrate.py

cd ../frontend
npx vue-tsc --noEmit
npm run build
```

## 原始结果与产物

- 命令是否实际执行：是
- 定向 R2-02A 退出码：0；82 passed, 70 warnings（最终安全回归；此前记录 71 passed）
- 完整后端退出码：0；834 passed, 258 warnings in 173.50s
- 迁移/release 测试退出码：0；33 passed in 17.46s
- fresh migration gate：唯一 head；upgrade 到 `r2_02a_idempotency_state`；Alembic check 为 `No new upgrade operations detected.`；release gate 为 `database migration gate passed`
- 前端退出码：0；`vue-tsc --noEmit` 通过；Vite 生产构建完成，1925 modules transformed，built in 1.77s
- 前端构建警告：第三方 `@vueuse/core` 的 Rolldown `INVALID_ANNOTATION` 警告；未导致失败
- 并发摘要：20 与 100 contender 均仅 1 个 `OWNED`，其余为 `IN_PROGRESS`；最终状态使用新 Session 断言为 `PROCESSING`
- Redis 摘要：disabled 与写入异常时，导出响应均从数据库原样重放；业务导出只执行一次；未写入 `idem:` 进程内缓存
- 追踪内摘要路径：本文件
- 外部原始产物位置 / CI artifact URL：CI run https://github.com/justtodo123/LogisticSystem_more/actions/runs/33151979633；本机后台任务输出为临时文件，不追踪
- 产物大小 / SHA-256：未登记（临时输出不作为持久 artifact）
- 保留期限 / 删除日期：会话临时输出，由工具运行环境管理
- 脱敏检查：已检查摘要；不含 DSN、JWT、口令、个人数据或原始业务请求体
- 访问限制或复现障碍：无真实 PostgreSQL、Redis、多 worker；Windows SQLite 锁行为不能外推生产拓扑

## 结论

- 状态：R2-02A 已通过本机验证、PR #10 与 CI，并合并到 `main`
- 结论与对应证据：数据库状态机、claim token fencing、401/403/key precedence、八个强制端点、其他认证写接口可选幂等、DELETE、响应 status/body/media type/安全 header 重放、流式响应 materialize、background 仅 owner 执行、Redis 故障降级、明确业务失败释放、取消歧义隔离、过期后新 payload reclaim 均有测试覆盖
- 成功终态失败边界：路由可能已提交副作用时，`mark_succeeded` 失败返回数据库错误但不主动标记 `FAILED`；记录保持 `PROCESSING`，即时重试为 `40902`，避免立即重复执行。业务提交与幂等终态不是同一事务，lease 到期后的重复风险不宣称 exactly-once，后续与 R2-03 outbox/事务边界处理
- 响应策略：keyed 响应在返回前完整 materialize 以便数据库保真重放；background task 仅挂在首次 owner 响应，不持久化、不在 replay 重复；当前不设置响应捕获上限，避免已提交副作用后因本地捕获阈值拒绝持久化
- PROCESSING lease：配置校验要求 lease 严格大于全局请求 timeout；无 heartbeat；请求取消/外层 timeout 属于歧义结果，不主动写 `FAILED`，保留 `PROCESSING` 隔离即时重试
- 已知限制：SQLite 写锁可能串行化竞争；本结果只证明 P0 协议辅助验证，不能证明 PostgreSQL、多 worker 或真实 Redis 的锁与容量行为
- 未执行项：PostgreSQL + Redis + 多 worker 拓扑验证归 R2-05；业务提交与幂等终态的原子边界归 R2-03
- 审查修复：HTTP 200 + JSON code != 0 的错误信封不再写入 SUCCEEDED，同一 key 可重试；导出等非 JSON 2xx 仍保真重放。
- 后续：在 R2-03 收口业务事务边界，在 R2-05 复跑生产拓扑验证
