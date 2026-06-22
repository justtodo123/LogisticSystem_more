# 阶段7 API 契约文档 - 异常与重规划（F013）

**版本**：V1.1  
**日期**：2026-06-22  
**阶段**：阶段7（异常与重规划 F013）  
**状态**：✅ 已完成（`package` 异常暂未实现）

---

## 1. 文档概述

本文档定义阶段7（异常事件管理与重规划）的API契约，包括：

- 异常事件 CRUD（创建、列表、详情、更新、标记已解决）
- 重规划触发（`redispatch` 全链路重调度 / `reroute` 重路径规划）
- 版本链管理（重规划后新旧方案通过 `version` + `parent_id` 关联）

所有接口遵循统一响应格式 `{code, message, data, meta}`。

> ⚠️ **`package` 异常类型暂未实现**：当前仅支持 `road`（道路异常→reroute）和 `node`（节点异常→redispatch）两种异常类型。`package` 类型（包裹异常→redispatch 全链路）已从 API 枚举中移除，后续版本补充。

---

## 2. API 端点列表

| 方法 | 路径 | 说明 | 认证 | 状态 |
|------|------|------|------|------|
| `GET` | `/api/exceptions` | 异常事件列表（分页、筛选） | Bearer Token | ✅ |
| `POST` | `/api/exceptions` | 创建异常事件 | Bearer Token (dispatcher) | ✅ |
| `GET` | `/api/exceptions/{event_code}` | 异常事件详情 | Bearer Token | ✅ |
| `POST` | `/api/exceptions/{event_code}/replan` | 触发重规划（redispatch 或 reroute） | Bearer Token (dispatcher) | ✅ |
| `PUT` | `/api/exceptions/{event_code}` | 更新异常事件 | Bearer Token (dispatcher) | ✅ |
| `PUT` | `/api/exceptions/{event_code}/resolve` | 标记异常已解决 | Bearer Token (dispatcher) | ✅ |

---

## 3. API 详细说明

### 3.1 GET /api/exceptions

**功能**：获取异常事件列表

支持分页，可按状态（`open`/`resolved`）和异常类型（`road`/`node`）筛选。

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `page` | integer | 否 | 页码（默认 1） |
| `page_size` | integer | 否 | 每页数量（默认 20，最大 100） |
| `status` | string | 否 | 状态筛选：`open` / `resolved` |
| `exception_type` | string | 否 | 异常类型筛选：`road` / `node` |

**响应格式**：

成功（200）：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "event_code": "EX1750600000123",
        "exception_type": "node",
        "exception_subtype": "capacity_limit",
        "target_type": "node",
        "target_code": "L1001",
        "recommended_action": "redispatch",
        "related_schedule_code": "GS20260622001",
        "replan_batch_code": null,
        "description": "L1001 容量不足，部分货物需重新分配 L1 节点",
        "status": "open",
        "resolved_at": null,
        "created_at": "2026-06-22T10:30:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**错误码**：

| code | HTTP 状态码 | 说明 |
|------|------------|------|
| 0 | 200 | 成功 |
| 40300 | 403 | 无权限 |

---

### 3.2 POST /api/exceptions

**功能**：创建异常事件

创建异常事件时，系统自动将关联的订单、货物、包裹状态标记为 `exception`（用于后续重规划筛选）。若 `target_type=vehicle`，还会将车辆设为 `disabled`。

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `exception_type` | string | **是** | 异常类型：`road` / `node` |
| `exception_subtype` | string | 否 | 异常子类型：`congestion` / `damage` / `capacity_limit` / `road_closed` / `road_accident` / `storage_timeout` / `node_maintenance` / `vehicle_breakdown` |
| `target_type` | string | 否 | 关联对象类型：`node` / `route` / `vehicle` |
| `target_code` | string | 否 | 关联对象业务编号 |
| `recommended_action` | string | **是** | 推荐操作：`redispatch` / `reroute` |
| `related_schedule_code` | string | 否 | 关联调度方案业务编号 |
| `description` | string | **是** | 异常描述 |

**请求体示例（redispatch - 节点异常）**：

```json
{
  "exception_type": "node",
  "exception_subtype": "capacity_limit",
  "target_type": "node",
  "target_code": "L1001",
  "recommended_action": "redispatch",
  "related_schedule_code": "GS20260622001",
  "description": "L1001 容量不足，部分货物需重新分配 L1 节点"
}
```

**请求体示例（reroute - 道路异常）**：

