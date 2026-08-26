---
plan_id: "R2-04A"
title: 领域错误、统一响应契约与数据库会话回滚
status: done
priority: P0
owner: justtodo123
created: 2026-08-25
updated: 2026-08-26
depends_on: ["R2-00"]
---

# R2-04A — 领域错误、统一响应契约与数据库会话回滚

## 来源证据与当前行为

- 项目成功响应约定为 `code/message/data/meta`，但 FastAPI `HTTPException.detail` 字符串/字典仍作为另一套对外错误形状存在。
- R2-01/R2-02 已冻结 `40901`、`40902`、`40903`，但业务卡不能各自硬编码错误结构与数字。
- 当前 `get_db` 最终会 close Session，但异常路径未形成统一的 rollback → re-raise → close 契约。
- 数据库、第三方和未处理异常若直接透传，可能泄露 SQL、DSN、请求内容或第三方原文。

决策基线：[D-R2-ERROR](./decisions.md)、[D-R2-ERROR-COMPAT](./decisions.md)。

## 问题与目标

建立所有后续业务卡可复用的领域错误基座：HTTP status 与业务 code 各司其职，客户端始终得到统一 envelope；兼容旧 `detail` 的同时提供明确移除路径；任何异常数据库 Session 都先 rollback 再关闭。

## 范围（P0 基础卡）

- 错误码登记：业务 code、HTTP status、公开 message、owner、调用方与兼容别名。
- `DomainError`：业务 code、HTTP status、公开 message、可选 meta；内部 cause/log context 不进入响应。
- 全局异常映射：`DomainError`、`HTTPException`、请求校验、数据库异常和未处理异常。
- 统一错误 envelope：`{code, message, data: null, meta}`；HTTP status 保持协议语义。
- 旧 `HTTPException.detail` 字符串/字典的兼容转换、路由迁移清单、调用方验证和移除条件。
- `get_db` 的 rollback、重新抛出和 finally close；rollback 自身失败时保留原异常并记录脱敏诊断。
- 参数化契约、脱敏和 Session 状态测试。

## 非目标

- 不在本卡迁移所有业务路由的领域判断；先建基座和兼容层，具体调用点随 R2-01～04B 迁移。
- 不改变成功响应语义，也不把所有 4xx 转成 HTTP 200。
- 不在客户端暴露 traceback、SQL、数据库/Redis DSN、第三方完整响应或内部 cause。
- 不实现 RBAC、token_version 或前端权限展示（R2-04B）。

## 依赖与进入条件

- R2-00 已完成；错误 shape 与兼容策略已版本化冻结。
- 已盘点现有错误码、FastAPI handlers、`HTTPException.detail` 形状、响应模型和 `get_db` 使用点。

## 错误码首批登记

| 业务 code | HTTP status | 公开语义 | Owner / 首批调用方 |
|---|---:|---|---|
| `40901` | 409 | 资源状态已变化，当前操作不能继续 | R2-01；调度/到货/AI 建议状态转移 |
| `40902` | 409 | 相同幂等请求正在处理，请稍后重试 | R2-02；幂等中间件，可带 `Retry-After` |
| `40903` | 409 | 幂等键已用于不同请求 | R2-02；幂等中间件 |

实际实现须引用 `core/error_codes.py`（或项目最终统一 registry）中的符号名，不在服务/路由硬编码裸数字。通用 validation、not found、unauthorized、forbidden、database unavailable 和 internal error code 在实施盘点后登记，不能临时复用上述 409 code。

## 兼容策略

1. 新增 `DomainError` 和统一 handler 后，新代码只抛领域异常或框架标准异常，不直接构造第二套 JSON。
2. 旧 `HTTPException.detail` 为字符串时，映射为登记的通用业务 code，`message` 使用安全公开文案；原 HTTP status 保留。
3. `detail` 为历史字典时，只读取白名单字段（如已登记的 code/message/meta）；未知键不透传，缺失字段使用安全默认值。
4. 请求校验错误返回统一 envelope，字段错误可放入经过裁剪的 `meta.errors`，不回显敏感原始值。
5. 数据库和未处理异常对外使用通用文案；内部日志记录 request/trace ID 与脱敏 cause。
6. 建立旧调用点与前端/ERP 消费方清单。清单全部迁移、契约测试通过且文档只描述统一 envelope 后，才能移除兼容分支。

## 有序实施步骤

