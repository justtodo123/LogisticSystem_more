---
name: 20260827-r2-01-cas-state-transitions
description: R2-01 CAS occupancy, DomainError passthrough, commit=False boundary, init dialect safety
metadata:
  type: project
---

# R2-01 实验与验证记录

## 元数据

- 计划 ID：R2-01
- 计划/决策版本：`v2026-08-25-r2-freeze` / `D-R2-CONFLICT` / `D-R2-ERROR`
- 本地完成时间：2026-08-27，Asia/Shanghai
- 执行人：justtodo123
- 层级：P0 内部协议
- Git 分支：`feat/R2-01-cas-state-transitions`
- Commit SHA：`03bffbc7afba3e6bf95ed6ac4fe7b7c06b875b67`
- Merge commit SHA：`4e355394eb420ab8f35d1852ceaa95dfc0eac1a7`
- PR URL：https://github.com/justtodo123/LogisticSystem_more/pull/8
- CI run URL：https://github.com/justtodo123/LogisticSystem_more/actions/runs/33047947336

## Schema 与数据来源

- Alembic 当前 revision：仓库唯一 head `r2_00a_schema_convergence`
- Alembic heads：唯一 head，本卡无新增 revision
- 数据库来源：pytest SQLite（内存 StaticPool + 并发用例文件 SQLite NullPool）
- 迁移前 revision / schema 指纹：未改业务 schema；`GlobalSchedule.version` 已存在
- 数据规模：合成 fixture；并发 20/100 worker 独立 Session
- 数据是否为合成/脱敏数据：是

## 环境

- OS：Windows-11-10.0.26200-SP0
- CPU：AMD64 Family 25 Model 116 Stepping 1, AuthenticAMD
- Python：3.13.3
- 数据库：SQLite；无 PostgreSQL
- Redis：无
- 应用 worker / 后台 worker 数：单进程 pytest；并发用例为线程池 + 独立 Session
- 关键依赖：仓库当前 backend 依赖；无 Docker / WSL

## 假设

- 目标代码不变量：CAS `rowcount==0` 统一 `DomainError(CODE_STATE_CONFLICT)`；批量到货不吞噬 DomainError；`confirm_schedule(commit=False)` 失败不持久化删 draft；init 脚本仅 SQLite 传 `check_same_thread`
- 并发分布 / 并发客户端：单机多线程，不是 PostgreSQL 多 worker
- 预热 / 持续时间：无
- 故障注入点：已 delivered 包裹进入批量正常确认；packaging RuntimeError + commit=False；postgres URL 传入 init 脚本
- 假账号 / 网络：无

## 命令

```text
cd src/backend

python -m pytest -q tests/unit/core/test_cas.py tests/unit/services/test_r2_01_cas_concurrency.py tests/unit/services/test_arrival_confirm_service.py::TestConfirmArrivalBatch::test_confirm_arrival_batch_state_conflict_rolls_back tests/unit/services/test_schedule_service.py::TestScheduleServiceExceptionRollback::test_confirm_packaging_exception_deletes_draft tests/unit/services/test_schedule_service.py::TestScheduleServiceExceptionRollback::test_confirm_packaging_exception_commit_false_keeps_draft tests/unit/scripts/test_init_engine_dialect.py tests/api/test_r2_01_conflict_contract.py tests/api/test_ai_confirmation.py tests/api/test_arrival_confirm.py -p no:cacheprovider

# TEMP/TMP 指向仓库 tmp/pytest-tmp 后
python -m pytest -q -p no:cacheprovider

python -m alembic -c alembic.ini heads
python -m alembic -c alembic.ini check
python scripts/release_migrate.py

python -m pytest -q -p no:cacheprovider tests/migration tests/unit/scripts/test_release_migrate.py tests/unit/core/test_model_registry.py tests/unit/core/test_database_sqlite.py tests/unit/services/test_db_indexes.py
```

## 原始输出摘要

- 命令是否实际执行：是（本地）
- 定向测试退出码：0；47 passed, 35 warnings in 23.84s
- 完整后端退出码：0；772 passed, 216 warnings in 238.32s
- 迁移/parity 子集退出码：0；49 passed in 15.91s
- alembic heads：`r2_00a_schema_convergence (head)`，退出码 0
- alembic check（本地默认 DATABASE_URL）：FAILED Target database is not up to date
- release_migrate：exit 2；拒绝 unknown 本地 SQLite 原地修改
- 追踪包摘要路径：仅本机 gitignored `tmp/`，未入仓
  - `tmp/r2_01_targeted.txt` 8662 B SHA-256 f3c586394ee2ed8c2c5b33f36e2d883d26ba6356a79d9c87eb777ebe1a6e3df8
  - `tmp/r2_01_full.txt` 16630 B SHA-256 b5cf57b81380e6ae1792a0b79389f315666318a06099ea2f58c8dc3fa79f708f
  - `tmp/r2_01_parity.txt` 908 B SHA-256 bc62a7e15dfdfb37e303865e483bab6e70804b6d201a477d9c6d701601f68bd4
- 保留策略 / 删除日期：本机临时；不追踪
- 脱敏检查：已检；日志不含 DSN/JWT/真实口令
- 原始输出是否绑定本计划：是

## 结论

- 状态：通过并已合并；R2-01 标记为 `done`
- 与假设对应证据：批量 40901 透传且回滚；commit=False packaging 失败回滚后 draft 仍在；init postgres `connect_args=={}`
- 远程交付证据：PR #8 已合并；CI run 33047947336 的 `数据库迁移基线`、`后端测试 (pytest)`、`前端类型检查 + 构建` 均成功
- 已知限制：SQLite 写锁可把 100 worker 拉成串行；本次 20/100 在 busy_timeout=30s 下仍为单成功 + 其余 40901。不能外推 PostgreSQL 多 worker。首次完整 pytest 曾因用户 Temp `pytest-of-Lenovo` PermissionError 出 43 ERROR；TEMP 改到仓库 `tmp/pytest-tmp` 后 772 passed。
- 未通过项 / 未执行项：PostgreSQL / Redis / 多 worker 复跑未执行，归 R2-05；本地默认库 alembic check / release_migrate 按设计 fail-closed，CI fresh SQLite 的发布迁移、Alembic check 与 parity 专项通过
- 下一动作：进入 R2-02A 数据库幂等状态机；R2-02B 业务编号号段另行实施
