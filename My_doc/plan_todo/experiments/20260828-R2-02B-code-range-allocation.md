---
name: 20260828-r2-02b-code-range-allocation
description: R2-02B business code range table, CAS allocation, unique-conflict retry, exhaustion errors, and SQLite concurrency evidence
metadata:
  type: project
---

# R2-02B 实验与验证记录

## 元数据

- 计划 ID：R2-02B
- 计划/决策版本：`v2026-08-25-r2-freeze` / `D-R2-CODE`
- 本地完成时间：2026-08-28，Asia/Shanghai
- 执行人：justtodo123
- 层级：P0 本机协议
- Git 分支：`feat/R2-02B-code-range-allocation`
- Commit SHA：`6b8a8d2c8c2e0a65a3c11b11f71172dd254737fe`
- PR URL：https://github.com/justtodo123/LogisticSystem_more/pull/11
- CI run URL：https://github.com/justtodo123/LogisticSystem_more/actions/runs/33157404527
- Merge SHA：`87190d23de8a28fa2a84f9abb50b18a2e6ddf167`

## Schema 与数据来源

- Alembic 当前 revision：`r2_02b_code_range_allocation`
- Alembic heads：唯一 head `r2_02b_code_range_allocation`
- 数据库来源：fresh 临时 SQLite；从 `r2_02a_idempotency_state` 升级的 Alembic-managed legacy；pytest fixture SQLite
- 升级前 revision / schema 指纹：`r2_02a_idempotency_state`；升级后新增 `code_ranges`，回滚后表删除
- 数据规模与种子方式：合成 pytest fixture；顺序 20/200 次分配；独立 Session 并发 20 与 100 个 contender
- 数据是否为合成/脱敏数据：是

## 环境

- OS：Windows 11 Home China，win32
- Python：3.13.3
- Node：本次未改前端，未单独跑前端构建
- 数据库：SQLite；并发用例为文件 SQLite、`NullPool`、`check_same_thread=False`、busy timeout、每个 contender 独立 Session
- Redis：未使用
- 应用 worker / 后台 worker 数：单进程 pytest；并发协议用线程池模拟独立数据库会话
- 关键依赖或容器镜像版本：仓库当前依赖；未使用容器

## 场景

- 目标与不变量：调度/包裹/路线/批次/调度明细编号由 `code_ranges` 条件更新抢号；对外形态仍为 `GS` / `PKG` / `ROUTE` / `BATCH` / `DISP` + 日期 + 定宽序号；已有唯一约束保留；占用编号有限重试；号段耗尽返回登记码 `40904`，冲突重试耗尽返回 `40905`，不升未知 `500`
- 请求分布 / 并发客户端：同一资源、同一日期前缀，20/100 个独立 Session 同时抢号并插入 `global_schedules`
- 预热 / 持续时间：无
- 故障注入点：号段 `next_value` 超过宽度上限；连续占用已存在编码；未知 resource
- 对照组 / 基线：生成函数不再扫描 `LIKE prefix` 或维护进程序号；仅在号段行缺失时一次性扫描已有最大号作为 seed

## 命令

```text
cd src/backend

python -m pytest -q -p no:cacheprovider tests/unit/core/test_code_allocation.py tests/unit/core/test_code_allocation_concurrency.py tests/unit/core/test_error_codes.py tests/unit/core/test_model_registry.py

python -m pytest -q -p no:cacheprovider tests/unit/algorithms/test_packaging.py tests/unit/algorithms/test_global_schedule.py tests/unit/algorithms/test_node_dispatch.py tests/unit/algorithms/test_route_planning.py tests/unit/services/test_state_machine.py tests/unit/services/test_r2_01_cas_concurrency.py --basetemp <workspace>/tmp/pytest-r202b4

python -m pytest -q -p no:cacheprovider tests/migration/test_schema_management.py tests/unit/scripts/test_release_migrate.py --basetemp <workspace>/tmp/pytest-r202b3

python -m pytest -q -p no:cacheprovider --basetemp <workspace>/tmp/pytest-r202b-full

# DATABASE_URL 指向 fresh 临时 SQLite
python -m alembic -c alembic.ini heads
python -m alembic -c alembic.ini upgrade head
python -m alembic -c alembic.ini check
python scripts/release_migrate.py
```

## 原始结果与产物

- 命令是否实际执行：是
- R2-02B 定向分配测试退出码：0；21 passed（19 单测 + 2 并发）
- 算法/状态机/R2-01 CAS 回归退出码：0；189 passed in 15.61s
- 迁移/release 测试退出码：0；35 passed in 16.42s
- 完整后端退出码：0；859 passed, 258 warnings in 173.70s
- fresh migration gate：唯一 head `r2_02b_code_range_allocation`；Alembic check 为 `No new upgrade operations detected.`；release gate 为 `database migration gate passed`
- 并发摘要：20 与 100 个独立 Session 均得到互不重复的 `GS20260828xxx`；落库行数等于并发数；号段 `next_value` 分别为 21 与 101
- 生成量摘要：同一 Session 连续分配 200 个包裹编号无重复，`next_value=201`
- 追踪内摘要路径：本文件
- 外部原始产物位置 / CI artifact URL：CI run https://github.com/justtodo123/LogisticSystem_more/actions/runs/33157404527；本机 pytest 输出为临时文件，不追踪
- 产物大小 / SHA-256：未登记（临时输出不作为持久 artifact）
- 保留期限 / 删除日期：会话临时输出，由工具运行环境管理
- 脱敏检查：已检查摘要；不含 DSN、JWT、口令、个人数据或原始业务请求体
- 访问限制或复现障碍：无真实 PostgreSQL、多 worker；Windows SQLite 写锁会串行化竞争，不能外推生产拓扑

## 结论

- 状态：R2-02B 已通过本机验证、PR #11 与 CI，并合并到 `main`
- 结论与对应证据：号段表、条件更新抢号、已有编码 seed、占用编号有限重试、耗尽/冲突登记错误码、生成函数委托 allocator、fresh/legacy 迁移与 downgrade 均有测试覆盖
- 已知限制：SQLite 写锁可能串行化竞争；本结果只证明 P0 协议辅助验证，不能证明 PostgreSQL 或多 worker 的锁与容量行为。PostgreSQL 拓扑复跑归 R2-05
- 未执行项：PostgreSQL + 多 worker 拓扑复验归 R2-05；本机未单独重跑前端，但 PR CI 的“前端类型检查 + 构建”已通过
- 后续：整个 R2-02 closeout 后进入 R2-03；在 R2-05 复跑生产拓扑验证
