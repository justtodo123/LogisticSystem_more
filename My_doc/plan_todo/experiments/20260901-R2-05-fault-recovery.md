# 20260901-R2-05-fault-recovery

## 元数据

- 计划 ID：R2-05
- 计划/决策版本：D-R2-ENV / D-R2-DB
- 日期与时区：2026-09-01 Asia/Shanghai
- 执行人：Codex
- 层级：P1 外部拓扑（第三刀，GHA 已验证，整卡未验收完成）
- Git 分支：feat/R2-05-fault-recovery
- Commit SHA：19a67bc65aded5c317df811a946015579f7d1814；修复：cdacba77f4cc60b92dccad023af292dd416b88a5
- Merge SHA：e0219663977b42aada90bf2124a4cffcabde2fb7
- PR URL：https://github.com/justtodo123/LogisticSystem_more/pull/23
- CI run URL：https://github.com/justtodo123/LogisticSystem_more/actions/runs/33494304652
- main CI run URL：https://github.com/justtodo123/LogisticSystem_more/actions/runs/33495246187
- CD run URL：https://github.com/justtodo123/LogisticSystem_more/actions/runs/33495660568

## Schema 与数据来源

- Alembic 当前 revision：由 `scripts/release_migrate.py` 升级到仓库唯一 head；restore 库读到 `r2_04b_token_version`
- 目标数据库：GitHub Actions `postgres:16-alpine` fresh service；备份恢复使用专用库 `logistics_restore`
- 目标缓存：GitHub Actions `redis:7-alpine` service
- 数据：合成演示数据与 harness 写入的唯一 node/outbox/编号行

## 场景

- Worker A 首次写入 storage-center，杀掉重启 worker A，相同幂等键从 worker B 重放，数据库只有一行
- Outbox claim 后终止，lease 过期后新 worker reclaim；stale claim token 不能完成事件
- Redis pause：health=`degraded`，login/me 仍走数据库；unpause 后 health=`available`
- PostgreSQL deadlock/serialization 有限重试；连接池 timeout；pause 时订单请求 ReadTimeout，恢复后订单可查
- 专用库 dump/restore：业务编号、幂等记录、outbox 恢复后可继续分配且不重复
- 100k 编号已在独立 workflow_dispatch 实测；详见下方规模测试记录
- 跨 worker 登录限流明确 `not_in_scope`

## 命令

本机无 Docker/PostgreSQL/Redis，live harness 只在 GHA 执行。目标 job：

```text
python -m pytest -q -p no:cacheprovider tests/p1/test_postgres_faults.py tests/unit/core/test_db_retry.py
python scripts/p1_fault_harness.py
python scripts/p1_backup_restore.py
```

100k 不进普通 PR，手工触发 `.github/workflows/p1-code-scale.yml`：

```text
gh workflow run p1-code-scale.yml --ref feat/docs-r2-05-fault-recovery-evidence -f scale=100000 -f workers=8
```

## 原始结果与产物

- GitHub Actions：PR #23 CI [run 33494304652](https://github.com/justtodo123/LogisticSystem_more/actions/runs/33494304652) 与 main CI [run 33495246187](https://github.com/justtodo123/LogisticSystem_more/actions/runs/33495246187) 四个 job 全绿；CD [run 33495660568](https://github.com/justtodo123/LogisticSystem_more/actions/runs/33495660568) 成功。
- 规模 workflow：分支 `feat/docs-r2-05-fault-recovery-evidence`，commit `c3c3aba6d8a6de3e9cb9067b4a5d2c8e739c3910`，run [33581256635](https://github.com/justtodo123/LogisticSystem_more/actions/runs/33581256635) 成功；PostgreSQL 16-alpine，8 workers，100,000 次唯一号段 CAS，测试耗时 516.578 秒（pytest 总耗时 516.94 秒），吞吐 193.6 claims/s，P95 158.342 ms，P99 294.859 ms。
- 规模断言：`unique=100000`、`contiguous=1..100000`、`resume_next=100001`，测试 `1 passed`。
- Artifact `p1-postgres-redis-worker-logs` 中 `fault-summary.txt`（458 bytes，SHA-256 `eb389460397ff0827b3a3aa27afda15862fb82b85189ed70aa381de59549e5db`）：
  - `redis_paused_health=degraded`
  - `db_login_during_redis_pause=ok`
  - `redis_recovered_health=available`
  - `worker_restart_idempotent_replay=ok`
  - `outbox_stale_token_blocked=ok`
  - `outbox_lease_reclaimed=ok`
  - `postgres_paused_orders_error=ReadTimeout`
  - `orders_after_postgres_recover=100`
  - `cross_worker_login_rate_limit=not_in_scope`
- `backup-restore-summary.txt`（221 bytes，SHA-256 `e4afb1813607adf3be2dd02c45f4a610ed8ed1a7f4103c9576b1487d5dfa9bb2`）：
  - `source_code=GS20990601001`
  - `alembic_version=r2_04b_token_version`
  - `next_code_after_restore=GS20990601002`
- 本机：未执行 Docker pause、pg_dump 或 100k 分配；100k 结果仅来自上述 GHA run。

## 证据边界

- Postgres pause 的断言是客户端 ReadTimeout，不是应用返回的 `50001` 包络；恢复后订单可查。
- 连接池耗尽只在独立 1 连接引擎上证明 timeout，不是生产默认 pool_size=5 的容量数字。
- 100k 号段 CAS 数字来自 GitHub-hosted `ubuntu-latest` 单次 workflow 运行，不外推为生产容量或 SLA；延迟为每次领取任务从开始到 commit 成功的客户端墙钟时间。
- 登录限流仍为进程内实现，不声称跨 worker 正确。
- Redis 恢复后的无界回源防护是 per-key single-flight 的单元测试 + GHA health 恢复，不是压测证明。

## 结论

- 状态：`in_progress`。PR #23 已于 2026-09-01 10:01:14 UTC 合并，merge `e021966`；main CI run 33495246187 四个 job 全绿；CD run 33495660568 成功。
- 100k 实测已完成；R2-05 仍不得标 `done`，剩余跨 worker 登录限流。