```json
{
  "exception_type": "road",
  "exception_subtype": "road_closed",
  "target_type": "route",
  "target_code": "RT202606220001",
  "recommended_action": "reroute",
  "related_schedule_code": "GS20260622001",
  "description": "L1001→L2034 路段施工封闭，需重新规划路线"
}
```

**参数约束**（Schema 层 validator）：

| 约束 | 说明 |
|------|------|
| `recommended_action=reroute` | 强制 `target_type=route`，且 `target_code` 必填 |
| `recommended_action=redispatch` | 建议 `target_type` 为 `node` / `vehicle` |
| `exception_type` | 仅允许 `road` / `node` |
| `target_type`（若提供） | 仅允许 `node` / `route` / `vehicle` |

**响应格式**：

成功（200）：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "event_code": "EX1750600000123",
    "exception_type": "node",
    "exception_subtype": "capacity_limit",
    "target_type": "node",
    "target_code": "L1001",
    "recommended_action": "redispatch",
    "related_schedule_code": "GS20260622001",
    "replan_batch_code": null,
    "description": "L1001 容量不足，部分货物需重新分配 L1 节点",
    "status": "open",
    "resolved_at": null,
    "created_at": "2026-06-22T10:30:00"
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**创建时自动状态变更**：

| target_type | 自动操作 |
|-------------|---------|
| 任意（有 `related_schedule_code`） | 关联订单 `delivering` → `exception`；货物 `packed`/`in_transit` → `exception`；包裹 `packed`/`in_transit`/`pending_pack` → `exception` |
| `vehicle` | 车辆状态 → `disabled`；同时按 `dispatch_id` 批量更新关联包裹和货物为 `exception` |

**错误码**：

| code | HTTP 状态码 | 说明 |
|------|------------|------|
| 0 | 200 | 成功 |
| 40000 | 400 | 参数校验失败（Schema 层 validator 触发） |
| 40001 | 200 | target_code 对应实体不存在 |
| 40401 | 200 | related_schedule_code 对应调度方案不存在 |
| 40300 | 403 | 无权限（manager 角色） |

---

### 3.3 GET /api/exceptions/{event_code}

**功能**：获取异常事件详情

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `event_code` | string | 是 | 异常事件编号（路径参数） |

**响应格式**：

成功（200）：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "event_code": "EX1750600000123",
    "exception_type": "node",
    "exception_subtype": "capacity_limit",
    "target_type": "node",
    "target_code": "L1001",
    "recommended_action": "redispatch",
    "related_schedule_code": "GS20260622001",
    "replan_batch_code": null,
    "description": "L1001 容量不足，部分货物需重新分配 L1 节点",
    "status": "open",
    "resolved_at": null,
    "created_at": "2026-06-22T10:30:00"
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**错误码**：

| code | HTTP 状态码 | 说明 |
|------|------------|------|
| 0 | 200 | 成功 |
| 40401 | 200 | 异常事件不存在 |
| 40300 | 403 | 无权限 |

---

### 3.4 POST /api/exceptions/{event_code}/replan

**功能**：触发重规划

根据请求体中的 `action` 选择重规划类型：
- `redispatch`：重新执行 F007→F021→F005→F006 全链路
- `reroute`：仅重新执行 F006 路径规划

**前置条件**：

| action | 前置条件 | 说明 |
|--------|---------|------|
| `redispatch` | 全局调度已完成 | `related_schedule_code` 对应 `GlobalSchedule` 记录必须存在；**不要求**节点调度完成（内部自行调用 F005+F006） |
| `reroute` | 节点调度已完成 | `target_code` 必须指向已存在的 `Route` 记录（Route 由 F005 完成后自动触发 F006 生成） |

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `event_code` | string | 是 | 异常事件编号（路径参数） |

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `action` | string | **是** | 重规划类型：`redispatch` / `reroute` |
| `reason` | string | **是** | 重规划原因 |

**请求体示例（redispatch）**：

```json
{
  "action": "redispatch",
  "reason": "L1001 容量溢出 120%，分流 3 票货物至 L1002"
}
```

**请求体示例（reroute）**：

```json
{
  "action": "reroute",
  "reason": "原路线途经封闭路段，绕行替代路径"
}
```

