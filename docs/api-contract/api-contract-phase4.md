# 阶段4：节点间调度 F005 - API 契约文档

> **文档版本**：V1.3  
> **创建日期**：2026年6月14日  
> **开发阶段**：阶段4（节点间调度 F005）  
> **API 基础路径**：`http://localhost:8000/api`  
> **API 协议**：HTTP/JSON，UTF-8  
> **参考资料**：PRD V2.7、系统架构设计说明书 V1.0、阶段4开发文档 V1.0、阶段4实际实现代码  
> 
> **⚠️ 阶段限制**：阶段4仅完整实现 `demo_mode=true`（一次调用完成 L0→L2 全链路）。`demo_mode=false` 的完整流程（分阶段调度 + 手动模拟送达）将在阶段6中完整实现。

---

## 1. 文档说明

本文档定义阶段4（节点间调度 F005）的 API 契约，包括：

- 节点调度管理接口（触发节点调度、调度批次列表、批次详情）
- 错误码定义
- 请求/响应示例（JSON）
- 前端对接指南

**前端开发者**：请基于此文档进行 Mock 数据开发和接口对接。

**后端开发者**：请确保实现的接口与此文档一致。

---

## 2. API 基本约定

### 2.1 基础信息

| 项 | 约定 |
|---|---|
| Base URL | `http://localhost:8000/api` |
| 协议 | HTTP/JSON，UTF-8 |
| 版本 | MVP 不加 `/v1` 前缀 |
| 时间格式 | ISO 8601，`2026-06-14T10:00:00` |
| 标识符 | 请求/响应中业务对象使用 `*_code`，不使用数据库 `id` |
| 分页 | `?page=1&page_size=20`；响应含 `total` |

### 2.2 统一响应格式

**成功响应**：