1. 盘点并去重错误码与 handlers，建立 registry 和迁移清单，锁定首批 409 code 的符号名。
2. 定义 `DomainError`，明确公开字段、内部 cause、日志 context 和 meta 白名单。
3. 注册全局异常处理器并保证 handler 顺序正确；统一 envelope 与 Content-Type，保留正确 HTTP status/header。
4. 实现旧 `detail` 兼容转换和安全默认值；对未知字典 fail safe，不把对象 `str()` 后直接返回客户端。
5. 修订 `get_db`：正常 yield；异常 rollback 并 bare re-raise；finally close。覆盖 flush/commit/handler 异常以及 rollback 异常日志。
6. 参数化测试各异常类型、status/code 对齐、header、validation meta、SQL/DSN/第三方/JWT 脱敏和 Session 可复用/关闭状态。
7. 更新错误码表、API 规范和调用方迁移清单；R2-01、R2-02、R2-04B 只引用本卡能力。

## 验收标准（P0）

- 所有受测错误响应只有 `code/message/data/meta`，`data` 为 `null`；HTTP status 不被统一改成 200。
- 40901/40902/40903 有唯一符号、登记 owner 和测试；调用方不硬编码数字。
- `DomainError`、旧 `HTTPException.detail` 字符串/字典、validation、数据库和未处理异常均得到稳定映射。
- `Retry-After` 等必要协议 header 可保留；未知 `detail` 字典不会原样透传。
- 响应和日志测试确认不泄露 SQL、口令、DSN、JWT/cookie、私钥、第三方原始正文或 traceback。
- `get_db` 异常路径严格执行 rollback → re-raise → close；原异常不被 rollback 异常覆盖。
- 旧调用方清单、兼容移除条件与前端/ERP 契约测试均有记录。

## 验证命令

```bash
cd src/backend
python -m pytest -q tests/api tests/unit/core tests/unit -p no:cacheprovider
```

按实际测试布局记录精确命令；若本卡不改前端，不将前端构建写成错误基座通过的替代证据。

## 文档与问题记录同步

同步 `docs/07-规范说明.md`、错误码定义/API 文档、数据库 Session 约定、调用方迁移清单、第二轮 README 与实验记录。

## 回滚与恢复

- 全局 handler 可按异常类别分步启用；回滚时保留错误码 registry 和契约测试，禁止恢复泄露内部异常的响应。
- 兼容层在调用方迁移完成前保留；发现客户端不兼容时回退具体映射，不并列公开两套长期契约。
- `get_db` 修订若触发现有测试失败，先定位事务所有权；不得以删除 rollback 作为最终修复。

## 完成记录

- R2-04A 已完成并合并；P0 错误契约、兼容层与 Session rollback 验证均通过。
- 调用方迁移清单：[04A-error-migration-inventory.md](./04A-error-migration-inventory.md)。兼容层保留；移除条件见该清单，本卡不删除 `exception_mapping.resolve_legacy_http_error`。
- Registry：无独立 version 字段，以 `src/backend/core/error_codes.py` @ `a8c5972` 为准。已登记通用码与冻结码 `40901` / `40902` / `40903`，owner 分别为 R2-01、R2-02、R2-02。
- 实现 commit：`a8c5972949a704da0232f06c301a4a9f312e74c7`（契约与 rollback）、`e2555eb`、`91730f60f4d3928280ccc6c815b306c680320d91`（rollback 失败日志断言）。
- PR URL：https://github.com/justtodo123/LogisticSystem_more/pull/6（MERGED，2026-08-26 08:36:59 UTC）。
- Merge commit：`ea6d8c5cb184040c2dde35d51d90df1d7fdc2d7c`。
- CI run：https://github.com/justtodo123/LogisticSystem_more/actions/runs/32948346709（SUCCESS，head `91730f6`）；合并后 main CI：https://github.com/justtodo123/LogisticSystem_more/actions/runs/32948669210（SUCCESS）。
- 全量后端 CI：`746 passed, 214 warnings`；数据库迁移基线、前端类型检查与构建均成功。
- 聚焦测试文件：`tests/api/test_error_contract.py`、`tests/unit/core/test_error_codes.py`、`tests/unit/core/test_domain_errors.py`、`tests/unit/core/test_database_session.py`、`tests/unit/test_response_contract.py`，以及 AI/export/arrival 脱敏回归。本收口会话未重跑本机 pytest，验收依据为已合并代码与上述远程 CI。
- 兼容层保留：旧 `HTTPException.detail` 字符串/字典仍由兼容映射承接；待鉴权/业务调用点与前端/ERP 契约全部迁到统一 envelope 后才能删除。
- PostgreSQL、Redis、多 worker 验证不在本卡 P0 本机协议范围内。
- 详细命令、环境、退出码、验收对照与限制见 [R2-04A 实验记录](./experiments/20260826-R2-04A-error-contract-verification.md)。
