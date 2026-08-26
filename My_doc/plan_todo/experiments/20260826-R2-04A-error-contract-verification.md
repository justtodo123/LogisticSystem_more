---
name: 20260826-r2-04a-error-contract-verification
description: R2-04A error contract, compatibility layer, and session rollback evidence
metadata:
  type: project
---

# R2-04A 实验与验证记录

## 元数据

- 计划 ID：R2-04A
- 计划/决策版本：`v2026-08-25-r2-freeze` / `D-R2-ERROR` / `D-R2-ERROR-COMPAT`
- 日期与时区：2026-08-26；Asia/Shanghai
- 执行人：justtodo123
- 层级：P0 本机协议
- Git 分支：`feat/R2-04A-error-contract`
- Commit SHA：实现 `a8c5972949a704da0232f06c301a4a9f312e74c7`；后续测试 `e2555eb`、`91730f60f4d3928280ccc6c815b306c680320d91`
- PR URL：https://github.com/justtodo123/LogisticSystem_more/pull/6（MERGED）
- CI run URL：https://github.com/justtodo123/LogisticSystem_more/actions/runs/32948346709（SUCCESS）
- Merge commit：`ea6d8c5cb184040c2dde35d51d90df1d7fdc2d7c`
- 合并后 main CI：https://github.com/justtodo123/LogisticSystem_more/actions/runs/32948669210（SUCCESS）

## Schema 与数据来源

- Alembic 当前 revision：沿用 R2-00A 唯一 head `r2_00a_schema_convergence`
- Alembic heads：唯一 head；本卡未新增 revision
- 数据库来源：pytest 隔离 SQLite / FastAPI TestClient；无业务库升级
- 升级前 revision / schema 指纹：不适用（本卡不改 schema）
- 数据规模与种子方式：契约测试使用内存/测试 app；AI/export/arrival 回归使用既有 fixture
- 数据是否为合成/脱敏数据：是

## 环境

- OS：GitHub Actions Ubuntu 24.04；本收口会话未重跑本机 pytest
- Python：CI 使用 setup-python 的 3.13.x
- 数据库：测试 SQLite；无 PostgreSQL
- Redis：无
- 应用 worker / 后台 worker 数：单进程 pytest / TestClient
- 关键依赖或容器镜像版本：仓库当前 backend 依赖；Docker runtime 未作为本卡证据

## 场景

- 目标与不变量：所有受测错误响应只有 `{code,message,data,meta}` 且 `data=null`；HTTP status 不被改成 200；`40901/40902/40903` 有符号与 owner；旧 `detail` 兼容且未知字典 fail closed；SQL/DSN/JWT/cookie/私钥/第三方原文/traceback 不进入响应；`get_db` 异常路径 rollback → re-raise → close，rollback 失败保留原异常。
- 请求分布 / 并发客户端：无并发压测；本卡只验证协议与脱敏。
- 预热 / 持续时间：不适用
- 故障注入点：SQLAlchemyError、未处理 RuntimeError、rollback 自身失败、timeout middleware
- 对照组 / 基线：旧 `HTTPException.detail` 字符串/字典与成功响应向后兼容

## 命令

```text
# PR #6 / main 合并后的全量后端 CI
cd src/backend
python -m pytest -q -p no:cacheprovider

# 本卡聚焦契约与 Session 测试（实现阶段已纳入上述全量 CI）
python -m pytest -q -p no:cacheprovider ^
  tests/api/test_error_contract.py ^
  tests/unit/core/test_error_codes.py ^
  tests/unit/core/test_domain_errors.py ^
  tests/unit/core/test_database_session.py ^
  tests/unit/test_response_contract.py ^
  tests/api/test_ai.py ^
  tests/api/test_export.py ^
  tests/api/test_arrival_confirm.py ^
  tests/api/test_auth.py
```

## 原始结果与产物

- 命令是否实际执行：是（远程 CI）；本收口会话未另起本机复跑
- 退出码：0（PR CI run 32948346709；main CI run 32948669210）
- 摘要（通过数 / 失败数 / 关键日志）：全量后端 `746 passed, 214 warnings in 156.77s`；数据库迁移基线成功；前端类型检查 + 构建成功。此前两次 PR CI（32947260481、32947832871）因 rollback 日志断言失败，已由 `e2555eb` / `91730f6` 修复，不以失败 run 作为验收依据。
- 追踪内摘要路径：本文件
- 外部原始产物位置 / CI artifact URL：无单独 artifact；日志见上述 CI run
- 产物大小：不适用
- SHA-256：不适用
- 保留期限 / 删除日期：以 GitHub Actions 日志保留策略为准
- 脱敏检查：已检查；报告只含公开错误文案、测试文件名、commit/PR/CI URL；无 DSN 口令、JWT、cookie 或原始异常正文
- 访问限制或复现障碍：本机 Docker / PostgreSQL / Redis 仍不可用；不把 SQLite 单进程结果外推为多 worker 证据

## 验收表核对

| 验收项 | 证据 | 结论 |
|---|---|---|
| 受测错误响应只有 `code/message/data/meta`，`data` 为 `null`；HTTP status 不被改成 200 | `test_error_contract.py` 的 `assert_envelope`；`test_response_contract.py` | 通过 |
| `40901/40902/40903` 有唯一符号、owner 和测试；调用方不硬编码数字 | `core/error_codes.py`；`test_error_codes.py` | 通过 |
| `DomainError`、旧 `detail` 字符串/字典、validation、数据库和未处理异常均稳定映射 | `test_error_contract.py` 对应用例 | 通过 |
| `Retry-After` 等必要 header 可保留；未知 `detail` 字典不原样透传 | `test_legacy_dict_requires_registered_status_and_whitelists_meta`；`test_malformed_detail_fails_closed` | 通过 |
| 响应和日志不泄露 SQL、口令、DSN、JWT/cookie、私钥、第三方原文或 traceback | `test_internal_errors_are_sanitized`；`test_domain_errors.py`；rollback 日志只记录异常类型 | 通过 |
| `get_db` 异常路径 rollback → re-raise → close；rollback 失败不覆盖原异常 | `test_database_session.py` 三条用例 | 通过 |
| 旧调用方清单、兼容移除条件与前端/ERP 契约测试均有记录 | [04A-error-migration-inventory.md](../04A-error-migration-inventory.md) | 通过（已记录；兼容层按条件保留） |

## 兼容层保留及移除条件

- 保留：`exception_mapping.resolve_legacy_http_error` 继续承接存量 `HTTPException.detail`。
- 移除条件（需同时满足，本卡不执行删除）：
  1. 清单中 HTTPException 调用点全部改为 `DomainError` 或框架标准校验异常。
  2. 前端 / ERP 契约测试只断言 `{code,message,data,meta}`。
  3. `docs/07-规范说明.md` 与现行 API 文档不再描述 `detail`。
  4. 存量 HTTP 200 业务错误如需改 HTTP status，由对应业务卡单独验收，不作为本卡删除条件。

## 结论

- 状态：通过
- 结论与对应证据：R2-04A 错误 registry、统一 envelope、旧 `detail` 兼容、脱敏与 `get_db` rollback 已合并到 `main`；PR #6 与最新成功 CI 可作为 P0 基座证据。
- 已知限制（尤其 SQLite 写锁、单 worker、无 Redis）：本卡只证明协议与脱敏；未验证 PostgreSQL、Redis、多 worker 或前端全面迁移。
- 未通过项 / 未执行项：无成功 CI 失败项；本收口会话未重跑本机 pytest；Docker runtime 未执行。
- 下一步：进入主链 R2-01；可并行 R2-04B。兼容层保持到迁移清单清空。