```json
{
  "code": 0,
  "message": "success",
  "data": { },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**业务失败**（HTTP 200，约束不满足等）：

```json
{
  "code": 40001,
  "message": "节点调度失败：L0→L1调度失败：节点 SC001 没有可用的车辆（载重不足或无不空闲车辆）",
  "data": null,
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**参数错误**（HTTP 400）：

```json
{
  "code": 40000,
  "message": "参数校验失败",
  "data": {
    "fields": {
      "schedule_code": "必填"
    }
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**认证/授权错误**（HTTP 401/403）：

```json
// 未登录
{ "code": 40100, "message": "未登录或 Token 无效", "data": null, "meta": { "degraded": false, "degraded_reason": null } }
// Token 过期
{ "code": 40101, "message": "Token 已过期，请重新登录", "data": null, "meta": { "degraded": false, "degraded_reason": null } }
// 无权限
{ "code": 40300, "message": "无操作权限", "data": null, "meta": { "degraded": false, "degraded_reason": null } }
```

### 2.3 认证方式

**登录**：

```
POST /api/auth/login
Content-Type: application/json

{ "username": "dispatcher", "password": "123456" }
```

**响应 data**：

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 86400,
  "role": "dispatcher",
  "display_name": "调度员"
}
```

**后续请求**：

```
Authorization: Bearer {access_token}
```

### 2.4 错误码定义

| code | HTTP | 说明 | 触发场景 |
|---|---|---|---|
| 0 | 200 | 成功 | 接口调用成功 |
| 40000 | 400 | 参数校验失败 | 请求体字段验证失败 |
| 40001 | 200 | 节点调度失败 | F005 算法无法完成调度（无可用车辆、无可调度包裹等） |
| 40401 | 200 | 调度方案不存在 | POST /api/schedule/node-dispatch 的 schedule_code 无效 |
| 40402 | 200 | 调度批次不存在 | GET /api/schedule/batches/{code} 批次编号无效 |
| 40100 | 401 | 未登录或 Token 无效 | Token 缺失、格式错误、签名验证失败 |
| 40101 | 401 | Token 已过期 | Token 的 exp 字段已过期 |
| 40300 | 403 | 无操作权限 | manager 角色调用 POST /api/schedule/node-dispatch |
| 40400 | 404 | 资源不存在 | 请求的资源路径不存在 |
| 50000 | 500 | 服务器内部错误 | 数据库写入失败等未预期异常 |

> **说明**：所有接口（包括 401/403/404/500）均返回统一响应格式 `{code, message, data, meta}`。前端可通过 `response.data.code` 统一判断，无需分别处理 `detail` 字段。

---

## 3. 节点调度管理 API（F005）

### 3.1 API 清单

| 方法 | 路径 | 说明 | 认证要求 | 权限要求 |
|---|---|---|---|---|
| POST | `/api/schedule/node-dispatch` | 触发节点调度（F005） | 需要认证 | dispatcher |
| GET | `/api/schedule/batches` | 调度批次列表 | 需要认证 | dispatcher + manager |
| GET | `/api/schedule/batches/{batch_code}` | 调度批次详情 | 需要认证 | dispatcher + manager |

---

### 3.2 POST /api/schedule/node-dispatch

**功能**：触发节点调度（F005 节点调度算法）。

**流程**：

> **阶段4实现范围**：阶段4仅实现 `demo_mode=true` 的完整流程。`demo_mode=false` 的分阶段调度（场景 A/B/C/D + 手动模拟送达）将在阶段6中完整实现。

1. **`demo_mode=true`（阶段4已实现）**：一次调用完成 L0→L2 全链路调度
   - L0→L1 调度（分配车辆与司机）
   - 写入批次 + L0→L1 调度明细
   - 自动模拟 L0→L1 送达（包裹→delivered、货物→pending_pack、车辆/司机恢复idle）
   - 自动在 L1 重新打包（货物→packed、生成 L1→L2 包裹）
   - L1→L2 调度（分配车辆与司机）
   - 写入 L1→L2 调度明细
   - 自动模拟 L1→L2 送达（包裹→delivered、货物→delivered、订单→completed）
   - 批次状态更新为 `completed`
   - **一条请求完成所有步骤，前端无需额外操作**
2. **`demo_mode=false`（阶段6实现）**：分阶段调度，后端通过 `_check_packages_by_level()` 智能检测：
   - **场景 A**：同时存在 L0→L1 和 L1→L2 包裹 → 优先执行 L0→L1
   - **场景 B**：仅存在 L0→L1 包裹 → 执行 L0→L1
   - **场景 C**：仅存在 L1→L2 包裹 → 自动创建批次，直接执行 L1→L2
   - **场景 D**：都不存在 → 返回错误"没有可调度的包裹"
3. F005 节点调度算法：分配车辆与司机（含跨节点后备车辆 Phase 2 重试）
4. 写入 dispatch_batches + node_dispatches
5. 单事务写入数据库并更新包裹/货物/车辆/司机状态

**请求**：

- **URL**：`/api/schedule/node-dispatch`
- **方法**：`POST`
- **Content-Type**：`application/json`
- **认证**：`Authorization: Bearer {access_token}`（dispatcher 角色）
- **请求体**：

```json
{
  "schedule_code": "GS20260614001",  // 必填，全局调度方案编号
  "demo_mode": true                 // 可选，是否演示模式，默认 true（阶段4仅支持 true）
}
```

**请求体验证规则**：

| 字段 | 类型 | 必填 | 验证规则 |
|---|---|---|---|
| schedule_code | string | 是 | 全局调度方案编号，必须存在 |
| demo_mode | bool | 否 | 是否演示模式，默认 true。阶段4仅支持 `true`；`false` 将在阶段6完整实现 |

**响应成功（HTTP 200）**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "batch_code": "BATCH20260614001",
    "status": "completed",
    "dispatches": [
      {
        "vehicle_code": "VEHSC00101",
        "driver_code": "DRVSC00101",
        "tasks": [
          {
            "from_node_code": "SC001",
            "to_node_code": "L1001",
            "package_codes": ["PKG202606140001"],
            "is_return": false
          },
          {
            "from_node_code": "L1001",
            "to_node_code": "SC001",
            "package_codes": [],
            "is_return": true
          }
        ],
        "total_distance": 25.3,
        "total_time": 0.42,
        "vehicle_id": 1,
        "driver_id": 1
      }
    ],
    "unallocated_packages": []
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**响应字段说明**：

| 字段 | 类型 | 说明 |
|---|---|---|
| batch_code | string | 调度批次编号，格式：BATCH + YYYYMMDD + 3位序号 |
| status | string | 批次状态：pending / l0_l1_done / completed / failed |
| dispatches | array | 调度明细列表（L0→L1 + L1→L2） |
| unallocated_packages | array | 未分配的包裹编码列表（因车辆不足等原因未分配） |
| dispatches[].vehicle_code | string | 车辆编号 |
| dispatches[].driver_code | string | 司机编号 |
| dispatches[].tasks | array | 任务列表 |
| dispatches[].tasks[].from_node_code | string | 起始节点编号 |
| dispatches[].tasks[].to_node_code | string | 目的节点编号 |
| dispatches[].tasks[].package_codes | array | 包裹编号列表 |
| dispatches[].tasks[].is_return | bool | 是否返回任务 |
| dispatches[].total_distance | float | 总距离（公里） |
| dispatches[].total_time | float | 总时间（小时） |
| dispatches[].vehicle_id | int | 车辆ID（内部） |
| dispatches[].driver_id | int | 司机ID（内部） |

**响应失败（HTTP 200，业务错误）**：

| code | message | 说明 |
|---|---|---|
| 40001 | 节点调度失败：L0→L1调度失败：节点 SC001 没有可用的车辆（载重不足或无不空闲车辆） | 车辆不足或载重不够 |
| 40001 | 节点调度失败：L1→L2调度失败：节点 L1001 没有可用的车辆 | L1→L2 车辆不足 |
| 40001 | 节点调度失败：没有可调度的包裹 | 该 schedule_code 下不存在 packed 状态的包裹 |
| 40001 | 节点调度失败：没有可用的车辆完成调度，N个包裹未分配 | 所有可用车辆均已满载，部分包裹无法分配 |
| 40401 | 调度方案不存在：GS20260614999 | schedule_code 无效 |

**cURL 示例**：

```bash
curl -X POST "http://localhost:8000/api/schedule/node-dispatch" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -d '{
    "schedule_code": "GS20260614001",
    "demo_mode": true
  }'
```

**Swagger 示例**：

```yaml
# Swagger UI 中的示例请求
{
  "schedule_code": "GS20260614001",
  "demo_mode": true
}

# Swagger UI 中的示例响应（200）
{
  "code": 0,
  "message": "success",
  "data": {
    "batch_code": "BATCH20260614001",
    "status": "completed",
    "dispatches": [
      {
        "vehicle_code": "VEHSC00101",
        "driver_code": "DRVSC00101",
        "tasks": [
          {
            "from_node_code": "SC001",
            "to_node_code": "L1001",
            "package_codes": ["PKG202606140001"],
            "is_return": false
          }
        ],
        "total_distance": 25.3,
        "total_time": 0.42,
        "vehicle_id": 1,
        "driver_id": 1
      }
    ]
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

---

### 3.2.1 demo_mode=true 完整演示流程（L0→L2 全链路）

当使用 `demo_mode=true` 时，一次 API 调用即可完成货物从 L0 到 L2 的全部调度流程。以下是前端需执行的步骤及后端对应的内部行为：

#### 前置条件

- 已完成阶段3全局调度（`POST /api/schedule/global`），获得 `schedule_code`
- 数据库中已存在 `packed` 状态的 L0→L1 包裹

#### 前端步骤 &amp; 后端行为对照表

| 步骤 | 前端操作 | 调用的 API | 后端内部行为 | 状态变化 |
|------|---------|-----------|-------------|---------|
| **0** | 触发全局调度 | `POST /api/schedule/global` | F007 全局调度 → F021 打包 → 写入 global_schedules + packages | 订单→delivering、货物→packed、包裹→packed |
| **1** | 调用节点调度（demo_mode=true） | `POST /api/schedule/node-dispatch`<br>`{"schedule_code":"GS...","demo_mode":true}` | **见下方详细拆解** | **见下方** |
| **2** | 查看批次结果 | `GET /api/schedule/batches/{batch_code}` | 返回批次详情（含 dispatches、状态等） | — |
| **3** | （可选）查看路线 | `GET /api/routes` | 阶段5实现路径规划后可查看 | — |

#### 步骤1 后端内部行为详细拆解

当 `POST /api/schedule/node-dispatch` 以 `demo_mode=true` 调用时，后端按以下顺序自动执行：

```
┌─────────────────────────────────────────────────────────────┐
│ 阶段 A：L0→L1 调度                                           │
├─────────────────────────────────────────────────────────────┤
│ A1. 查询 schedule_code 下所有 L0→L1 的 packed 包裹            │
│ A2. 按 from_node(L0仓储中心) 分组                             │
│ A3. 为每个节点组分配车辆（同节点优先，载重匹配）                  │
│     - 同节点无可用车辆 → 跨节点后备车辆 Phase 2 重试            │
│ A4. 分配空闲司机（从车辆归属节点选第一个 idle 司机）             │
│ A5. 为每辆车添加返回任务（is_return=true, package_codes=[]）    │
│ A6. 生成 batch_code，写入 DispatchBatch（status=pending）      │
│ A7. 写入 NodeDispatch 明细（level_phase=0）                    │
├─────────────────────────────────────────────────────────────┤
│ 阶段 B：自动模拟 L0→L1 送达                                    │
├─────────────────────────────────────────────────────────────┤
│ B1. 更新 L0→L1 包裹状态：packed → delivered                   │
│ B2. 更新 L0→L1 货物状态：packed → pending_pack（到达L1需重打包）│
│ B3. 更新车辆状态：delivering → idle                            │
│ B4. 更新司机状态：busy → idle                                  │
├─────────────────────────────────────────────────────────────┤
│ 阶段 C：自动 L1 重新打包                                        │
├─────────────────────────────────────────────────────────────┤
│ C1. 查询到达 L1 的 pending_pack 货物                           │
│ C2. 按 L1→L2 规则打包（同订单的货物合并成一个包裹）              │
│ C3. 写入新的 L1→L2 packages（status=packed）                  │
│ C4. 更新货物状态：pending_pack → packed                        │
├─────────────────────────────────────────────────────────────┤
│ 阶段 D：L1→L2 调度                                             │
├─────────────────────────────────────────────────────────────┤
│ D1. 查询新生成的 L1→L2 packed 包裹                             │
│ D2. 按 from_node(L1分拣中心) 分组                              │
│ D3. 分配车辆与司机（同节点优先）                                 │
│ D4. 添加返回任务                                               │
│ D5. 写入 NodeDispatch 明细（level_phase=1）                    │
│ D6. 更新批次：l0_l1_dispatch_count、l1_l2_dispatch_count       │
├─────────────────────────────────────────────────────────────┤
│ 阶段 E：自动模拟 L1→L2 送达                                    │
├─────────────────────────────────────────────────────────────┤
│ E1. 更新 L1→L2 包裹状态：packed → delivered                    │
│ E2. 更新 L1→L2 货物状态：packed → delivered                    │
│ E3. 检查订单：若该订单所有货物均已 delivered → 订单→completed    │
│ E4. 更新车辆状态：delivering → idle                            │
│ E5. 更新司机状态：busy → idle                                  │
│ E6. 批次状态更新：pending → completed                          │
└─────────────────────────────────────────────────────────────┘
```

#### 前后端交互时序图

```
前端                          后端                         数据库
 │                             │                            │
 │── POST /schedule/global ──→│                            │
 │                             │── F007+F021 ──────────────→│
 │←──── { schedule_code } ────│←── 写入成功 ───────────────│
 │                             │                            │
 │── POST /node-dispatch ────→│                            │
 │   {demo_mode: true}        │                            │
 │                             │── A. L0→L1调度 ────────────→│
 │                             │── B. 模拟L0→L1送达 ────────→│
 │                             │── C. L1重新打包 ───────────→│
 │                             │── D. L1→L2调度 ────────────→│
 │                             │── E. 模拟L1→L2送达 ────────→│
 │                             │   (以上全部在单事务中)        │
 │←── { batch_code, ──────────│←── commit ─────────────────│
 │      status:"completed",   │                            │
 │      dispatches: [...] }   │                            │
 │                             │                            │
 │── GET /batches/{code} ────→│                            │
 │←── 批次详情 ───────────────│── 查询 ────────────────────→│
```

#### 响应解读

调用成功后，响应中 `status` 直接为 `"completed"`，表示 L0→L2 全链路已完成：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "batch_code": "BATCH20260614001",
    "status": "completed",
    "dispatches": [
      // L0→L1 调度明细（level_phase=0）+ L1→L2 调度明细（level_phase=1）
    ],
    "unallocated_packages": []
  }
}
```

| 响应字段 | demo_mode=true 时的含义 |
|---------|----------------------|
| `status: "completed"` | L0→L1 + L1→L2 均已完成，货物已送达 L2 |
| `dispatches` | 包含 L0→L1（level_phase=0）和 L1→L2（level_phase=1）全部调度明细 |
| `unallocated_packages` | 因车辆/载重不足未分配的包裹（空数组=全部分配成功） |

#### 前端状态判断

```typescript
// 前端收到响应后的处理逻辑
const res = await triggerNodeDispatch({ schedule_code, demo_mode: true })

if (res.code === 0 && res.data.status === 'completed') {
  // demo_mode=true 成功 → 货物已到达 L2，可直接展示结果
  showSuccess('调度完成！货物已全部送达 L2 末端节点')
  // 可通过 GET /api/orders 查看订单状态（应为 completed）
  // 可通过 GET /api/goods 查看货物状态（应为 delivered）
} else if (res.code === 0 && res.data.status === 'failed') {
  showError('调度失败：' + res.message)
}
```

---

### 3.3 GET /api/schedule/batches

**功能**：获取调度批次列表。

**请求**：

- **URL**：`/api/schedule/batches`
- **方法**：`GET`
- **请求头**：`Authorization: Bearer {access_token}`（dispatcher 或 manager 角色）
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| schedule_code | string | 否 | 按调度方案编号筛选 |
| status | string | 否 | 按状态筛选：pending / l0_l1_done / completed / failed |
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页数量，默认 20，最大 100 |

> **注意**：当前版本暂未实现分页参数（page/page_size），接口返回所有匹配的批次记录。后续版本将补充分页支持。

**响应成功（HTTP 200）**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "batch_code": "BATCH20260614001",
        "schedule_code": "GS20260614001",
        "status": "completed",
        "demo_mode": true,
        "l0_l1_dispatch_count": 5,
        "l1_l2_dispatch_count": 8,
        "created_at": "2026-06-14T10:30:00"
      }
    ],
    "total": 1
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**响应字段说明**：

