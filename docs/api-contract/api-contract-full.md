# 智能物流平台 — 完整 API 契约文档 v1.0

> **生成日期**: 2026-06-25  
> **覆盖范围**: 阶段 1–8 + P1-1 + P1-2 + P1-3（全部已实现）  
> **统一响应格式**: `{ code, message, data, meta }` — 成功 `code=0`

---

## 目录

1. [通用约定](#1-通用约定)
2. [认证与权限](#2-认证与权限)
3. [基础数据管理](#3-基础数据管理)
4. [全局调度](#4-全局调度)
5. [节点调度](#5-节点调度)
6. [路径规划](#6-路径规划)
7. [模拟送达](#7-模拟送达)
8. [到货确认](#8-到货确认-p1-3)
9. [异常管理](#9-异常管理)
10. [AI 助手](#10-ai-助手)
11. [健康检查](#11-健康检查)
12. [错误码速查](#12-错误码速查)

---

## 1. 通用约定

### 1.1 统一响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": { ... },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

| code | HTTP 状态码 | 说明 |
|------|-------------|------|
| `0` | 200 | 成功 |
| `40000` | 400 | 参数校验失败 |
| `40001` | 200 | 业务逻辑失败 |
| `40002` | 200 | 已有活跃方案，不允许重复调度 |
| `40003` | 200 | 订单状态已变化，请重新预览 |
| `40100` | 401 | 未登录或 Token 无效 / 用户名密码错误 |
| `40101` | 401 | Token 已过期 |
| `40300` | 403 | 无权限执行此操作 |
| `40400` | 404 | 资源不存在 |
| `40401` | 200 | 指定资源不存在（业务层） |
| `50000` | 500 | 服务器内部错误 |
| `50001` | 200 | 确认失败，draft 已丢弃 |

### 1.2 认证方式

所有需认证的端点使用 `Authorization: Bearer <JWT_TOKEN>` 请求头。

### 1.3 双标识策略

- 数据库内部使用自增 `id` 做外键关联
- API 层统一暴露 `*_code` 业务编号，绝不暴露数据库 `id`

### 1.4 分页规范

列表接口支持 `page`（默认 1）和 `page_size`（默认 20）查询参数，响应格式：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [ ... ],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

### 1.5 DeepSeek 降级策略

AI 相关端点（`/api/ai/*`）若 DeepSeek API 调用失败，在响应中设置 `meta.degraded=true` 和 `meta.degraded_reason`，使用默认参数/降级数据完成。**绝不伪造 AI 成功结果**。

---

## 2. 认证与权限

### 2.1 登录

```
POST /api/auth/login
```

**请求体**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | ✅ | 用户名 |
| password | string | ✅ | 密码 |

**示例**:
```json
{"username": "dispatcher", "password": "123456"}
```

**成功响应 (code=0)**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "expires_in": 86400,
    "role": "dispatcher",
    "display_name": "张三"
  }
}
```

**失败响应**:
| code | 场景 |
|------|------|
| 40100 | 用户名或密码错误 |
| 40100 | 账号未激活 |

---

### 2.2 获取当前用户

```
GET /api/auth/me
```

**权限**: 登录即可

**成功响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "username": "dispatcher",
    "role": "dispatcher",
    "display_name": "张三",
    "is_active": true
  }
}
```

---

### 2.3 登出

```
POST /api/auth/logout
```

**权限**: 登录即可

**成功响应**: `data=null`

---

## 3. 基础数据管理

### 3.1 订单管理

#### 3.1.1 订单列表

```
GET /api/orders
```

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码（默认 1） |
| page_size | int | 否 | 每页数量（默认 20） |
| status | string | 否 | 状态筛选: `pending` / `delivering` / `completed` / `exception` |

**权限**: 登录即可

---

#### 3.1.2 订单详情

```
GET /api/orders/{order_code}
```

**权限**: 登录即可

---

#### 3.1.3 创建订单

```
POST /api/orders
```

**权限**: dispatcher

**请求体**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| destination_node_code | string | ✅ | 目的地节点编码（必须是 L2 级分拣中心） |
| storage_center_code | string | 否 | 发货存储中心编码（L0，不传则自动分配） |
| time_window | string | 否 | 配送时间窗口 |
| goods | array | ✅ | 货物列表 |

**goods 数组中每项**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| goods_code | string | 否 | 货物编码（留空自动生成） |
| goods_name | string | ✅ | 货物名称 |
| goods_type | string | ✅ | 货物类型 |
| weight | float | ✅ | 重量(kg) |
| volume | float | ✅ | 体积(m³) |

---

#### 3.1.4 编辑订单

```
PUT /api/orders/{order_code}
```

**权限**: dispatcher

**请求体**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| destination_node_code | string | 否 | 目的地节点编码 |
| time_window | string | 否 | 配送时间窗口 |

---

#### 3.1.5 删除订单

```
DELETE /api/orders/{order_code}
```

**权限**: dispatcher  
**约束**: `delivering` 状态订单不可删除

---

#### 3.1.6 批量导入订单

```
POST /api/orders/import
```

**权限**: dispatcher  
**Content-Type**: `multipart/form-data`

**请求参数**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | ✅ | Excel 文件 (.xlsx) |
| skip_errors | bool | 否 | 是否跳过错误行（默认 true） |

**成功响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "success_count": 45,
    "failed_count": 2,
    "failed_rows": [3, 18]
  }
}
```

---

### 3.2 货物管理

#### 3.2.1 货物列表

```
GET /api/goods
```

**查询参数**: `page`, `page_size`, `status`, `node_code`, `order_code`

**权限**: 登录即可

---

#### 3.2.2 货物详情

```
GET /api/goods/{goods_code}
```

**权限**: 登录即可

---

#### 3.2.3 编辑货物

```
PUT /api/goods/{goods_code}
```

**权限**: dispatcher

**请求体**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| goods_name | string | 否 | 货物名称 |
| goods_type | string | 否 | 货物类型 |
| weight | float | 否 | 重量(kg) |
| volume | float | 否 | 体积(m³) |
| node_code | string | 否 | 所在节点编码 |

---

### 3.3 包裹管理

#### 3.3.1 包裹列表

```
GET /api/packages
```

**查询参数**: `page`, `page_size`, `status`, `from_node_code`, `to_node_code`

**权限**: 登录即可

---

#### 3.3.2 包裹详情

```
GET /api/packages/{package_code}
```

**权限**: 登录即可

---

#### 3.3.3 重新打包

```
POST /api/packages/{package_code}/repack
```

**权限**: dispatcher

**请求体**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| goods_codes | string[] | ✅ | 需要重新打包的货物编码列表 |

---

### 3.4 车辆管理

#### 3.4.1 车辆列表

```
GET /api/vehicles
```

**查询参数**: `page`, `page_size`, `status` (`idle`/`delivering`/`maintenance`/`disabled`), `node_code`

**权限**: 登录即可

---

#### 3.4.2 车辆详情

```
GET /api/vehicles/{vehicle_code}
```

**权限**: 登录即可

---

#### 3.4.3 创建车辆

```
POST /api/vehicles
```

**权限**: dispatcher

**请求体**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| vehicle_code | string | 否 | 车辆编码（留空自动生成） |
| model | string | ✅ | 车型 |
| capacity | float | ✅ | 载重(吨) |
| energy_type | string | ✅ | 能源类型: `electric` / `fuel` |
| vehicle_type | string | 否 | 车辆类型: `truck` / `van` / `small_truck` |
| capability_tags | string[] | 否 | 能力标签 |
| last_arrived_node_code | string | ✅ | 当前所在节点编码 |
| node_code | string | ✅ | 归属节点编码 |
| status | string | 否 | 状态（默认 `idle`） |

---

#### 3.4.4 编辑车辆

```
PUT /api/vehicles/{vehicle_code}
```

**权限**: dispatcher

---

#### 3.4.5 删除车辆

```
DELETE /api/vehicles/{vehicle_code}
```

**权限**: dispatcher

---

### 3.5 司机管理

#### 3.5.1 司机列表

```
GET /api/drivers
```

**查询参数**: `page`, `page_size`, `status` (`idle`/`busy`), `node_code`

**权限**: 登录即可

---

#### 3.5.2 司机详情

```
GET /api/drivers/{driver_code}
```

**权限**: 登录即可

---

#### 3.5.3 创建司机

```
POST /api/drivers
```

**权限**: dispatcher

**请求体**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| driver_code | string | 否 | 司机编码（留空自动生成） |
| name | string | ✅ | 姓名 |
| phone | string | 否 | 电话 |
| node_code | string | ✅ | 归属节点编码 |
| status | string | 否 | 状态（默认 `idle`） |

---

#### 3.5.4 编辑司机

```
PUT /api/drivers/{driver_code}
```

**权限**: dispatcher

---

#### 3.5.5 删除司机

```
DELETE /api/drivers/{driver_code}
```

**权限**: dispatcher

---

### 3.6 节点管理

#### 3.6.1 节点列表

```
GET /api/nodes
```

**查询参数**: `page`, `page_size`, `node_type` (`storage_center`/`sorting_center`/`distribution_center`), `level`

**权限**: 登录即可

---

#### 3.6.2 节点详情

```
GET /api/nodes/{node_code}
```

**权限**: 登录即可

---

#### 3.6.3 创建存储中心

```
POST /api/nodes/storage-centers
```

**权限**: dispatcher

---

#### 3.6.4 编辑存储中心

```
PUT /api/nodes/storage-centers/{code}
```

**权限**: dispatcher

---

#### 3.6.5 删除存储中心

```
DELETE /api/nodes/storage-centers/{code}
```

**权限**: dispatcher

---

#### 3.6.6 创建分拣中心

```
POST /api/nodes/sorting-centers
```

**权限**: dispatcher

---

#### 3.6.7 编辑/删除分拣中心

```
PUT /api/nodes/sorting-centers/{code}
DELETE /api/nodes/sorting-centers/{code}
```

**权限**: dispatcher

---

## 4. 全局调度

### 4.1 预览调度方案

```
POST /api/schedule/global
```

生成 draft 调度方案（仅执行 F007 全局调度，不执行 F021 打包），不修改订单/货物状态。

**权限**: dispatcher

**请求体** (可选):
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| order_codes | string[] | 否 | 指定订单（不传=全部 pending） |
| algorithm | string | 否 | 算法类型（默认 `traditional`） |
| preview | bool | 否 | 是否预览模式（默认 `true`） |

**成功响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "schedule_code": "GS20260625001",
    "status": "draft",
    "total_goods": 17,
    "total_distance": 125.3,
    "total_time": 8.5,
    "score": 83.58,
    "score_display": 83,
    "algorithm_type": "traditional",
    "goods_schedules": [
      {
        "goods_code": "G001",
        "goods_name": "电子产品",
        "goods_type": "electronics",
        "weight": 2.5,
        "volume": 0.05,
        "node_code": "SC001",
        "order_code": "O001",
        "path": [
          {"node_code": "SC001", "node_name": "武汉存储中心"},
          {"node_code": "SO001", "node_name": "武汉1级分拣中心"},
          {"node_code": "SO027", "node_name": "光谷0级分拣中心"}
        ]
      }
    ],
    "packages": [],
    "created_at": "2026-06-25T10:30:00"
  }
}
```

> **P1-1 优化**: `goods_schedules.path` 为对象数组（`node_code` + `node_name`），每项含 `goods_name`/`goods_type`/`weight`/`volume`/`node_code`/`order_code`  
> **P1-1 优化**: `score_display` 为 0~100 归一化百分制  
> **P1-2 优化**: `status: "draft"` 表示未确认

---

### 4.2 确认调度方案

```
POST /api/schedule/confirm/{schedule_code}
```

执行 F021 打包 + 状态更新，draft → active。

**权限**: dispatcher

**约束**:
- 仅 `draft` 状态方案可确认
- 确认时检查关联订单状态是否仍为 `pending`
- 订单状态已变化 → `40003`
- 确认失败 → draft 自动删除 → `50001`

**成功响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "schedule_code": "GS20260625001",
    "status": "active",
    "package_count": 59,
    ...
  }
}
```

---

### 4.3 丢弃 draft 方案

```
DELETE /api/schedule/draft/{schedule_code}
```

**权限**: dispatcher  
**约束**: 仅 `draft` 状态可丢弃

---

### 4.4 历史方案列表

```
GET /api/schedule/global
```

**查询参数**: `page`, `page_size`, `status` (`active`/`draft`)，默认过滤 `draft`

**权限**: 登录即可

---

### 4.5 方案详情

```
GET /api/schedule/global/{schedule_code}
```

**权限**: 登录即可

---

## 5. 节点调度

### 5.1 触发节点调度

```
POST /api/schedule/node-dispatch
```

**权限**: dispatcher

**请求体**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| schedule_code | string | ✅ | 调度方案编码 |
| demo_mode | bool | 否 | 演示模式（默认 `false`） |

**demo_mode=true**: 一次调用完成 L0→L1 和 L1→L2 两次调度（含自动模拟送达 + 重新打包）  
**demo_mode=false**: 仅执行当前阶段调度

**成功响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "batch_code": "BATCH20260625001",
    "level_phase": "l0_l1",
    "dispatch_count": 5,
    "status": "l0_l1_done"
  }
}
```

---

### 5.2 批次列表

```
GET /api/schedule/batches
```

**查询参数**: `page`, `page_size`, `status`, `schedule_code`

**权限**: 登录即可

---

### 5.3 批次详情

```
GET /api/schedule/batches/{batch_code}
```

**查询参数**: `vehicle_code`, `level_phase`（P1-07 新增过滤）

**权限**: 登录即可

> **P1-1 优化**: `tasks` 新增 `from_node_name`/`to_node_name`，`package_codes` 展开为 `package_details`

---

### 5.4 其他调度查询端点 (P1-07)

```
GET /api/schedule/batches/{batch_code}/dispatches    # 按批次查询调度明细
GET /api/schedule/{schedule_code}/dispatches         # 按方案查询所有调度明细
GET /api/schedule/dispatches/{dispatch_code}          # 查询单个调度明细详情
```

**权限**: 登录即可

---

## 6. 路径规划

### 6.1 触发路径规划

```
POST /api/routes/plan
```

**权限**: dispatcher

**请求体**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| batch_code | string | ✅ | 批次编码 |
| dispatch_code | string | 否 | 指定调度明细（不传=批次全部） |

---

### 6.2 路线列表

```
GET /api/routes
```

**查询参数**: `page`, `page_size`, `batch_code`, `vehicle_code`, `schedule_code`

**权限**: 登录即可

---

### 6.3 路线详情

```
GET /api/routes/{route_code}
```

**权限**: 登录即可

**响应包含**:
- `route_segments`: 路段数组 `[{road_name, start_lng, start_lat, end_lng, end_lat}]`
- `total_distance`: 总距离 (km)
- `total_time`: 总时间 (h)
- `carbon_emission`: 碳排放 (kg)

---

### 6.4 车辆路线坐标

```
GET /api/routes/by-vehicle/{vehicle_code}/coordinates
```

**权限**: 登录即可

**响应**: 前端可视化用坐标数组

---

## 7. 模拟送达

### 7.1 模拟送达

```
POST /api/simulation/deliver
```

驱动状态流转（按车辆 / 按包裹 / 全部送达）。

**权限**: dispatcher

**请求体** (三选一):
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| vehicle_code | string | 条件 | 按车辆送达 |
| package_code | string | 条件 | 按包裹送达 |
| 都不传 | — | — | 全部送达 |

> **P1-3 语义修正**: 送达后 `goods.status` 保持 `in_transit`（不变），仅更新 `goods.node_id`。货物状态变化统一由 `confirm-arrival` 驱动。

---

### 7.2 送达状态查询

```
GET /api/simulation/status/{batch_code}
```

**权限**: 登录即可

---

### 7.3 批量送达 (P1)

```
POST /api/simulation/deliver-batch
```

**权限**: dispatcher

---

## 8. 到货确认 (P1-3)

### 8.1 单个到货确认

```
POST /api/simulation/confirm-arrival
```

**权限**: 登录即可

**请求体**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| schedule_code | string | ✅ | 调度方案编号 |
| package_code | string | ✅ | 到站包裹编号 |
| is_normal | bool | ✅ | 是否正常到站 |
| exception_subtype | string | 否 | 异常子类型（仅 `is_normal=false` 时必填） |
| remark | string | 否 | 备注 |

**正常路径**: 货物标记到位 → L1 到达触发 `_trigger_repacking` 生成 L1→L2 包裹  
**异常路径**: 包裹/货物/订单 → `exception`，写入 `exception_events` 审计

**成功响应**:
```json
{
  "code": 0,
  "data": {
    "package_code": "PKG001",
    "status": "confirmed",
    "goods_status": "pending_pack",
    "triggered_repacking": true,
    "new_package_code": "PKG20260625002"
  }
}
```

---

### 8.2 批量到货确认

```
POST /api/simulation/confirm-arrival-batch
```

**权限**: 登录即可

**请求体**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| schedule_code | string | ✅ | 调度方案编号（所有包裹必须属于该方案） |
| confirmations | array | ✅ | 确认列表 |

**confirmations 每项**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| package_code | string | ✅ | 包裹编号 |
| is_normal | bool | ✅ | 是否正常到站 |
| exception_subtype | string | 否 | 异常子类型 |
| remark | string | 否 | 备注 |

**事务性**: 预校验所有包裹 → 逐条确认 → 统一 commit；任一失败全部回滚。

---

### 8.3 查询待确认包裹

```
GET /api/simulation/arrival-packages
```

**查询参数**: `schedule_code`

**权限**: 登录即可

---

## 9. 异常管理

### 9.1 异常事件列表

```
GET /api/exceptions
```

**查询参数**: `page`, `page_size`, `exception_type`, `status`, `related_schedule_code`

**权限**: 登录即可

---

### 9.2 创建异常事件

```
POST /api/exceptions
```

**权限**: dispatcher

**请求体**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| exception_type | string | ✅ | `road` / `package` / `node` |
| exception_subtype | string | 否 | `congestion` / `damage` / `capacity_limit` / `road_closed` / `road_accident` / `node_maintenance` / `storage_timeout` / `vehicle_breakdown` |
| target_type | string | 否 | `node` / `package` / `route` / `vehicle` |
| target_code | string | 否 | 目标实体编码 |
| recommended_action | string | ✅ | `redispatch` / `reroute` |
| related_schedule_code | string | 否 | 关联调度方案编码 |
| description | string | 否 | 异常描述 |

**redispatch 场景** (`recommended_action=redispatch`):
| 异常类型 | exception_subtype | target_type | 说明 |
|---------|-------------------|-------------|------|
| `node` | `capacity_limit` | `node` | 分拣中心容量不足 |
| `node` | `storage_timeout` | `node` | 存储中心货物积压超时 |
| `node` | `node_maintenance` | `node` | 节点维修关停 |
| `vehicle` | `vehicle_breakdown` | `vehicle` | 车辆故障 |

**reroute 场景** (`recommended_action=reroute`):
| 异常类型 | exception_subtype | target_type | 说明 |
|---------|-------------------|-------------|------|
| `road` | `road_closed` | `route` | 道路封闭 |
| `road` | `congestion` | `route` | 严重拥堵 |
| `road` | `road_accident` | `route` | 交通事故 |

> **副作用**: 创建异常后自动将关联订单/货物/包裹状态置为 `exception`；`target_type=vehicle` 时车辆 → `disabled`

---

### 9.3 异常事件详情

```
GET /api/exceptions/{event_code}
```

**权限**: 登录即可

---

### 9.4 触发重规划

```
POST /api/exceptions/{event_code}/replan
```

**权限**: dispatcher

**请求体**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| action | string | ✅ | `redispatch` / `reroute` |
| reason | string | ✅ | 重规划原因 |

**redispatch 响应**:
```json
{
  "code": 0,
  "data": {
    "schedule_code": "GS20260625002",
    "new_schedule_code": "GS20260625002",
    "batch_code": "BATCH20260625002",
    "version": 2,
    "is_replan": true,
    "replan_reason": "L1001 容量溢出 120%，分流 3 票货物至 L1002",
    "original_schedule_code": "GS20260625001"
  }
}
```

**reroute 响应**:
```json
{
  "code": 0,
  "data": {
    "batch_code": "BATCH20260625001",
    "route_codes": ["RT202606250002"],
    "new_route_code": "RT202606250002",
    "version": 2,
    "is_replan": true,
    "replan_reason": "原路线途经封闭路段，绕行替代路径",
    "original_route_code": "RT202606250001"
  }
}
```

---

### 9.5 更新异常事件

```
PUT /api/exceptions/{event_code}
```

**权限**: dispatcher

---

### 9.6 标记异常已解决

```
PUT /api/exceptions/{event_code}/resolve
```

**权限**: dispatcher  
**副作用**: `status` → `resolved`，自动记录 `resolved_at`

---

## 10. AI 助手

### 10.1 自然语言解析与调度

```
POST /api/ai/parse
```

**权限**: dispatcher

**请求体**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| message | string | 否 | 自然语言指令 |
| weights | object | 否 | 手动权重（结构与 `algorithm_config.json` 一致） |
| schedule_codes | string[] | 否 | 目标方案编码列表（非空=重规划） |
| execute | string | 否 | `"draft"`=生成 draft 方案 / `"dry-run"`=仅返回参数（默认 `"draft"`） |

**四种参数模式**:

| 条件 | 模式 | 说明 |
|------|------|------|
| 有 `message`，无 `weights` | `ai` | DeepSeek 解析自然语言 |
| 无 `message`，有 `weights` | `manual` | 直接使用手动权重 |
| 有 `message`，有 `weights` | `hybrid` | DeepSeek 解析后用 `weights` 覆盖 |
| 无 `message`，无 `weights` | `default` | 使用 `algorithm_config.json` 默认值 |

**请求示例**:
```json
// AI 重规划（最常用）
{"message": "优先缩短距离，多用电车", "schedule_codes": ["GS20260625001"]}

// AI 新建调度
{"message": "优先时效，减少总时间"}

// dry-run 预览
{"message": "缩短距离，减少碳排放", "execute": "dry-run"}

// 纯手动权重
{
  "weights": {"global_schedule": {"weights": {"distance": 0.9, "time": 0.05, "package_count": 0.05}}},
  "schedule_codes": ["GS20260625001"]
}

// 默认参数
{"schedule_codes": ["GS20260625001"]}
```

**成功响应 (draft 模式)**:
```json
{
  "code": 0,
  "data": {
    "schedule_code": "GS20260625010",
    "algorithm_params": {
      "global_schedule": {"weights": {"distance": 0.7, "time": 0.2, "package_count": 0.1}}
    },
    "mode": "ai",
    "is_replan": true,
    "status": "draft",
    "reference_codes": ["GS20260625001"]
  },
  "meta": {"degraded": false, "degraded_reason": null}
}
```

**成功响应 (dry-run 模式)**:
```json
{
  "code": 0,
  "message": "success (dry-run)",
  "data": {
    "algorithm_params": {
      "global_schedule": {"weights": {"distance": 0.8, "time": 0.15, "package_count": 0.05}}
    },
    "mode": "ai"
  },
  "meta": {"degraded": false, "degraded_reason": null}
}
```

---

### 10.2 方案解释 (F015)

```
POST /api/ai/explain
```

**权限**: 登录即可

**请求体**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| schedule_code | string | 条件 | 调度方案编码（与 batch_code 至少提供一个） |
| batch_code | string | 条件 | 调度批次编码（与 schedule_code 至少提供一个） |

**成功响应**:
```json
{
  "code": 0,
  "data": {
    "explanation": "该方案采用传统贪心算法，优先选择距离最短的L1分拣中心...",
    "key_decisions": [
      "选择SO001作为中间节点，距离最优",
      "17件货物分配至3个L1节点"
    ],
    "potential_risks": [
      "SO001容量使用率达85%，建议扩容",
      "部分路线途经拥堵高发区域"
    ],
    "suggestions": [
      "增加SO001容量配置",
      "考虑SO003作为备选分流节点"
    ]
  }
}
```

**降级响应** (DeepSeek 不可用):
```json
{
  "code": 0,
  "data": {
    "explanation": "AI服务暂时不可用，请稍后重试",
    "key_decisions": [],
    "potential_risks": [],
    "suggestions": []
  },
  "meta": {
    "degraded": true,
    "degraded_reason": "DeepSeek API 调用超时（60秒）"
  }
}
```

---

### 10.3 方案审查 (F016)

```
POST /api/ai/review
```

**权限**: 登录即可

**请求体**: 同 `/api/ai/explain`

**成功响应**:
```json
{
  "code": 0,
  "data": {
    "risks": [
      {
        "type": "容量风险",
        "description": "SO001容量使用率达85%，接近上限",
        "severity": "medium",
        "suggestion": "建议启用SO003作为分流节点"
      },
      {
        "type": "时效风险",
        "description": "3条路线预计用时超过12小时",
        "severity": "high",
        "suggestion": "考虑拆分长距离路线或增加中转"
      }
    ]
  }
}
```

---

### 10.4 异常分析 (F017)

```
POST /api/ai/analyze-exception
```

**权限**: 登录即可

**请求体**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| event_code | string | ✅ | 异常事件编码 |

**成功响应**:
```json
{
  "code": 0,
  "data": {
    "root_cause": "SO002节点维护关停导致3条路线中断，影响5件货物",
    "suggestions": [
      "立即触发redispatch，将受影响货物重分配至SO001或SO003",
      "后续调度方案中降低SO002权重"
    ],
    "auto_fix_available": true
  }
}
```

---

## 11. 健康检查

```
GET /api/health
```

**无需认证**

**成功响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "status": "healthy",
    "version": "1.0.0"
  }
}
```

---

## 12. 错误码速查

| code | HTTP | 说明 | 触发场景 |
|------|------|------|----------|
| `0` | 200 | 成功 | — |
| `40000` | 400 | 参数校验失败 | 请求体格式/必填字段/类型错误 |
| `40001` | 200 | 业务逻辑失败 | 无可用车辆、无待调度订单、L0→L1 未完成 |
| `40002` | 200 | 已有活跃方案 | 同批订单已存在 active 方案 |
| `40003` | 200 | 订单状态已变化 | confirm 时订单不是 pending |
| `40100` | 200 | 用户名或密码错误 | 登录接口 |
| `40100` | 401 | 未登录或 Token 无效 | Token 缺失/格式错误/密钥不匹配 |
| `40101` | 401 | Token 已过期 | JWT 过期 |
| `40300` | 403 | 无权限 | manager 角色尝试写操作 |
| `40400` | 404 | 资源不存在 | 路由不匹配 |
| `40401` | 200 | 指定资源不存在 | 查不存在的 schedule_code 等 |
| `50000` | 500 | 服务器内部错误 | 未捕获异常 |
| `50001` | 200 | draft 已丢弃 | confirm 异常时 draft 自动删除 |

---

> **文档维护**: 本文档在阶段 1–8 + P1-1 + P1-2 + P1-3 全部完成后生成，覆盖所有已实现端点。后续新增端点应同步更新本文档。
