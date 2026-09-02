# 20260902-R2-05-cross-worker-login-rate-limit

## 元数据

- 计划 ID：R2-05
- 计划/决策版本：D-R2-ENV / D-R2-DB
- 日期与时区：2026-09-02 Asia/Shanghai
- 执行人：Codex
- 层级：P1 外部拓扑（GHA 已验证）
- Git 分支：feat/R2-05-cross-worker-login-rate-limit
- Commit SHA：0bab96a10cede4f3453015a54b36c477cc651019；修复：fffee0e
- Merge SHA：372ae9f81ba3da80ceaca64595cefa256dd01a2d
- PR URL：https://github.com/justtodo123/LogisticSystem_more/pull/25
- CI run URL：https://github.com/justtodo123/LogisticSystem_more/actions/runs/33589202969
- main CI run URL：https://github.com/justtodo123/LogisticSystem_more/actions/runs/33590407219
- CD run URL：https://github.com/justtodo123/LogisticSystem_more/actions/runs/33590735173

## Schema 与数据来源

- Alembic 当前 revision：不涉及新迁移
- Alembic heads：仓库唯一 head
- 目标数据库：GitHub Actions postgres:16-alpine fresh service
- 目标缓存：GitHub Actions redis:7-alpine service
- 数据：合成用户与失败登录，不含真实凭据

## 环境

- OS：GitHub-hosted ubuntu-latest
- Python：3.13
- 数据库：PostgreSQL 16
- Redis：Redis 7，key 前缀 loginrl:，主体 HMAC-SHA256(JWT_SECRET, IP and username separated by NUL)
- 应用 worker：2 个可单独寻址的 Uvicorn worker（18001/18002）
- 限流参数：LOGIN_RATE_LIMIT_ATTEMPTS=5，LOGIN_RATE_LIMIT_WINDOW_SECONDS=60
- Redis 探测超时：socket_timeout=1.0s；降级冷却 REDIS_RECOVER_SECONDS=2.0

## 场景

- 不改变登录 API、错误码 42900 和前端行为
- Redis 可用：Lua 原子 INCR/EXPIRE/PTTL/DEL，两 worker 交替失败登录共同触发阈值
- Redis pause：登录仍可用且 meta.degraded=true / degraded_reason=redis
- Redis 恢复后重新使用共享计数并锁定；其他用户不串扰
- 成功登录解锁；Redis key 不保存明文用户名

## 命令

```text
python -m pytest -q -p no:cacheprovider tests/unit/core/test_login_rate_limit.py tests/unit/core/test_domain_errors.py tests/api/test_login_rate_limit.py tests/api/test_auth.py
python -m pytest -q -p no:cacheprovider tests/p1/test_login_rate_limit_redis.py
P1_WORKER_A_URL=http://127.0.0.1:18001 P1_WORKER_B_URL=http://127.0.0.1:18002 python -m pytest -q -p no:cacheprovider tests/p1/test_multi_worker_http.py tests/p1/test_login_rate_limit_http.py
python scripts/p1_fault_harness.py
```

## 原始结果与产物

- 命令是否实际执行：是
- 退出码：CI 四个 job 均为 0
- GitHub Actions：PR #25 CI [run 33589202969](https://github.com/justtodo123/LogisticSystem_more/actions/runs/33589202969)：数据库迁移基线、后端测试 (pytest)、P1 PostgreSQL + Redis 协议与多 worker 验证、前端类型检查 + 构建 全绿
- Artifact p1-postgres-redis-worker-logs 中 fault-summary.txt（543 bytes，SHA-256 be8c89d8cae8fb7d553ba7badbd2a6da29d52ee95d77ea931840e6a6912f62d9）：
  - redis_paused_health=degraded
  - login_rate_limit_redis_paused_degraded=ok
  - login_rate_limit_redis_recovered=ok
  - cross_worker_login_rate_limit=ok
- scenario-summary.txt（333 bytes，SHA-256 5bf79184f8caa3d20bee63d31eee536392aab093231071c8a27007d259d22191）：PostgreSQL 16 + Redis 7 + 2 workers，assertions 含 shared login rate limit
- 本机 pytest：20 passed + 17 passed，退出码 0
- 保留期：GHA artifact 7 days
- 脱敏检查：已检查；报告不含密码、JWT 或 Redis 明文主体

## 结论

- 状态：通过
- 结论与对应证据：跨 worker 共享登录限流、Redis pause 降级与恢复后重新共享已在 GHA 验证
- 已知限制：本机无 Docker；P1 结果不外推为生产容量
- 未通过项 / 未执行项：无
- 下一步：R2-06 request/trace/task ID、最小指标与 load/spike

