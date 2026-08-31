# 20260831-R2-05-postgres-redis-gha

## 元数据

- 计划 ID：R2-05
- 计划/决策版本：D-R2-ENV / D-R2-DB
- 日期与时区：2026-08-31 Asia/Shanghai
- 执行人：Codex
- 层级：P1 外部拓扑（第一刀，未验收完成）
- Git 分支：feat/R2-05-postgres-redis-gha
- Commit SHA：03a3436790a7d98342ba04e35386358718c08891
- PR URL：https://github.com/justtodo123/LogisticSystem_more/pull/18
- CI run URL（如有）：尚无

## Schema 与数据来源

- Alembic 当前 revision：r2_04b_token_version
- 数据库来源：GHA 将使用 fresh PostgreSQL 16；本机未启动 PostgreSQL
- 数据是否为合成/脱敏数据：是

## 环境

- OS：Windows 11 本机无 Docker / WSL / PostgreSQL / Redis
- 目标拓扑：GitHub Actions ubuntu-latest + postgres:16-alpine + redis:7-alpine
- 应用 worker / 后台 worker 数：compose 定义 uvicorn --workers 2 + outbox-worker；本机未启动
- 关键依赖：psycopg[binary]>=3.2.0

## 场景

- 给 CI 增加 Postgres/Redis service
- PostgreSQL 驱动与 URL 规范化
- fresh PostgreSQL 迁移到唯一 Alembic head
- Redis ping
- 不把 SQLite 结果写成 P1 通过

## 命令

```text
cd src/backend
python -m pytest -q -p no:cacheprovider tests/unit/core/test_database_url.py tests/unit/core/test_database_sqlite.py tests/unit/scripts/test_init_engine_dialect.py tests/unit/scripts/test_release_migrate.py tests/p1
```

## 原始结果与产物

- 命令是否实际执行：本机仅跑不依赖 Postgres 的单元测试；P1 live 测试在无 P1_DATABASE_URL 时 skip
- GHA Postgres/Redis job：PR #18 已创建，CI 进行中
- 脱敏检查：已检查；无凭据入库（compose 使用示例口令 logistics/logistics，仅 P1 实验栈）

## 结论

- 状态：in_progress；未执行 Docker Compose，不得标 done
- 已知限制：登录限流仍为进程内计数；SQLite StaticPool 不是跨 worker 证明
- 下一步：等待 PR #18 CI；随后复跑 CAS/幂等/Saga/撤权
