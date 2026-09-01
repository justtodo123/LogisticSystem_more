# 20260901-R2-05-fault-harness

## 元数据

- 计划 ID：R2-05
- 计划/决策版本：D-R2-ENV / D-R2-DB
- 日期与时区：2026-09-01 Asia/Shanghai
- 执行人：Codex
- 层级：P1 外部拓扑（故障切片，GHA 已验证，整卡未验收完成）
- Git 分支：feat/R2-05-fault-resilience
- Commit SHA：c2b1f69d5ee782ba9e42e7e2c9a1f41cc00b0421
- Merge SHA：4c72828ab9dd147d44b0f92893426783ae3fef9b
- PR URL：https://github.com/justtodo123/LogisticSystem_more/pull/21
- CI run URL：https://github.com/justtodo123/LogisticSystem_more/actions/runs/33487318596
- main CI run URL：https://github.com/justtodo123/LogisticSystem_more/actions/runs/33489817053
- CD run URL：https://github.com/justtodo123/LogisticSystem_more/actions/runs/33490209885

## Schema 与数据来源

- Alembic 当前 revision：由 `scripts/release_migrate.py` 升级到仓库唯一 head
- 目标数据库：GitHub Actions `postgres:16-alpine` fresh service
- 目标缓存：GitHub Actions `redis:7-alpine` service
- 数据：P1 job 已有合成演示数据；本切片不新增业务数据

## 环境

- OS：Windows 11 本机无 Docker / WSL / PostgreSQL / Redis
- 目标拓扑：GitHub Actions ubuntu-latest + postgres:16-alpine + redis:7-alpine
- 应用 worker：两个可单独寻址的单 worker Uvicorn 进程（`127.0.0.1:18001` / `18002`）+ 独立 outbox worker
- 关键依赖：Docker CLI 可见 GHA service 容器；`pg_dump` 在 Postgres 容器内以用户 `logistics` 执行

## 场景

- Redis `docker pause` 后：`/api/health` 的 `redis` 字段为 `degraded`；login/me 仍成功
- 杀掉并重启两个 Uvicorn worker 后：订单列表仍可查询
- `pg_dump --schema-only` 产出包含 `alembic_version` 的 schema SQL
- 不把 schema dump 写成备份恢复；不把 Redis pause 写成完整恢复演练

## 命令

本机没有 PostgreSQL/Redis/Docker，不执行 live harness。目标 GHA job 在现有 smoke 之后执行：

```text
python scripts/p1_fault_harness.py
```

harness 内部顺序：

```text
docker pause <redis:7-alpine>
GET /api/health
POST /api/auth/login
GET /api/auth/me
docker unpause <redis:7-alpine>
kill worker A/B && restart uvicorn :18001/:18002
GET /api/orders
docker exec <postgres:16-alpine> pg_dump -U logistics -d logistics --schema-only
```

## 原始结果与产物

- 命令是否实际执行：是（GitHub Actions，不是本机）
- GitHub Actions：PR #21 CI [run 33487318596](https://github.com/justtodo123/LogisticSystem_more/actions/runs/33487318596) 四个 job 全绿；main CI [run 33489817053](https://github.com/justtodo123/LogisticSystem_more/actions/runs/33489817053) 四个 job 全绿；CD [run 33490209885](https://github.com/justtodo123/LogisticSystem_more/actions/runs/33490209885) 成功。`P1 PostgreSQL + Redis 协议与多 worker 验证` 日志记录：
  - `fault_checks=redis-pause,worker-restart,pg-schema-dump`
  - `redis_paused_health=degraded`
  - `db_login_during_redis_pause=ok`
  - `orders_after_restart=100`
  - `pg_dump_schema_bytes=48019`
- 产物：artifact `p1-postgres-redis-worker-logs`（zip 7928 bytes，保留 7 天，约 2026-09-08 过期）
  - `fault-summary.txt` 182 bytes，SHA-256 `764014428e92bde3bd0055a1efcf2bbd06c06c8ebbee531022aacccdde008409`
  - `pg-schema.sql` 48019 bytes，SHA-256 `4b03bc5b454d20eb9ece7fcf1d137aa74eccdd64d5cd693070c08e847c958ffc`；含 `CREATE TABLE public.alembic_version`
- 脱敏检查：已检查；摘要与 schema dump 不含凭据、JWT 或业务请求体。compose/service 仍使用示例口令 `logistics/logistics`，仅 P1 实验栈。
- 本机：未执行 Docker pause/unpause、worker kill 或 `pg_dump`。

## 证据边界

- Redis pause 只证明数据库登录路径在缓存不可用时仍可用，以及 health 可见 `degraded`。未断言 unpause 后同一进程内 Redis client 自动恢复。
- worker 重启只证明合成订单在 PostgreSQL 中可再次列出；不是 outbox 中途重启，也不是连接池耗尽。
- `pg_dump --schema-only` 只是 schema 导出，不是备份恢复 drill，没有 restore 或数据回放。
- 未覆盖：PostgreSQL 断连、deadlock/serialization、连接池耗尽、100,000 编号规模、跨 worker 登录限流。
- 本机无 Docker/PostgreSQL/Redis，不得用 SQLite 或 skip 结果替代本切片。

## 结论

- 状态：`in_progress`。PR #21 已于 2026-09-01 08:58:49 UTC 合并，merge `4c72828`；main CI run 33489817053 四个 job 全绿；CD run 33490209885 成功。故障切片已验证，R2-05 仍不得标 `done`。
- 即使本次 CI 全绿，R2-05 仍不得标 `done`；后续继续 deadlock/serialization、连接池耗尽、备份恢复和 100,000 编号规模验证。
