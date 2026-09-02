# 20260902-R2-05-cross-worker-login-rate-limit

## 元数据

- 计划 ID：R2-05
- 计划/决策版本：D-R2-ENV / D-R2-DB
- 日期与时区：2026-09-02 Asia/Shanghai
- 执行人：Codex
- 层级：P0 本机协议 + P1 外部拓扑（P1 尚未在 GHA 执行）
- Git 分支：feat/R2-05-cross-worker-login-rate-limit
- Commit SHA：0bab96a10cede4f3453015a54b36c477cc651019
- PR URL：尚无
- CI run URL：未执行

## Schema 与数据来源

- Alembic 当前 revision：不涉及新迁移
- Alembic heads：仓库唯一 head
- 数据库来源：本机 API/单元测试使用 SQLite；P1 目标为 GitHub Actions postgres:16-alpine fresh service
- 目标缓存：GitHub Actions redis:7-alpine service（尚未执行）
- 数据：合成用户与失败登录，不含真实凭据

## 环境

- OS / CPU / 内存：本机 Win11 家庭版，无 Docker / WSL / PostgreSQL / Redis
- Python：3.13.3
- 数据库：本机 SQLite（pytest）；P1 目标 PostgreSQL 16
- Redis：本机无；P1 目标 Redis 7，key 前缀 loginrl:，主体为 HMAC-SHA256(JWT_SECRET, IP and username separated by NUL)
- 应用 worker：P1 目标 2 个可单独寻址的 Uvicorn worker（18001/18002）
- 限流参数：LOGIN_RATE_LIMIT_ATTEMPTS=5，LOGIN_RATE_LIMIT_WINDOW_SECONDS=60
- Redis 探测超时：登录限流客户端 socket_timeout=1.0s；降级冷却 REDIS_RECOVER_SECONDS=2.0

## 场景

- 不改变登录 API、错误码 42900 和前端行为；只把计数从进程内升级为 Redis 共享状态
- Redis 可用：Lua 原子完成 INCR / EXPIRE / PTTL / DEL，多 worker 共享同一主体窗口
- Redis 不可用：回退进程内固定窗口，登录仍可用；meta.degraded=true，degraded_reason=redis，不得声称全局限流
- Redis 恢复后重新走共享计数
- 成功登录解锁；错误密码累计；不同用户不串扰
- Redis key 不保存明文用户名或 IP

## 命令

本机已执行：

```text
cd src/backend
python -m pytest -q -p no:cacheprovider tests/unit/core/test_login_rate_limit.py tests/unit/core/test_domain_errors.py tests/api/test_login_rate_limit.py tests/api/test_auth.py --tb=short
python -m pytest -q -p no:cacheprovider tests/api/test_error_contract.py tests/unit/core/test_error_codes.py --tb=short
```

P1 目标命令（本机无 Docker，未执行；由 CI job P1 PostgreSQL + Redis 协议与多 worker 验证 运行）：

```text
python -m pytest -q -p no:cacheprovider tests/p1/test_login_rate_limit_redis.py
P1_WORKER_A_URL=http://127.0.0.1:18001 P1_WORKER_B_URL=http://127.0.0.1:18002 python -m pytest -q -p no:cacheprovider tests/p1/test_login_rate_limit_http.py
python scripts/p1_fault_harness.py
```

## 原始结果与产物

- 命令是否实际执行：本机 pytest 是；P1 GHA 否
- 退出码：本机两轮 pytest 均为 0
- 摘要：tests/unit/core/test_login_rate_limit.py 5 passed；test_domain_errors.py 5 passed；tests/api/test_login_rate_limit.py 3 passed；tests/api/test_auth.py 7 passed；随后 test_error_contract.py 9 passed、test_error_codes.py 8 passed
- 追踪内摘要路径：尚无
- 外部原始产物位置 / CI artifact URL：未执行
- 产物大小：尚无
- SHA-256：尚无
- 保留期限 / 删除日期：尚无
- 脱敏检查：已检查；报告不含密码、JWT 或 Redis 明文主体
- 访问限制或复现障碍：本机无 Docker，无法 pause Redis 或启动双 worker

## 结论

- 状态：本机单测通过；P1 双 worker / Redis pause 未执行
- 结论与对应证据：进程内窗口、阈值、TTL、解锁和 Redis 异常降级已由单元测试覆盖；跨 worker 共享计数与 Redis pause 降级/恢复需等 GHA
- 已知限制：本机无 Redis，不能把 SQLite/单进程结果外推为跨 worker 能力
- 未通过项 / 未执行项：P1 Redis Lua、双 worker HTTP、fault harness
- 下一步：创建 PR，等待 CI 四个 job 通过后再把 R2-05 标 done