**响应格式 — redispatch 成功**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "schedule_code": "GS20260622002",
    "new_schedule_code": "GS20260622002",
    "batch_code": "BATCH20260622002",
    "version": 2,
    "is_replan": true,
    "replan_reason": "L1001 容量溢出 120%，分流 3 票货物至 L1002",
    "original_schedule_code": "GS20260622001"
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**响应格式 — reroute 成功**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "batch_code": "BATCH20260622001",
    "route_codes": ["RT202606220002"],
    "new_route_code": "RT202606220002",
    "version": 2,
    "is_replan": true,
    "replan_reason": "原路线途经封闭路段，绕行替代路径",
    "original_route_code": "RT202606220001"
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**redispatch 内部调用链**：

```
POST /api/exceptions/{event_code}/replan { action: "redispatch" }
  → ExceptionService.trigger_replan()
    → ReplanService.redispatch():
      ① 查询原 GlobalSchedule (by original_schedule_code)
      ② 提取 order_codes + algorithm_type
      ③ 提取 excluded_nodes（来自 event.target_code）
      ④ 调用 ScheduleService.create_global_schedule()
         → F007 全局调度 + F021 打包（is_replan=true，仅调度 exception 订单）
      ⑤ 更新新版 GlobalSchedule 版本链 (version+1, parent_id, is_replan)
      ⑥ 调用 DispatchService.create_node_dispatch()
         → F005 节点调度 (demo_mode=false, is_replan=true, 仅调度 exception 包裹)
         → F006 路径规划自动触发
      ⑦ 更新新版 DispatchBatch / NodeDispatch / Route 版本链
      ⑧ 回写 event.replan_batch_code
```

**reroute 内部调用链**：

```
POST /api/exceptions/{event_code}/replan { action: "reroute" }
  → ExceptionService.trigger_replan()
    ① 通过 event.target_code 查找原 Route
    ② 通过 Route.dispatch_id → NodeDispatch → DispatchBatch
    ③ 提取 excluded_vehicles（原车辆排除）
    → ReplanService.reroute():
      ④ 读取原 Route + 关联 dispatch + batch
      ⑤ 调用 RouteService.create_route_planning()
         → F006 仅为该 dispatch_code 重新规划路径
      ⑥ 更新新版 Route 版本链 (version+1, parent_id, is_replan)
      ⑦ 回写 event.replan_batch_code
```

**错误码**：

| code | HTTP 状态码 | 说明 |
|------|------------|------|
| 0 | 200 | 成功 |
| 400 | 400 | 无效的 action（非 redispatch/reroute） |
| 40001 | 200 | 异常已解决无法重规划 / redispatch 缺少 related_schedule_code / reroute 缺少 target_code / 内部调度失败 |
| 40401 | 200 | 异常事件不存在 |
| 40300 | 403 | 无权限（manager 角色） |

---

### 3.5 PUT /api/exceptions/{event_code}

**功能**：更新异常事件

支持更新 `status` 字段。当 `status` 设为 `resolved` 时，自动记录 `resolved_at`。

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `event_code` | string | 是 | 异常事件编号（路径参数） |

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `status` | string | 否 | 异常状态：`open` / `resolved` |

**请求体示例**：

```json
{
  "status": "resolved"
}
```

**响应格式**：

成功（200）：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "event_code": "EX1750600000123",
    "exception_type": "node",
    "exception_subtype": "capacity_limit",
    "target_type": "node",
    "target_code": "L1001",
    "recommended_action": "redispatch",
    "related_schedule_code": "GS20260622001",
    "replan_batch_code": "GS20260622002",
    "description": "L1001 容量不足",
    "status": "resolved",
    "resolved_at": "2026-06-22T10:35:00",
    "created_at": "2026-06-22T10:30:00"
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**错误码**：

| code | HTTP 状态码 | 说明 |
|------|------------|------|
| 0 | 200 | 成功 |
| 40401 | 200 | 异常事件不存在 |
| 40300 | 403 | 无权限 |

---

### 3.6 PUT /api/exceptions/{event_code}/resolve

**功能**：标记异常已解决

将异常状态从 `open` 改为 `resolved`，自动记录 `resolved_at` 时间戳。已解决的异常不可重复标记。

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `event_code` | string | 是 | 异常事件编号（路径参数） |

**请求体**：无

**响应格式**：

成功（200）：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "event_code": "EX1750600000123",
    "status": "resolved",
    "resolved_at": "2026-06-22T10:35:00"
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**错误码**：

| code | HTTP 状态码 | 说明 |
|------|------------|------|
| 0 | 200 | 成功 |
| 40001 | 200 | 异常已解决，重复标记拒绝 |
| 40401 | 200 | 异常事件不存在 |
| 40300 | 403 | 无权限 |