| 字段 | 类型 | 说明 |
|---|---|---|
| items | array | 调度批次列表 |
| items[].batch_code | string | 批次编号 |
| items[].schedule_code | string | 全局调度方案编号 |
| items[].status | string | 批次状态：pending / l0_l1_done / completed / failed |
| items[].demo_mode | bool | 是否演示模式（阶段4统一为 true） |
| items[].l0_l1_dispatch_count | int | L0→L1 调度明细数量 |
| items[].l1_l2_dispatch_count | int | L1→L2 调度明细数量 |
| items[].created_at | string | 创建时间（ISO 8601） |
| total | int | 总记录数 |

**cURL 示例**：

```bash
curl -X GET "http://localhost:8000/api/schedule/batches" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**Swagger 示例**：

```yaml
# Swagger UI 中的示例响应（200）
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "batch_code": "BATCH20260614001",
        "schedule_code": "GS20260614001",
        "status": "completed",
        "demo_mode": true,
        "l0_l1_dispatch_count": 5,
        "l1_l2_dispatch_count": 8,
        "created_at": "2026-06-14T10:30:00"
      }
    ],
    "total": 1
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

---

### 3.4 GET /api/schedule/batches/{batch_code}

**功能**：获取调度批次详情（含 dispatches）。

**请求**：

