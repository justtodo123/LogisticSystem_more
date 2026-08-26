# R2-04A 错误迁移清单

> 更新：2026-08-26 | 状态：R2-04A 仍为 pending，本清单只盘点调用方，不表示兼容层可以移除。

本清单记录仍使用旧 `HTTPException.detail`、`error_response` 或 `str(e)` 对外返回的点，并标注后续迁移边界。
兼容层（`exception_mapping.resolve_legacy_http_error`）必须在本清单清空、契约测试通过且文档只描述统一 envelope 后才能删除。

## 迁移边界

| 后续卡 | 负责范围 | 不在本卡做的事 |
|---|---|---|
| R2-04A | 错误 registry、`DomainError`、全局 handler、统一 envelope、旧 `detail` 兼容、`get_db` rollback；只修代表性高风险泄露 | 不迁移全部业务判断，不改成功响应语义 |
| R2-01 | 调度 / 到货 / AI 建议的状态冲突改为 `DomainError(CODE_STATE_CONFLICT)`，HTTP 409 + `40901` | 不自建错误 JSON，不重编号现有 code |
| R2-02 | 幂等中间件改为登记码 `40902` / `40903`，需要时带 `Retry-After` | 不把冲突映射成 200 |
| R2-04B | `dependencies.py`、登录/ERP/审计鉴权从 `HTTPException` 迁到 `DomainError`；前端不再依赖 `detail` | 不重做错误 envelope 或 Session rollback |
| 原业务卡保留 | 订单/货物/包裹/车辆/节点/路径/重调度等 HTTP 200 + `error_response` 业务错误 | R2-04A 不强制改成 4xx |

## 本卡已处理的高风险点

| 位置 | 原行为 | 现行为 |
|---|---|---|
| `src/backend/api/ai.py` `/parse` | `HTTPException(500, detail=str(e))` | `DomainError(CODE_INTERNAL_ERROR)`，HTTP 500 + 安全文案 |
| `src/backend/api/ai.py` explain/review/analyze except | `meta.degraded_reason=str(e)` | 固定公开文案 `AI服务暂时不可用` |
| `src/backend/api/export.py` | `HTTPException(404, detail=str(e))` | `DomainError(CODE_NOT_FOUND)`，HTTP 404 + `资源不存在` |
| `src/backend/api/arrival_confirm.py` | HTTP 200 + `message` 拼接 `str(e)` | 仍返回 HTTP 200 + `50000`，但 message 不再含异常原文 |

## 旧 HTTPException.detail（兼容层仍承接）

| 位置 | 说明 | 后续卡 |
|---|---|---|
| `src/backend/api/dependencies.py` | 401/403 字符串 detail，含角色/权限描述 | R2-04B |
| `src/backend/api/erp_webhook.py` | 401/403 字符串 detail | R2-04B |
| `src/backend/services/arrival_confirm_service.py` | 404/400/500，detail 含包裹编码、状态、`str(e)` | R2-01 |
| `src/backend/api/auth.py` | 仍 import `HTTPException`，鉴权细节随 R2-04B | R2-04B |
| `src/backend/api/orders.py` / `goods.py` / `packages.py` / `vehicles.py` / `drivers.py` | 仍 import `HTTPException`，具体抛出点随原业务卡 | 原业务卡 |

## HTTP 200 + error_response / 手写 envelope（保持现状）

这些路径已是 `{code,message,data}`，但 HTTP status 多为 200，且部分 message 仍拼接内部异常。R2-04A 不改其 HTTP 语义。

| 位置 | 风险 | 后续卡 |
|---|---|---|
| `src/backend/api/audit_logs.py` | `error_response(40301, ...)`，HTTP 200 | R2-04B |
| `src/backend/api/schedule_override.py` | `error_response(40400, ...)` 含业务编码 | 原业务卡 |
| `src/backend/api/ai.py` explain/review 缺参 | `error_response(40001, ...)`，HTTP 200 | 原 AI 卡 |
| `src/backend/services/ai_suggestion_service.py` | `error_response(40401, ...)`，`40401` 未进 registry | R2-01 |
| `src/backend/services/schedule_service.py` | 多处 `error_response(..., str(e))`，另有未登记 `40401` | R2-01 |
| `src/backend/services/replan_service.py` | `error_response(..., str(e))`，另有未登记 `40401` | R2-03 |
| `src/backend/services/route_service.py` | `error_response(..., str(e))` 及编码回显 | 原路径卡 |
| `src/backend/services/simulation_service.py` | `error_response(..., str(e))` | 原模拟卡 |
| `src/backend/services/dispatch_service.py` | `error_response` 业务错误 | R2-01 |
| `src/backend/services/exception_service.py` | `error_response` 业务错误 | R2-01 / R2-03 |
| `src/backend/services/node_service.py` / `vehicle_service.py` / `driver_service.py` / `order_service.py` / `goods_service.py` / `package_service.py` | HTTP 200 + `str(e)` | 原 CRUD 卡 |

## 其它 str(e) 暴露点

| 位置 | 说明 | 后续卡 |
|---|---|---|
| `src/backend/services/deepseek_service.py` | `error` 字段含 `str(e)`，可经 `/api/ai/parse` 的 `meta.degraded_reason` 返回 | 原 AI 卡 |
| `src/backend/algorithms/node_dispatch.py` | `ValueError` 包装 `str(e)`，若上层直接回传会泄露 | R2-01 |
| `src/backend/services/notification/dispatcher.py` | 返回 `{"_error": str(e)}`，需确认不进入 API | 原通知卡 |

## 文档残留

| 位置 | 说明 |
|---|---|
| `docs/07-规范说明.md` | 本卡已改为统一 envelope |
| `docs/开发规范.md` | 仍有旧 `{detail: ...}` 示例，随文档卡清理 |
| `docs/history/api-contract/` | 历史契约，不改 |

## 兼容层移除条件

1. 上表 HTTPException 调用点全部改为 `DomainError` 或框架标准校验异常。
2. 前端 / ERP 契约测试只断言 `{code,message,data,meta}`。
3. `docs/07-规范说明.md` 与现行 API 文档不再描述 `detail`。
4. 存量 HTTP 200 业务错误如需改 HTTP status，由对应业务卡单独验收，不作为本卡兼容层删除条件。