---

## 4. 数据模型

### 4.1 ExceptionEvent（数据库模型）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER PK | 主键自增 |
| `event_code` | VARCHAR(64) UNIQUE | 异常事件编号（格式：`EX` + 时间戳毫秒） |
| `exception_type` | VARCHAR(32) | 异常类型：`road` / `node` |
| `exception_subtype` | VARCHAR(64) | 异常子类型（可选） |
| `target_type` | VARCHAR(32) | 关联对象类型：`node` / `route` / `vehicle` |
| `target_code` | VARCHAR(64) | 关联对象业务编号 |
| `recommended_action` | VARCHAR(32) | 推荐操作：`redispatch` / `reroute` |
| `related_schedule_code` | VARCHAR(64) | 关联调度方案编号 |
| `replan_batch_code` | VARCHAR(64) | 重规划后新批次编号（触发 replan 后回写） |
| `description` | TEXT | 异常描述 |
| `status` | VARCHAR(32) | 状态：`open` / `resolved`（默认 `open`） |
| `resolved_at` | DATETIME | 解决时间（标记 resolved 时自动记录） |
| `created_at` | DATETIME | 创建时间 |

### 4.2 CreateExceptionEventRequest（请求体）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `exception_type` | string | **是** | `road` / `node` |
| `exception_subtype` | string\|null | 否 | 异常子类型 |
| `target_type` | string\|null | 否 | `node` / `route` / `vehicle` |
| `target_code` | string\|null | 否 | 关联对象业务编号 |
| `recommended_action` | string | **是** | `redispatch` / `reroute` |
| `related_schedule_code` | string\|null | 否 | 关联调度方案编号 |
| `description` | string | **是** | 异常描述 |

### 4.3 TriggerReplanRequest（请求体）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `action` | string | **是** | `redispatch` / `reroute` |
| `reason` | string | **是** | 重规划原因 |

### 4.4 UpdateExceptionRequest（请求体）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `status` | string\|null | 否 | `open` / `resolved` |

### 4.5 ExceptionEventResponse（响应体）

| 字段 | 类型 | 说明 |
|------|------|------|
| `event_code` | string | 异常事件编号 |
| `exception_type` | string | 异常类型 |
| `exception_subtype` | string\|null | 异常子类型 |
| `target_type` | string\|null | 关联对象类型 |
| `target_code` | string\|null | 关联对象编号 |
| `recommended_action` | string | 推荐操作 |
| `related_schedule_code` | string\|null | 关联调度方案 |
| `replan_batch_code` | string\|null | 重规划批次编号 |
| `description` | string | 异常描述 |
| `status` | string | 状态 |
| `resolved_at` | string\|null | 解决时间（ISO 8601） |
| `created_at` | string\|null | 创建时间（ISO 8601） |

---

## 5. 完整使用流程

### 5.1 Redispatch 流程（6 步）

```
Step 1  POST /api/schedule/global            ← 全局调度（前置：阶段3）
Step 2  POST /api/exceptions                  ← 创建节点异常（recommended_action=redispatch）
            副作用: 订单/货物/包裹 → exception
Step 3  [可选] GET /api/exceptions/{code}     ← 确认异常
Step 4  POST /api/exceptions/{code}/replan    ← 触发重规划 { action: "redispatch" }
            内部: F007→F021→F005→F006 全链路
            版本链: version+1, parent_id, is_replan
Step 5  [可选] GET /api/schedule/global/{new} ← 验证新方案
Step 6  PUT /api/exceptions/{code}/resolve    ← 标记已解决
```

### 5.2 Reroute 流程（7 步）

```
Step 1  POST /api/schedule/global            ← 全局调度（前置：阶段3）
Step 2  POST /api/schedule/node-dispatch     ← 节点调度（前置：阶段4，生成 Route 记录）
Step 3  POST /api/exceptions                  ← 创建道路异常（recommended_action=reroute, target_type=route）
Step 4  [可选] GET /api/exceptions/{code}     ← 确认异常
Step 5  POST /api/exceptions/{code}/replan    ← 触发重规划 { action: "reroute" }
            内部: 仅 F006 路径规划
            版本链: 新 Route version+1
Step 6  [可选] GET /api/routes/{new_code}     ← 对比新旧路线
Step 7  PUT /api/exceptions/{code}/resolve    ← 标记已解决
```

---

## 6. 版本链机制

重规划生成的每条新记录均通过以下字段形成版本链：