- **URL**：`/api/schedule/batches/{batch_code}`
- **方法**：`GET`
- **请求头**：`Authorization: Bearer {access_token}`（dispatcher 或 manager 角色）
- **路径参数**：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| batch_code | string | 是 | 调度批次编号 |

**响应成功（HTTP 200）**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "batch_code": "BATCH20260614001",
    "schedule_code": "GS20260614001",
    "status": "completed",
    "unallocated_packages": ["PKG202606140005", "PKG202606140006"],
    "dispatches": [
      {
        "dispatch_code": "DISP20260614001",
        "vehicle_code": "VEHSC00101",
        "driver_code": "DRVSC00101",
        "level_phase": 0,
        "tasks": [
          {
            "from_node_code": "SC001",
            "to_node_code": "L1001",
            "package_codes": ["PKG202606140001"],
            "is_return": false
          },
          {
            "from_node_code": "L1001",
            "to_node_code": "SC001",
            "package_codes": [],
            "is_return": true
          }
        ],
        "total_distance": 25.3,
        "total_time": 0.42
      }
    ]
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**响应字段说明**：

| 字段 | 类型 | 说明 |
|---|---|---|
| batch_code | string | 批次编号 |
| schedule_code | string | 全局调度方案编号 |
| status | string | 批次状态：pending / l0_l1_done / completed / failed |
| unallocated_packages | array | 未分配的包裹编码列表（可能因车辆不足或载重不够而未分配） |
| dispatches | array | 调度明细列表 |
| dispatches[].dispatch_code | string | 调度明细编号 |
| dispatches[].vehicle_code | string | 车辆编号 |
| dispatches[].driver_code | string | 司机编号 |
| dispatches[].level_phase | int | 层级阶段：0（L0→L1）/ 1（L1→L2） |
| dispatches[].tasks | array | 任务列表 |
| dispatches[].tasks[].from_node_code | string | 起始节点编号 |
| dispatches[].tasks[].to_node_code | string | 目的节点编号 |
| dispatches[].tasks[].package_codes | array | 包裹编号列表 |
| dispatches[].tasks[].is_return | bool | 是否返回任务 |
| dispatches[].total_distance | float | 总距离（公里） |
| dispatches[].total_time | float | 总时间（小时） |

