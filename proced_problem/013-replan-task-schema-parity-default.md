---
problem_id: "013"
slug: replan-task-schema-parity-default
date: 2026-08-29
tags: [alembic, schema-parity, sqlite, replan, migration]
severity: major
status: fixed
related_files: ["src/backend/models/replan_task.py", "src/backend/alembic/versions/r2_03_replan_tasks.py", "src/backend/utils/schema_management.py", "src/backend/tests/migration/test_schema_management.py"]
related_pr: "feat/R2-03-replan-saga-outbox (commit 尚无)"
---

# 新增 replan_tasks 后 create_all 混合库 schema parity 校验失败

## 1. 症状（表现形式）

在新增 `replan_tasks` ORM 与 Alembic revision 后，首次运行迁移和 registry 定向测试时出现 2 个失败：

```text
tests/migration/test_schema_management.py::test_unversioned_current_schema_is_adopted_on_copy FAILED
tests/migration/test_schema_management.py::test_wal_source_copy_preserves_committed_rows FAILED
```

完整定向集合当时为 36 个测试，结果为 `34 passed, 2 failed`。失败位置都在 `adopt_known_mixed_sqlite()`，错误为 `目标数据库未处于 Alembic managed 状态`（终端显示乱码但对应该 RuntimeError）。

## 2. 复现条件

只要 ORM `Base.metadata.create_all()` 创建的未版本化 SQLite 与 Alembic fresh upgrade 的 schema 在 server default 的字符串表示上不一致，就能稳定复现：

1. 在 `src/backend` 执行 `python -m pytest -q -p no:cacheprovider tests/migration`。
2. 让 `replan_tasks.manual_required` 的 ORM 默认值由 SQLAlchemy SQLite 编译为 `"'0'"`。
3. 让迁移使用 `sa.text("0")`，SQLite inspector 返回 `"0"`。
4. `schema_management._metadata_differences()` 判定 parity 不一致，adoption 不进入 managed 状态。

## 3. 定位过程

1. 先确认不是 Alembic 分支问题：`python -m alembic -c alembic.ini heads` 返回单一 `r2_03_replan_tasks (head)`，且完整 migration 测试中的其他用例通过。
2. 对比 ORM `create_all()` 与迁移 fresh upgrade 的 `replan_tasks` schema 签名，发现唯一差异是 `manual_required` 的 server default：ORM 为 `"'0'"`，迁移为 `"0"`；字段、索引、约束和其他默认值一致。
3. 将迁移中的 `server_default=sa.text("0")` 改为与现有迁移风格一致的 `server_default="0"`，重新比较后 parity 差异消失。
4. 复跑定向集合，结果从 `34 passed, 2 failed` 变为 `36 passed`；再按监督指令仅运行 migration 与 registry，结果为 `34 passed`。

## 4. 根因

ORM 的 SQLite server-default 编译形式与迁移中显式 `sa.text("0")` 的 inspector 表示不同，导致 schema parity 严格比较失败。

## 5. 解决方案

- 在 `src/backend/alembic/versions/r2_03_replan_tasks.py` 将 `manual_required` 的迁移默认值改为 `server_default="0"`，与 ORM `Boolean` 在 SQLite 下的实际签名保持一致。
- 保留 `replan_tasks` 的字段、状态/步骤/retry/version check constraints、唯一幂等索引和状态步骤索引。
- 未修改 schema 管理器的严格校验逻辑；严格 parity 检查仍能发现真实漂移。

## 6. 验证

修复前后：

| 命令 | 修复前 | 修复后 |
|---|---:|---:|
| `python -m pytest -q -p no:cacheprovider tests/migration tests/unit/core/test_model_registry.py tests/unit/models/test_replan_task.py` | 34 passed, 2 failed | 36 passed |
| `python -m alembic -c alembic.ini heads` | 单 head（已确认） | `r2_03_replan_tasks (head)` |
| `python -m pytest -q -p no:cacheprovider tests/migration tests/unit/core/test_model_registry.py` | 未单独执行 | 34 passed |

## 7. 通用经验

- 新增 ORM 表时，必须同时比较 `Base.metadata.create_all()` 与 Alembic fresh upgrade 的 inspector schema 签名，不能只检查字段名。
- SQLite Boolean/整数默认值在 SQLAlchemy 编译后可能带引号；迁移应沿用仓库已有 server-default 写法，并以 inspector 返回值作为 parity 基准。
- migration suite 出现 adoption/WAL copy 失败时，先比较 schema signature，再判断是否是 WAL/文件复制问题；不要放宽 parity 校验来掩盖迁移漂移。
- 每个新幂等任务模型都应测试重复 key 的 `IntegrityError`，并单独验证 migration downgrade 能回到父 revision。