| 字段 | 说明 | 示例 |
|------|------|------|
| `version` | 版本号，原方案=1，每次重规划+1 | `2` |
| `parent_id` | 指向前一版本的数据库 `id`（自关联外键） | `1` |
| `is_replan` | 标记为重规划记录 | `true` |
| `replan_reason` | 重规划原因（人工填写） | `"L1001 容量溢出"` |

**版本链对象范围**：

| 操作 | 版本链对象 |
|------|----------|
| `redispatch` | GlobalSchedule + DispatchBatch + NodeDispatch + Route |
| `reroute` | Route（仅路径规划记录） |

> **对比查询**：通过 `parent_id` 可追溯完整版本链，前端可展示"原方案 vs 新方案"对比视图。原方案完整保留，不做任何修改。

---

## 7. 错误码汇总

| code | HTTP 状态码 | 说明 |
|------|------------|------|
| `0` | 200 | 成功 |
| `40000` | 400 | 参数校验失败（Schema validator 触发） |
| `40001` | 200 | 业务错误（已解决重复操作、缺少必要参数、target_code 不存在、内部调度失败） |
| `40401` | 200 | 资源不存在（异常事件 / 调度方案 / 路线） |
| `40300` | 403 | 无权限（manager 角色写操作） |
| `40100` | 401 | 未登录或 Token 无效 |

---

## 8. 测试覆盖

| 测试类型 | 文件 | 测试数 | 状态 |
|---------|------|--------|------|
| 异常服务单元测试 | `tests/test_services/test_exception_service.py` | 19 | ✅ |
| 调度管道集成测试 | `tests/tests/integration/test_dispatch_pipeline.py` | — | ✅ |
| 自动重规划集成测试 | `tests/tests/integration/test_auto_redispatch.py` | — | ✅ |
| 异常重规划集成测试 | `tests/tests/integration/test_exception_replan.py` | — | ✅ |
| **总计** | | **32** | **100%** |

---

## 9. 设计决策

### 9.1 方案A：不修改现有服务层

- `ReplanService` 直接调用 `ScheduleService`、`DispatchService`、`RouteService`
- 版本链逻辑完全在 `ReplanService` 中实现
- 原服务层代码（`schedule_service.py`、`dispatch_service.py`、`route_service.py`）零修改

### 9.2 重规划仅调度 exception 状态实体

- `is_replan=True` 标记传入各服务层，仅对 `exception` 状态的订单/包裹进行调度
- 正常配送中的实体不受影响

### 9.3 reroute 不修改状态

- 与 `redispatch` 不同，`reroute` 不重置订单/货物/包裹为 `exception`
- 仅生成新路线记录，原路线保留用于对比

### 9.4 创建异常自动关联状态

- 创建异常事件时，自动将 `related_schedule_code` 关联的订单/货物/包裹置为 `exception`
- 车辆异常（`target_type=vehicle`）：车辆 → `disabled`，且批量更新关联包裹和货物

### 9.5 Redispatch 只需全局调度完成

- `redispatch` 前置条件仅为阶段3（全局调度 `schedule_code` 存在）
- `ReplanService.redispatch()` 内部自行调用 `DispatchService` 执行 F005+F006
- **不需要**预先执行节点间调度

### 9.6 Reroute 需节点调度完成

- `reroute` 前置条件为阶段4（节点调度完成，`Route` 记录存在）
- 因为 `reroute` 的操作对象是 F006 生成的 `Route` 记录

### 9.7 Package 异常暂未实现

- `exception_type=package`（包裹破损/丢失等）尚未实现，已从本次 API 枚举取值中移除
- 后续版本中，`package` 异常将触发 `redispatch` 全链路重调度（F007→F021→F005→F006）
- 当前 MVP 仅支持 `road`（道路异常→reroute）和 `node`（节点异常→redispatch）

---

## 10. 相关文档

- [项目宪章](../../.codebuddy/CODEBUDDY.md)
- [系统架构设计说明书](../../docs/architecture/系统架构设计说明书.md)
- [MVP 开发计划 - 后端](../../docs/MVP开发计划-后端.md)
- [阶段7开发文档](../../My_doc/阶段7开发文档-异常与重规划.md)
- [阶段5 API 契约文档](./api-contract-phase5.md)

---

**文档版本历史**：

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| V1.0 | 2026-06-22 | AI | 初始版本，定义阶段7 API契约 |
| V1.1 | 2026-06-22 | AI | 移除 `package` 异常类型：功能暂未实现，已从 API 枚举中删除 |
