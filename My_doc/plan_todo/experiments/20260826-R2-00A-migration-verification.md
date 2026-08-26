---
name: 20260826-r2-00a-migration-verification
description: R2-00A Alembic/SQLite migration verification evidence
metadata:
  type: project
---

# R2-00A 实验与验证记录

## 元数据

- 计划 ID：R2-00A
- 日期与时区：2026-08-26；本机时区
- 执行人：justtodo123
- 层级：P0 本机协议
- Git 分支：`feat/R2-00A-alembic-migration-baseline`
- Commit SHA：最终分支 head `81db382ed61b8d279a4fef1f7964c29769989270`；分批提交为 `71237cd`、`9952095`、`adb3cac`、`efe6d73`、`8e3c3c2`、`d25da0b`、`81db382`
- PR URL：https://github.com/justtodo123/LogisticSystem_more/pull/5（MERGED）
- CI run URL：https://github.com/justtodo123/LogisticSystem_more/actions/runs/32932228092（SUCCESS）
- Merge commit：`8431fd8d66905d548e62e27ffea21bb1949d5f48`（GitHub verified signature）

## Schema 与数据来源

- Alembic 当前 revision：`r2_00a_schema_convergence`
- Alembic heads：唯一 head，`r2_00a_schema_convergence`
- 实验数据库：pytest `tmp_path` 临时 file-backed SQLite；smoke 使用 `C:\Users\Lenovo\AppData\Local\Temp\logistics-02a\logistics.db`
- 禁止使用的库：`src/backend/data/logistics.db` 未用于迁移实验，smoke 日志确认其 unchanged
- 数据：合成/脱敏 fixture；smoke 两轮初始化演示数据

## 环境

- OS：Windows 11 Home China 10.0.26200
- Python：3.13.3
- SQLite：3.49.1
- Alembic：1.19.1
- SQLAlchemy：2.0.52
- Redis：未纳入本机协议验证
- 应用 worker：本地 smoke 单 worker；未执行多 worker/外部拓扑验证
- Docker：Docker CLI 未安装，Compose runtime 未执行

## 场景与不变量

验证 fresh upgrade、唯一 head、metadata parity、受支持 legacy upgrade、known mixed adoption、未知/漂移/多版本/孤立 sidecar fail closed、WAL 数据保留、源文件不变、失败目标清理、release gate，以及临时数据库应用 smoke 与重启持久化。未知 schema 不执行 DDL 或盲目 stamp；copy/adopt 失败不覆盖源库。

## 实际命令与结果

### Alembic 图

```text
cd src/backend
python -m alembic -c alembic.ini heads
python -m alembic -c alembic.ini history
```

退出码：0。结果：`r2_00a_schema_convergence (head)`；历史链从 `<base>` 连续到两个父 revision 后汇聚为单一 head。

### Migration/release 回归

```text
cd src/backend
python -m pytest -q -p no:cacheprovider tests/migration tests/unit/scripts/test_release_migrate.py
```

退出码：0；31 passed；11.68s。

### Migration CI-equivalent subset

```text
python -m pytest -q -p no:cacheprovider tests/migration tests/unit/core/test_model_registry.py tests/unit/core/test_database_sqlite.py tests/unit/services/test_db_indexes.py tests/unit/scripts/test_release_migrate.py
```

退出码：0；49 passed；14.67s。

### Local temporary SQLite smoke

```text
python scripts/smoke_local.py --self-host
```

退出码：0；输出 `ALL_02A_SMOKE_CHECKS_PASS`。覆盖 Alembic fresh upgrade、双轮 seed、health、三角色登录、调度/确认/派车/路线、权限拒绝、交付到达、重启持久化；health 因空 AI key 为预期 degraded。

### Complete backend suite

```text
python -m pytest -q -p no:cacheprovider
```

退出码：0；718 passed，209 warnings；113.89s。

### Python compilation

```text
python -m compileall -q src/backend/config src/backend/models src/backend/scripts src/backend/utils src/backend/alembic/versions
```

退出码：0。

### Repository hygiene

```text
git diff --check
git -c core.whitespace=cr-at-eol diff --check
```

CRLF-aware 检查退出码：0。标准检查会把历史文档 CRLF 行尾视为 trailing whitespace；该文件保留既有 CRLF 风格，新增 banner 内容无实际空白字符。

敏感/禁止产物清单检查：退出码 0；未发现 tracked 数据库、`.env`、凭据、node_modules、缓存、日志或 raw/artifacts/tmp 产物。真实 token 格式扫描：退出码 0；DSN 测试字符串仅为测试 URL，不是凭据。

```text
docker --version && docker compose version
```

退出码：127；blocked，环境无 Docker CLI，未声称 Compose runtime 通过。

## 结论

- 状态：本机协议与 PR #5 最新远程 CI 通过；PR 已合并；Docker runtime blocked
- 结论：R2-00A 的 migration/parity/safety 及临时 SQLite smoke 证据均通过。源库保护覆盖普通文件、WAL、未知结构、漂移、孤立 sidecar 和失败目标清理。
- 已知限制：SQLite 本机单 worker；未验证 PostgreSQL、Redis、多 worker 和 Docker Compose runtime。
- 未通过/未执行：无本机或远程 CI 测试失败；Docker runtime 未执行。
- 追踪内原始输出：本次会话临时 task output；未提交 raw/artifact 文件。
- 下一步：R2-00A 已完成；当前主链为 R2-01，可并行推进 R2-04B。
