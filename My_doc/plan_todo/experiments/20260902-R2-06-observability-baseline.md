# 20260902-R2-06-observability-baseline

## 元数据

- 计划 ID：R2-06
- 计划/决策版本：D-R2-OBS / D-R2-CI
- 日期与时区：2026-09-02 Asia/Shanghai
- 执行人：Codex
- 层级：P1 第一刀（协议与观测基线；load/spike 未执行）
- Git 分支：feat/R2-06-observability-baseline
- Commit SHA：尚无
- PR URL：尚无
- CI run URL：尚无

## Schema 与数据来源

- Alembic：本刀无 schema 变更
- 数据库来源：本机 SQLite pytest；P1 live / k6 未执行
- 数据是否为合成/脱敏数据：是

## 环境

- OS：Windows 11；无 Docker / WSL / PostgreSQL / Redis / k6 / Locust
- Python：3.13
- 目标拓扑：GitHub Actions ubuntu-latest + postgres:16-alpine + redis:7-alpine + k6

## 场景

- 统一 X-Request-ID / X-Trace-ID / X-Task-ID 生成与回写
- JSON 日志 + 敏感字段脱敏 + SQL 注释
- /metrics 核心计数（HTTP、40901、幂等命中、缓存命中/降级、outbox backlog/dead-letter）
- k6 load/spike 脚本与 P1 load and spike workflow（未跑）

## 命令

`	ext
cd src/backend
python -m pytest -q -p no:cacheprovider tests/unit/core/test_request_context.py tests/unit/core/test_json_logging.py tests/unit/core/test_metrics.py tests/unit/core/test_sql_comments.py tests/unit/services/test_observability_service.py tests/api/test_observability.py tests/api/test_error_contract.py tests/api/test_health.py
`

## 原始结果与产物

- 命令是否实际执行：是。全量 pytest 991 passed / 16 skipped（P1 live skip），331.48s，2026-09-02
- load/spike：未执行
- 脱敏检查：脚本不含凭据；GHA 使用示例口令 logistics/logistics

## STAR 素材（引用已有 P0/P1 证据，待 load 数字补齐）

1. 并发确认冲突：R2-01 CAS，同 draft 第二次确认 HTTP 409 / 40901，PR #8。
2. 幂等重放：R2-02A 数据库状态机，同 key 重放原响应，PR #10/#12。
3. P1 编号规模：100,000 claims，GHA run 33581256635，P95 158.342 ms，193.6 claims/s。

## 结论

- 状态：in_progress。观测基线本机 pytest 已绿；load/spike 未执行，不能标 done
- 已知限制：本机无 k6 与 PostgreSQL；/metrics 计数为进程内，多 worker 需分别抓取或后续聚合
- 下一步：本机 pytest；PR CI 含 P1 /metrics 探针；workflow_dispatch 跑 5 分钟 load + spike 后回填绝对值
