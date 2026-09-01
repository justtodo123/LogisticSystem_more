# 20260901-R2-05-postgres-protocols-multi-worker

## 元数据

- 计划 ID：R2-05
- 计划/决策版本：D-R2-ENV / D-R2-DB
- 日期与时区：2026-09-01 Asia/Shanghai
- 执行人：Claude Code
- 层级：P1 外部拓扑（第二刀，GHA 已验证，整卡未验收完成）
- Git 分支：feat/R2-05-postgres-protocols
- Commit SHA：2de7c467b1722a2563915ea0a93e8e47160e6260；修复：ccf67fb、b8b391b
- PR URL：https://github.com/justtodo123/LogisticSystem_more/pull/20
- CI run URL：https://github.com/justtodo123/LogisticSystem_more/actions/runs/33484488151

## Schema 与数据来源

- Alembic 当前 revision：由 `scripts/release_migrate.py` 升级到仓库唯一 head
- 目标数据库：GitHub Actions `postgres:16-alpine` fresh service
- 目标缓存：GitHub Actions `redis:7-alpine` service
- 数据：脚本生成的合成演示数据，以及每个协议测试独占的 UUID/保留前缀数据

## 实现范围

- PostgreSQL 独立 Session 复跑：
  - CAS 状态抢占单赢家；
  - durable idempotency claim 单 owner；
  - 原子业务编号唯一且连续；
  - 重规划步骤 claim 单赢家；
  - outbox claim 单赢家。
- 多进程 HTTP 验证：
  - 两个独立、单 worker Uvicorn 进程分别监听 `127.0.0.1:18001` 和 `127.0.0.1:18002`；
  - 两个进程共享 PostgreSQL 和 Redis；
  - 登录在 worker A，`/me` 在 worker B；
  - 写请求首次发往 worker A，使用同一 `X-Idempotency-Key` 在 worker B 重放；
  - worker B logout 后，旧 token 在 worker A 被拒绝；
  - 数据库检查只产生一个 Node/StorageCenter，幂等记录为 `SUCCEEDED`。
- 后台进程：独立 outbox worker，进程日志与脱敏场景摘要保存为 CI artifact。

## 命令

本机没有 PostgreSQL/Redis，只执行安全的收集、skip 和静态检查：

```text
cd src/backend
env -u P1_DATABASE_URL -u P1_REDIS_URL -u DATABASE_URL -u REDIS_URL python -m pytest -q -p no:cacheprovider tests/p1
python -m py_compile tests/p1/conftest.py tests/p1/test_postgres_protocols.py tests/p1/test_multi_worker_http.py
```

目标 GHA job 将执行：

```text
python scripts/release_migrate.py
python -m pytest -q -p no:cacheprovider tests/p1/test_postgres_baseline.py tests/p1/test_redis_baseline.py tests/p1/test_postgres_protocols.py tests/unit/core/test_database_url.py
python scripts/init_users.py
python scripts/init_demo_data.py
python -m uvicorn main:app --host 127.0.0.1 --port 18001
python -m uvicorn main:app --host 127.0.0.1 --port 18002
python scripts/outbox_worker.py --worker-id gha-p1-outbox
python scripts/wait_http.py --timeout 60 http://127.0.0.1:18001/api/health http://127.0.0.1:18002/api/health
python scripts/smoke_local.py --base-url http://127.0.0.1:18001
P1_WORKER_A_URL=http://127.0.0.1:18001 P1_WORKER_B_URL=http://127.0.0.1:18002 python -m pytest -q -p no:cacheprovider tests/p1/test_multi_worker_http.py
```

## 当前结果

- Python 编译：通过。
- workflow YAML 解析和 P1 stage 静态断言：通过。
- 本机完整后端回归：`965 passed, 8 skipped, 317 warnings`（391.08 秒）；8 个 skip 均为缺少外部 PostgreSQL/Redis/双进程服务的 P1 场景，不是 PostgreSQL/Redis 通过证据。
- 前端 `npm run build`：通过；依赖 `@vueuse/core` 有 2 条 Rolldown `INVALID_ANNOTATION` 警告，未导致构建失败。
- `git diff --check` 与定向敏感内容检查：通过。
- GitHub Actions：PR #20 CI [run 33484488151](https://github.com/justtodo123/LogisticSystem_more/actions/runs/33484488151) 四个 job 全绿。`P1 PostgreSQL + Redis 协议与多 worker 验证` 已验证 PostgreSQL CAS/幂等/号段/replan/outbox 单赢家、双进程 JWT 撤权与幂等重放、以及 02A HTTP smoke。产物：artifact `p1-postgres-redis-worker-logs`。

## 证据边界

- 双端口方案可明确证明相关请求分别进入两个不同应用进程；没有向生产响应添加 PID/worker header。
- 本增量尚未覆盖 PostgreSQL 断连、deadlock/serialization、连接池耗尽、Redis 中断与恢复、应用或 outbox worker 中途重启、备份恢复和 100,000 编号规模。
- 登录限流仍为进程内实现；本实验不声称跨 worker 限流正确。
- outbox worker 在本增量中作为独立进程随拓扑运行；跨 worker claim 的数据库协议由 PostgreSQL 测试覆盖，但通知外部系统的 exactly-once 不在承诺范围，仍是 at-least-once。

## 结论

- 状态：`in_progress`。PR #20 CI run 33484488151 全绿，第二刀外部拓扑已验证。PR #20 已于 2026-09-01 08:23:59 UTC 合并，merge `b7a9c52`。
- 即使本次 CI 全绿，R2-05 仍不得标 `done`；后续继续故障注入、恢复和备份验证。