**响应失败（HTTP 200，业务错误）**：

| code | message | 说明 |
|---|---|---|
| 40402 | 调度批次不存在：BATCH20260614999 | 批次编号无效 |

**cURL 示例**：

```bash
curl -X GET "http://localhost:8000/api/schedule/batches/BATCH20260614001" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**Swagger 示例**：

```yaml
# Swagger UI 中的示例响应（200）
{
  "code": 0,
  "message": "success",
  "data": {
    "batch_code": "BATCH20260614001",
    "schedule_code": "GS20260614001",
    "status": "completed",
    "unallocated_packages": ["PKG202606140005", "PKG202606140006"],
    "dispatches": [
      {
        "dispatch_code": "DISP20260614001",
        "vehicle_code": "VEHSC00101",
        "driver_code": "DRVSC00101",
        "level_phase": 0,
        "tasks": [
          {
            "from_node_code": "SC001",
            "to_node_code": "L1001",
            "package_codes": ["PKG202606140001"],
            "is_return": false
          }
        ],
        "total_distance": 25.3,
        "total_time": 0.42
      }
    ]
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

---

## 4. 前端对接指南

### 4.1 节点调度触发流程

```
1. 用户访问调度工作台页
2. 用户选择全局调度方案（GS20260614001）
3. 用户点击"节点调度"按钮
4. 前端调用 POST /api/schedule/node-dispatch（demo_mode=true 用于演示）
5. 后端返回 batch_code
6. 前端跳转至调度批次详情页
```

### 4.2 请求拦截器

前端需配置 Axios 请求拦截器，自动在请求头中附加 Token（同阶段1/2/3）：

```typescript
// src/api/request.ts

import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const request = axios.create({
  baseURL: '/api',  // Vite 代理转发至 :8000
  timeout: 15000     // 15 秒超时（调度接口可能接近 10 秒）
})

// 请求拦截器：附加 Token
request.interceptors.request.use((config) => {
  const authStore = useAuthStore()
  if (authStore.accessToken) {
    config.headers.Authorization = `Bearer ${authStore.accessToken}`
  }
  return config
})

// 响应拦截器：统一处理业务错误和 HTTP 错误
request.interceptors.response.use(
  (response) => {
    const { code, message } = response.data
    if (code !== 0) {
      // 所有错误（包括 40100/40101/40300 等）均返回统一格式
      if (code === 40100 || code === 40101) {
        const authStore = useAuthStore()
        authStore.logout()
        router.push('/login')
      }
      return Promise.reject(new Error(message))
    }
    return response.data  // 直接返回 data 层
  },
  (error) => {
    // 网络错误（超时、无响应等）
    ElMessage.error('网络请求失败，请检查网络连接')
    return Promise.reject(error)
  }
)

export default request
```

### 4.3 节点调度接口调用示例

```typescript
// src/api/schedule.ts

import request from './request'

export interface NodeDispatchRequest {
  schedule_code: string
  demo_mode?: boolean
}

export interface NodeDispatchResponse {
  batch_code: string
  status: string
  dispatches: Array<{
    vehicle_code: string
    driver_code: string
    tasks: Array<{
      from_node_code: string
      to_node_code: string
      package_codes: string[]
      is_return: boolean
    }>
    total_distance: number
    total_time: number
  }>
}

export async function createNodeDispatch(data: NodeDispatchRequest) {
  return request.post('/schedule/node-dispatch', data)
}

export async function listDispatchBatches(params: {
  schedule_code?: string
  status?: string
}) {
  return request.get('/schedule/batches', { params })
}

export async function getDispatchBatchDetail(batch_code: string) {
  return request.get(`/schedule/batches/${batch_code}`)
}
```

### 4.4 调度批次列表页面示例

```vue
<!-- src/views/DispatchBatchView.vue -->

<template>
  <div>
    <el-button type="primary" @click="handleNodeDispatch" :loading="loading">
      节点调度
    </el-button>

    <el-table :data="batches">
      <el-table-column prop="batch_code" label="批次编号" />
      <el-table-column prop="schedule_code" label="调度方案" />
      <el-table-column prop="status" label="状态" />
      <el-table-column prop="l0_l1_dispatch_count" label="L0→L1调度数" />
      <el-table-column prop="l1_l2_dispatch_count" label="L1→L2调度数" />
      <el-table-column prop="created_at" label="创建时间" />
      <el-table-column label="操作">
        <template #default="scope">
          <el-button @click="viewDetail(scope.row.batch_code)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { listDispatchBatches, createNodeDispatch } from '@/api/schedule'

const batches = ref([])
const loading = ref(false)

const loadBatches = async () => {
  const res = await listDispatchBatches({})
  batches.value = res.data.items
}

const handleNodeDispatch = async () => {
  loading.value = true
  try {
    const res = await createNodeDispatch({ 
      schedule_code: 'GS20260614001', 
      demo_mode: true 
    })
    ElMessage.success(`节点调度成功：${res.data.batch_code}`)
    loadBatches()
  } catch (error: any) {
    ElMessage.error(error.message || '节点调度失败')
  } finally {
    loading.value = false
  }
}

const viewDetail = (batch_code: string) => {
  // 跳转至批次详情页
  router.push(`/dispatch-batches/${batch_code}`)
}

loadBatches()
</script>
```

---

## 5. 后端实现检查清单

### 5.1 FastAPI 路由实现

- [ ] `POST /api/schedule/node-dispatch` 接口已实现
- [ ] `GET /api/schedule/batches` 接口已实现
- [ ] `GET /api/schedule/batches/{batch_code}` 接口已实现
- [ ] 所有接口返回统一响应格式 `{ code, message, data, meta }`
- [ ] POST 接口对业务错误返回 code=40001
- [ ] GET 接口对批次不存在返回 code=40402

### 5.2 认证与权限

- [ ] `POST /api/schedule/node-dispatch` 需要 dispatcher 角色（require_dispatcher）
- [ ] `GET /api/schedule/batches` 需要认证（get_current_user）
- [ ] `GET /api/schedule/batches/{batch_code}` 需要认证（get_current_user）
- [ ] manager 角色调用 POST 接口时返回 HTTP 403 + code=40300

### 5.3 节点调度编排服务

- [ ] `DispatchService.create_node_dispatch` 已实现
- [ ] F005 算法调用正确（node_dispatch.py）
- [ ] 单事务写入：dispatch_batches + node_dispatches + 更新 packages/vehicles/drivers 状态
- [ ] 事务回滚：F005 异常时全局回滚

### 5.4 算法实现

- [ ] F005 节点调度算法已实现（node_dispatch.py）
- [ ] F005 第一次调用（L0→L1）正确
- [ ] F005 第二次调用（L1→L2）正确
- [ ] 车辆匹配策略：载重匹配 + 节点优先级
- [ ] 返回任务添加：每个车辆任务列表末尾添加 is_return=true

### 5.5 Swagger 文档

- [ ] Swagger 文档可通过 http://localhost:8000/docs 访问
- [ ] 节点调度接口有示例请求/响应
- [ ] 受保护接口需在 Swagger 中授权后调用

---

## 6. 测试用例

### 6.1 触发节点调度测试

| 测试用例 | 请求 | 预期响应 |
|---|---|---|
| 正常调度（demo_mode=true） | `{ "schedule_code": "GS20260614001", "demo_mode": true }` | 200, code=0, 返回 batch_code, status=completed, dispatches 含 L0→L1+L1→L2 |
| 无可调度包裹 | 无packed包裹 | 200, code=40001, message="没有可调度的包裹" |
| 无可用车辆 | 车辆状态=delivering | 200, code=40001, message="没有可用的车辆完成调度" |
| 调度方案不存在 | `{ "schedule_code": "GS999" }` | 200, code=40401, message="调度方案不存在" |
| demo_mode=false（阶段6预留） | `{ "schedule_code": "GS20260614001", "demo_mode": false }` | ⚠️ 阶段4未完整实现，行为以阶段6文档为准 |

### 6.2 调度批次列表测试

| 测试用例 | 请求 | 预期响应 |
|---|---|---|
| 获取列表 | `GET /api/schedule/batches` | 200, code=0, 返回 items 数组 |
| 按方案筛选 | `GET /api/schedule/batches?schedule_code=GS20260614001` | 200, code=0, 返回该方案的批次 |
| 按状态筛选 | `GET /api/schedule/batches?status=completed` | 200, code=0, 返回 completed 批次 |

### 6.3 批次详情测试

| 测试用例 | 请求 | 预期响应 |
|---|---|---|
| 正常获取 | `GET /api/schedule/batches/BATCH20260614001` | 200, code=0, 返回批次详情 |
| 批次不存在 | `GET /api/schedule/batches/BATCH999` | 200, code=40402, message="调度批次不存在" |

### 6.4 权限测试

| 测试用例 | 用户角色 | 接口 | 预期响应 |
|---|---|---|---|
| dispatcher 调用节点调度 | dispatcher | POST /api/schedule/node-dispatch | 200, code=0 |
| manager 调用节点调度 | manager | POST /api/schedule/node-dispatch | 403, code=40300 |
| manager 查看列表 | manager | GET /api/schedule/batches | 200, code=0 |

---

## 7. 变更历史

| 版本 | 日期 | 修改内容 | 作者 |
|---|---|---|---|
| V1.0 | 2026-06-14 | 初版：阶段4 节点间调度 F005 API 契约文档 | AI 开发助手 |
| V1.1 | 2026-06-17 | 更新 `GET /api/schedule/batches/{batch_code}` 接口，添加 `unallocated_packages` 字段（未分配的包裹编码列表） | AI 开发助手 |
| V1.2 | 2026-06-18 | 更新节点调度流程描述（智能检测包裹类型、4种场景）；更新 `GET /api/schedule/batches` 分页说明（当前未实现 page/page_size）；移除过时错误信息；`POST /api/schedule/node-dispatch` 响应新增 `unallocated_packages` 字段 | AI 开发助手 |
| V1.3 | 2026-06-18 | 标注阶段4仅实现 `demo_mode=true`，`demo_mode=false` 完整流程推迟到阶段6；新增 §3.2.1 demo_mode=true 完整演示流程（前端步骤+后端行为对照表、内部行为拆解、交互时序图）；Swagger 示例默认改为 demo_mode=true；测试用例更新 | AI 开发助手 |

---

**文档结束**
