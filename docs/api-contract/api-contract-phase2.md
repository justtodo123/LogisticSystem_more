# 阶段2：基础数据管理 - API 契约文档

> **文档版本**：V1.3
> **更新时间**：2026年6月13日
> **阶段范围**：F001订单管理、F001-1货物管理、F001-2包裹管理、F002车辆管理、F003司机管理、F004存储中心管理、F004-1分拣中心管理
> **参考资料**：PRD V2.7、系统架构设计说明书V1.0、阶段2开发文档V1.2、阶段2实际实现
> 
> **更新说明（V1.3）**：
> - 根据实际实现更新：货物管理只有GET/PUT，无POST/DELETE
> - 包裹管理只有GET/repack，无POST/DELETE
> - 车辆创建请求体增加`node_code`字段
> - 节点详情响应结构与实际实现对齐
> - 订单导入接口实际已实现（POST /api/orders/import）

---

## 一、API 基本约定

### 1.1 基础信息

| 项 | 约定 |
| --- | --- |
| Base URL | `http://localhost:8000/api` |
| 协议 | HTTP/JSON，UTF-8 |
| 版本 | MVP 不加 `/v1` 前缀 |
| 时间格式 | ISO 8601，`2026-06-09T10:00:00+08:00` |
| 标识符 | 请求/响应中业务对象使用 `*_code`，不使用数据库 `id` |
| 分页 | `?page=1&page_size=20`；响应含 `total` |

### 1.2 统一响应格式

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
  "message": "无法完成全局调度，请增加1级分拣中心容量或减少订单",
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
      "order_code": "必填"
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

### 1.3 认证方式

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

### 1.4 错误码

| code | HTTP | 说明 |
| --- | --- | --- |
| 0 | 200 | 成功 |
| 40000 | 400 | 参数校验失败 |
| 40100 | 401 | 未登录或 Token 无效 |
| 40101 | 401 | Token 过期 |
| 40300 | 403 | 无权限 |
| 40400 | 404 | 资源不存在 |
| 40900 | 409 | 资源冲突（如重复编号） |
| 50000 | 500 | 系统内部错误 |

---

## 二、认证 API（已实现）

### 2.1 登录

```
POST /api/auth/login
```

**请求体**：

```json
{
  "username": "dispatcher",
  "password": "123456"
}
```

**响应 data**：

```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 86400,
  "role": "dispatcher",
  "display_name": "调度员"
}
```

### 2.2 当前用户信息

```
GET /api/auth/me
```

**响应 data**：

```json
{
  "user_code": "U001",
  "username": "dispatcher",
  "role": "dispatcher",
  "display_name": "调度员"
}
```

### 2.3 登出

```
POST /api/auth/logout
```

**响应 data**：`null`

---

## 三、订单管理 API（F001）

### 3.1 订单列表

```
GET /api/orders
```

**Query 参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |
| status | string | 否 | 状态筛选：pending/delivering/completed/exception |

**响应 data**：

```json
{
  "items": [
    {
      "order_code": "O001",
      "destination_node_code": "L2001",
      "destination_node_name": "武汉0级分拣中心(1)",
      "time_window": "9:00-18:00",
      "status": "pending",
      "goods_count": 3,
      "created_at": "2026-06-13T10:00:00",
      "updated_at": "2026-06-13T10:00:00"
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20
}
```

### 3.2 订单详情

```
GET /api/orders/{order_code}
```

**响应 data**：

```json
{
  "order_code": "O001",
  "destination_node_code": "L2001",
  "destination_node_name": "武汉0级分拣中心(1)",
  "time_window": "9:00-18:00",
  "status": "pending",
  "goods": [
    {
      "goods_code": "GO001_1",
      "goods_name": "电子产品",
      "goods_type": "电子产品",
      "weight": 2.5,
      "volume": 0.5,
      "status": "pending_pack"
    }
  ],
  "created_at": "2026-06-13T10:00:00",
  "updated_at": "2026-06-13T10:00:00"
}
```

### 3.3 新增订单

```
POST /api/orders
```

**请求体**：

```json
{
  "destination_node_code": "L2001",
  "time_window": "9:00-18:00",
  "goods": [
    {
      "goods_name": "电子产品",
      "goods_type": "电子产品",
      "weight": 2.5,
      "volume": 0.5
    }
  ]
}
```

**请求体验证规则**：

| 字段 | 类型 | 必填 | 验证规则 |
| --- | --- | --- | --- |
| destination_node_code | string | 是 | 目标节点编号，必须存在 |
| time_window | string | 是 | 时效要求 |
| goods | array | 是 | 货物列表，至少1个 |
| goods[].goods_name | string | 是 | 货物名称 |
| goods[].goods_type | string | 是 | 货物类型 |
| goods[].weight | float | 是 | 重量（kg），>0 |
| goods[].volume | float | 是 | 体积（m³），>0 |

**响应 data**：

```json
{
  "order_code": "O051",
  "destination_node_code": "L2001",
  "destination_node_name": "武汉0级分拣中心(1)",
  "time_window": "9:00-18:00",
  "status": "pending",
  "goods_count": 1,
  "created_at": "2026-06-13T10:00:00",
  "updated_at": "2026-06-13T10:00:00"
}
```

**响应失败（HTTP 200，业务错误）**：

| code | message | 说明 |
| --- | --- | --- |
| 40001 | 目标节点不存在 | destination_node_code 无效 |
| 40001 | 货物列表不能为空 | goods 数组为空 |

### 3.4 编辑订单

```
PUT /api/orders/{order_code}
```

**请求体**：

```json
{
  "destination_node_code": "L2002",
  "time_window": "10:00-20:00"
}
```

**约束**：仅 `status=pending` 的订单可编辑。

**响应 data**：同新增订单响应。

### 3.5 删除订单

```
DELETE /api/orders/{order_code}
```

**约束**：仅 `status=pending` 的订单可删除；`delivering/completed/exception` 状态不可删除。

**响应 data**：

```json
{
  "order_code": "O001"
}
```

**响应失败（HTTP 200，业务错误）**：

| code | message | 说明 |
| --- | --- | --- |
| 40002 | 仅 pending 状态订单可删除 | 订单已调度，无法删除 |

### 3.6 批量导入订单

```
POST /api/orders/import
Content-Type: multipart/form-data
```

**Form 参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| file | File | 是 | Excel(.xlsx) 文件 |
| skip_errors | boolean | 否 | 是否跳过错误行，默认true（部分成功） |

**响应 data**：

```json
{
  "success_count": 10,
  "failed_count": 2,
  "failed_rows": [
    {
      "row": 3,
      "error": "目标节点不存在"
    }
  ]
}
```

**导入模板字段**（Excel 首行）：

| 列名 | 说明 | 必填 |
| --- | --- | --- |
| destination_node_code | 目的节点编号 | 是 |
| time_window | 时效要求 | 是 |
| goods_name | 货物名称 | 是 |
| goods_type | 货物类型 | 是 |
| weight | 重量(kg) | 是 |
| volume | 体积(m³) | 是 |

---

## 四、货物管理 API（F001-1）

> **说明**：阶段2货物管理仅支持查询和编辑，不支持单独创建和删除（货物通过订单创建时自动生成）。

### 4.1 货物列表

```
GET /api/goods
```

**Query 参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |
| status | string | 否 | 状态筛选：pending_pack/packed/in_transit/delivered/exception |
| node_code | string | 否 | 所属节点筛选 |

**响应 data**：

```json
{
  "items": [
    {
      "goods_code": "GO001_1",
      "goods_name": "电子产品",
      "goods_type": "电子产品",
      "weight": 2.5,
      "volume": 0.5,
      "node_code": "L2001",
      "node_name": "武汉0级分拣中心(1)",
      "order_code": "O001",
      "status": "pending_pack",
      "created_at": "2026-06-13T10:00:00",
      "updated_at": "2026-06-13T10:00:00"
    }
  ],
  "total": 200,
  "page": 1,
  "page_size": 20
}
```

### 4.2 货物详情

```
GET /api/goods/{goods_code}
```

**响应 data**：

```json
{
  "goods_code": "GO001_1",
  "goods_name": "电子产品",
  "goods_type": "电子产品",
  "weight": 2.5,
  "volume": 0.5,
  "node_code": "L2001",
  "node_name": "武汉0级分拣中心(1)",
  "order_code": "O001",
  "status": "pending_pack",
  "created_at": "2026-06-13T10:00:00",
  "updated_at": "2026-06-13T10:00:00"
}
```

### 4.3 编辑货物

```
PUT /api/goods/{goods_code}
```

**请求体**：

```json
{
  "goods_name": "电子产品（改）",
  "goods_type": "电子产品",
  "weight": 3.0,
  "volume": 0.6,
  "node_code": "L2002"
}
```

**请求体验证规则**：

| 字段 | 类型 | 必填 | 验证规则 |
| --- | --- | --- | --- |
| goods_name | string | 否 | 货物名称 |
| goods_type | string | 否 | 货物类型 |
| weight | float | 否 | 重量（kg），>0 |
| volume | float | 否 | 体积（m³），>0 |
| node_code | string | 否 | 节点编号 |

**响应 data**：同货物详情响应。

**响应失败（HTTP 200，业务错误）**：

| code | message | 说明 |
| --- | --- | --- |
| 40003 | 货物不存在 | 货物编号无效 |

---

---

## 五、包裹管理 API（F001-2）

> **说明**：阶段2包裹管理仅支持查询和重新打包，不支持单独创建和删除（包裹通过调度算法F021自动生成）。

### 5.1 包裹列表

```
GET /api/packages
```

**Query 参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |
| status | string | 否 | 状态筛选：pending_pack/packed/in_transit/delivered/exception |
| from_node_code | string | 否 | 发送地节点筛选 |
| to_node_code | string | 否 | 接收地节点筛选 |

**响应 data**：

```json
{
  "items": [
    {
      "package_code": "PKG001",
      "weight": 15.5,
      "volume": 0.8,
      "status": "pending_pack",
      "from_node_code": "SC001",
      "from_node_name": "武汉存储中心(东)",
      "to_node_code": "L1001",
      "to_node_name": "武汉1级分拣中心(北)",
      "from_longitude": 114.4,
      "from_latitude": 30.5,
      "to_longitude": 114.3,
      "to_latitude": 30.55,
      "goods_items": [
        {
          "goods_code": "GO001_1",
          "order_code": "O001"
        }
      ],
      "dispatch_code": null,
      "created_at": "2026-06-13T10:00:00",
      "updated_at": "2026-06-13T10:00:00"
    }
  ],
  "total": 45,
  "page": 1,
  "page_size": 20
}
```

### 5.2 包裹详情

```
GET /api/packages/{package_code}
```

**响应 data**：

```json
{
  "package_code": "PKG001",
  "weight": 15.5,
  "volume": 0.8,
  "status": "pending_pack",
  "from_node_code": "SC001",
  "from_node_name": "武汉存储中心(东)",
  "to_node_code": "L1001",
  "to_node_name": "武汉1级分拣中心(北)",
  "from_longitude": 114.4,
  "from_latitude": 30.5,
  "to_longitude": 114.3,
  "to_latitude": 30.55,
  "goods_items": [
    {
      "goods_code": "GO001_1",
      "order_code": "O001"
    }
  ],
  "dispatch_code": null,
  "created_at": "2026-06-13T10:00:00",
  "updated_at": "2026-06-13T10:00:00"
}
```

### 5.3 手动重新打包

```
POST /api/packages/{package_code}/repack
```

**请求体**：

```json
{
  "goods_codes": ["GO001_1", "GO001_2"]
}
```

**请求体验证规则**：

| 字段 | 类型 | 必填 | 验证规则 |
| --- | --- | --- | --- |
| goods_codes | array | 是 | 货物编号列表，至少1个 |

**说明**：拆开原包裹，将指定货物重新打包成新包裹。原包裹状态变为 `exception`，新包裹状态为 `pending_pack`。

**响应 data**：

```json
{
  "package_code": "PKG045",
  "weight": 10.0,
  "volume": 0.5,
  "status": "pending_pack",
  "from_node_code": "SC001",
  "from_node_name": "武汉存储中心(东)",
  "to_node_code": "L1001",
  "to_node_name": "武汉1级分拣中心(北)",
  "goods_items": [
    {
      "goods_code": "GO001_1",
      "order_code": "O001"
    }
  ],
  "created_at": "2026-06-13T11:00:00",
  "updated_at": "2026-06-13T11:00:00"
}
```

**响应失败（HTTP 200，业务错误）**：

| code | message | 说明 |
| --- | --- | --- |
| 40004 | 包裹不存在 | 包裹编号无效 |
| 40005 | 包裹状态不允许repack | 包裹状态不为pending_pack |
| 40005 | 货物不属于原包裹 | goods_codes包含非原包裹货物 |

---

## 六、车辆管理 API（F002）

### 6.1 车辆列表

```
GET /api/vehicles
```

**Query 参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |
| status | string | 否 | 状态筛选：idle/delivering/maintenance/disabled |
| node_code | string | 否 | 所属节点筛选 |

**响应 data**：

```json
{
  "items": [
    {
      "vehicle_code": "VEHSC00101",
      "model": "东风卡车",
      "capacity": 5.0,
      "energy_type": "fuel",
      "vehicle_type": "normal",
      "capability_tags": null,
      "last_arrived_node_code": "SC001",
      "last_arrived_node_name": "武汉存储中心(东)",
      "status": "idle",
      "node_code": "SC001",
      "node_name": "武汉存储中心(东)",
      "created_at": "2026-06-13T10:00:00",
      "updated_at": "2026-06-13T10:00:00"
    }
  ],
  "total": 70,
  "page": 1,
  "page_size": 20
}
```

### 6.2 车辆详情

```
GET /api/vehicles/{vehicle_code}
```

**响应 data**：

```json
{
  "vehicle_code": "VEHSC00101",
  "model": "东风卡车",
  "capacity": 5.0,
  "energy_type": "fuel",
  "vehicle_type": "normal",
  "capability_tags": null,
  "last_arrived_node_code": "SC001",
  "last_arrived_node_name": "武汉存储中心(东)",
  "status": "idle",
  "node_code": "SC001",
  "node_name": "武汉存储中心(东)",
  "created_at": "2026-06-13T10:00:00",
  "updated_at": "2026-06-13T10:00:00"
}
```

### 6.3 新增车辆

```
POST /api/vehicles
```

**请求体**：

```json
{
  "vehicle_code": "VEHSC00111",
  "model": "东风卡车",
  "capacity": 5.0,
  "energy_type": "fuel",
  "vehicle_type": "normal",
  "capability_tags": null,
  "last_arrived_node_code": "SC001",
  "node_code": "SC001",
  "status": "idle"
}
```

**请求体验证规则**：

| 字段 | 类型 | 必填 | 验证规则 |
| --- | --- | --- | --- |
| vehicle_code | string | 是 | 车辆编号，唯一 |
| model | string | 是 | 车型 |
| capacity | float | 是 | 载重（吨），>0 |
| energy_type | string | 是 | 能源类型：fuel/electric |
| vehicle_type | string | 否 | 车辆类型：normal/cold_chain |
| capibility_tags | array | 否 | 能力标签 |
| last_arrived_node_code | string | 是 | 最后到达节点编号 |
| node_code | string | 是 | 所属节点编号 |
| status | string | 否 | 状态：idle/delivering/maintenance/disabled |

**响应 data**：同车辆详情响应。

**响应失败（HTTP 200，业务错误）**：

| code | message | 说明 |
| --- | --- | --- |
| 40006 | 车辆不存在 | 车辆编号无效 |
| 40900 | 车辆编号已存在 | vehicle_code 重复 |

### 6.4 编辑车辆

```
PUT /api/vehicles/{vehicle_code}
```

**请求体**：

```json
{
  "model": "东风卡车（改）",
  "capacity": 6.0,
  "energy_type": "electric",
  "vehicle_type": "normal",
  "capability_tags": null,
  "status": "maintenance"
}
```

**请求体验证规则**：

| 字段 | 类型 | 必填 | 验证规则 |
| --- | --- | --- | --- |
| model | string | 否 | 车型 |
| capacity | float | 否 | 载重（吨），>0 |
| energy_type | string | 否 | 能源类型：fuel/electric |
| vehicle_type | string | 否 | 车辆类型 |
| capibility_tags | array | 否 | 能力标签 |
| last_arrived_node_code | string | 否 | 最后到达节点编号 |
| status | string | 否 | 状态 |

**约束**：`status=delivering` 的车辆不允许编辑。

**响应 data**：同车辆详情响应。

**响应失败（HTTP 200，业务错误）**：

| code | message | 说明 |
| --- | --- | --- |
| 40007 | 车辆状态不允许编辑 | 车辆状态为delivering |

### 6.5 删除车辆

```
DELETE /api/vehicles/{vehicle_code}
```

**约束**：`status=delivering` 的车辆不允许删除。

**响应 data**：

```json
{
  "vehicle_code": "VEHSC00101"
}
```

**响应失败（HTTP 200，业务错误）**：

| code | message | 说明 |
| --- | --- | --- |
| 40007 | 车辆状态不允许删除 | 车辆状态为delivering |

---

## 七、司机管理 API（F003）

### 7.1 司机列表

```
GET /api/drivers
```

**Query 参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |
| status | string | 否 | 状态筛选：idle/busy |
| node_code | string | 否 | 所属节点筛选 |

**响应 data**：

```json
{
  "items": [
    {
      "driver_code": "D001",
      "name": "张三",
      "phone": "13800138000",
      "license_type": "C1",
      "shift": "早班",
      "node_code": "SC001",
      "node_name": "存储中心1",
      "status": "idle",
      "created_at": "2026-06-09T10:00:00+08:00"
    }
  ],
  "total": 70,
  "page": 1,
  "page_size": 20
}
```

### 7.2 司机详情

```
GET /api/drivers/{driver_code}
```

**响应 data**：

```json
{
  "driver_code": "D001",
  "name": "张三",
  "phone": "13800138000",
  "license_type": "C1",
  "shift": "早班",
  "node_code": "SC001",
  "node_name": "存储中心1",
  "status": "idle",
  "created_at": "2026-06-09T10:00:00+08:00",
  "updated_at": "2026-06-09T10:00:00+08:00"
}
```

### 7.3 新增司机

```
POST /api/drivers
```

**请求体**：

```json
{
  "driver_code": "DRVSC00171",
  "name": "司机SC001-71",
  "phone": "13800000071",
  "license_type": "C1",
  "shift": "day",
  "node_code": "SC001",
  "status": "idle"
}
```

**请求体验证规则**：

| 字段 | 类型 | 必填 | 验证规则 |
| --- | --- | --- | --- |
| driver_code | string | 是 | 司机编号，唯一 |
| name | string | 是 | 姓名 |
| phone | string | 是 | 电话 |
| license_type | string | 是 | 驾照类型：C1/C2/B1/B2/A1/A2 |
| shift | string | 是 | 班次：day/night |
| node_code | string | 是 | 所属节点编号 |
| status | string | 否 | 状态：idle/busy |

**响应 data**：同司机详情响应。

**响应失败（HTTP 200，业务错误）**：

| code | message | 说明 |
| --- | --- | --- |
| 40008 | 司机不存在 | 司机编号无效 |
| 40900 | 司机编号已存在 | driver_code 重复 |

### 7.4 编辑司机

```
PUT /api/drivers/{driver_code}
```

**请求体**：

```json
{
  "name": "司机SC001-71（改）",
  "phone": "13800000072",
  "license_type": "C2",
  "shift": "night",
  "node_code": "SC002"
}
```

**请求体验证规则**：

| 字段 | 类型 | 必填 | 验证规则 |
| --- | --- | --- | --- |
| name | string | 否 | 姓名 |
| phone | string | 否 | 电话 |
| license_type | string | 否 | 驾照类型 |
| shift | string | 否 | 班次 |
| node_code | string | 否 | 所属节点编号 |
| status | string | 否 | 状态 |

**约束**：有未完成订单的司机不允许删除（编辑无此限制）。

**响应 data**：同司机详情响应。

**响应失败（HTTP 200，业务错误）**：

| code | message | 说明 |
| --- | --- | --- |
| 40009 | 司机有未完成订单 | 司机有关联的未完成订单 |

### 7.5 删除司机

```
DELETE /api/drivers/{driver_code}
```

**约束**：有未完成订单的司机不允许删除。

**响应 data**：

```json
{
  "driver_code": "DRVSC00171"
}
```

**响应失败（HTTP 200，业务错误）**：

| code | message | 说明 |
| --- | --- | --- |
| 40009 | 司机有未完成订单 | 司机有关联的未完成订单 |

---

## 八、节点管理 API（F004/F004-1）

### 8.1 节点列表

```
GET /api/nodes
```

**Query 参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |
| node_type | string | 否 | 节点类型筛选：storage_center/sorting_center |

**响应 data**：

```json
{
  "items": [
    {
      "node_code": "SC001",
      "name": "武汉存储中心(东)",
      "location": "30.5, 114.4",
      "latitude": 30.5,
      "longitude": 114.4,
      "node_type": "storage_center",
      "created_at": "2026-06-13T10:00:00",
      "updated_at": "2026-06-13T10:00:00"
    }
  ],
  "total": 57,
  "page": 1,
  "page_size": 20
}
```

### 8.2 节点详情

```
GET /api/nodes/{node_code}
```

**响应 data**：

```json
{
  "node_code": "SC001",
  "name": "武汉存储中心(东)",
  "location": "30.5, 114.4",
  "latitude": 30.5,
  "longitude": 114.4,
  "node_type": "storage_center",
  "capacity": 1000.0,
  "inventory": 0,
  "level": null,
  "max_storage_time": null,
  "created_at": "2026-06-13T10:00:00",
  "updated_at": "2026-06-13T10:00:00"
}
```

---

## 九、存储中心管理 API（F004）

### 9.1 新增存储中心

```
POST /api/nodes/storage-centers
```

**请求体**：

```json
{
  "node_code": "SC006",
  "name": "武汉存储中心(北)",
  "location": "30.58, 114.3",
  "latitude": 30.58,
  "longitude": 114.3,
  "capacity": 1000.0,
  "inventory": 0
}
```

**请求体验证规则**：

| 字段 | 类型 | 必填 | 验证规则 |
| --- | --- | --- | --- |
| node_code | string | 是 | 节点编号，唯一 |
| name | string | 是 | 名称 |
| location | string | 是 | 位置描述 |
| latitude | float | 是 | 纬度 |
| longitude | float | 是 | 经度 |
| capacity | float | 是 | 容量 |
| inventory | int | 否 | 库存，默认0 |

**说明**：原子操作，同时创建 `nodes` 记录和 `storage_centers` 记录。

**响应 data**：

```json
{
  "node_code": "SC006",
  "name": "武汉存储中心(北)",
  "location": "30.58, 114.3",
  "latitude": 30.58,
  "longitude": 114.3,
  "node_type": "storage_center",
  "capacity": 1000.0,
  "inventory": 0,
  "created_at": "2026-06-13T10:00:00",
  "updated_at": "2026-06-13T10:00:00"
}
```

**响应失败（HTTP 200，业务错误）**：

| code | message | 说明 |
| --- | --- | --- |
| 40011 | 存储中心不存在 | 节点编号无效 |
| 40900 | 存储中心编号已存在 | node_code 重复 |

### 9.2 编辑存储中心

```
PUT /api/nodes/storage-centers/{node_code}
```

**请求体**：

```json
{
  "name": "武汉存储中心(北)（改）",
  "location": "30.59, 114.25",
  "latitude": 30.59,
  "longitude": 114.25,
  "capacity": 1200.0,
  "inventory": 50
}
```

**请求体验证规则**：

| 字段 | 类型 | 必填 | 验证规则 |
| --- | --- | --- | --- |
| name | string | 否 | 名称 |
| location | string | 否 | 位置描述 |
| latitude | float | 否 | 纬度 |
| longitude | float | 否 | 经度 |
| capacity | float | 否 | 容量 |
| inventory | int | 否 | 库存 |

**响应 data**：同新增存储中心响应。

### 9.3 删除存储中心

```
DELETE /api/nodes/storage-centers/{node_code}
```

**约束**：需确认无关联未完成任务。

**响应 data**：

```json
{
  "node_code": "SC006"
}
```

**响应失败（HTTP 200，业务错误）**：

| code | message | 说明 |
| --- | --- | --- |
| 40011 | 存储中心不存在 | 节点编号无效 |

---

## 十、分拣中心管理 API（F004-1）

### 10.1 新增分拣中心

```
POST /api/nodes/sorting-centers
```

**请求体**：

```json
{
  "node_code": "L1052",
  "name": "武汉1级分拣中心(西)",
  "location": "30.51, 114.2",
  "latitude": 30.51,
  "longitude": 114.2,
  "level": 1,
  "capacity": 500,
  "max_storage_time": 24
}
```

**请求体验证规则**：

| 字段 | 类型 | 必填 | 验证规则 |
| --- | --- | --- | --- |
| node_code | string | 是 | 节点编号，唯一 |
| name | string | 是 | 名称 |
| location | string | 是 | 位置描述 |
| latitude | float | 是 | 纬度 |
| longitude | float | 是 | 经度 |
| level | int | 是 | 级别：0/1 |
| capacity | int | 否 | 容量（level=0时可空） |
| max_storage_time | int | 否 | 最大存储时长（level=0时可空） |

**说明**：原子操作，同时创建 `nodes` 记录和 `sorting_centers` 记录。`level=0` 时 `capacity` 和 `max_storage_time` 可空。

**响应 data**：

```json
{
  "node_code": "L1052",
  "name": "武汉1级分拣中心(西)",
  "location": "30.51, 114.2",
  "latitude": 30.51,
  "longitude": 114.2,
  "node_type": "sorting_center",
  "level": 1,
  "capacity": 500,
  "max_storage_time": 24,
  "created_at": "2026-06-13T10:00:00",
  "updated_at": "2026-06-13T10:00:00"
}
```

**响应失败（HTTP 200，业务错误）**：

| code | message | 说明 |
| --- | --- | --- |
| 40012 | 分拣中心不存在 | 节点编号无效 |
| 40900 | 分拣中心编号已存在 | node_code 重复 |

### 10.2 编辑分拣中心

```
PUT /api/nodes/sorting-centers/{node_code}
```

**请求体**：

```json
{
  "name": "武汉1级分拣中心(西)（改）",
  "location": "30.5, 114.18",
  "latitude": 30.5,
  "longitude": 114.18,
  "capacity": 600,
  "max_storage_time": 36
}
```

**请求体验证规则**：

| 字段 | 类型 | 必填 | 验证规则 |
| --- | --- | --- | --- |
| name | string | 否 | 名称 |
| location | string | 否 | 位置描述 |
| latitude | float | 否 | 纬度 |
| longitude | float | 否 | 经度 |
| level | int | 否 | 级别 |
| capacity | int | 否 | 容量 |
| max_storage_time | int | 否 | 最大存储时长 |

**响应 data**：同新增分拣中心响应。

### 10.3 删除分拣中心

```
DELETE /api/nodes/sorting-centers/{node_code}
```

**约束**：需确认无关联未完成任务。

**响应 data**：

```json
{
  "node_code": "L1052"
}
```

**响应失败（HTTP 200，业务错误）**：

| code | message | 说明 |
| --- | --- | --- |
| 40012 | 分拣中心不存在 | 节点编号无效 |

---

## 十一、演示数据初始化说明

> **注意**：演示数据初始化通过**脚本**执行，不是API。
> 
> 执行命令：`cd src/backend && python scripts/init_demo_data.py`
> 
> 初始化内容：5存储中心、2分拣中心（L1）、50分拣中心（L2）、70车、70司机、50订单（每单2-7货物）。

---

## 十二、API 清单汇总

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| **认证** | | | |
| POST | `/api/auth/login` | 登录 | 公开 |
| GET | `/api/auth/me` | 当前用户 | 已认证 |
| POST | `/api/auth/logout` | 登出 | 已认证 |
| **订单** | | | |
| GET | `/api/orders` | 订单列表 | dispatcher+manager |
| POST | `/api/orders` | 新增订单 | dispatcher |
| GET | `/api/orders/{order_code}` | 订单详情 | 全部 |
| PUT | `/api/orders/{order_code}` | 编辑订单 | dispatcher |
| DELETE | `/api/orders/{order_code}` | 删除订单 | dispatcher |
| POST | `/api/orders/import` | 批量导入 | dispatcher |
| **货物** | | | |
| GET | `/api/goods` | 货物列表 | 全部 |
| GET | `/api/goods/{goods_code}` | 货物详情 | 全部 |
| PUT | `/api/goods/{goods_code}` | 编辑货物 | dispatcher |
| **包裹** | | | |
| GET | `/api/packages` | 包裹列表 | 全部 |
| GET | `/api/packages/{package_code}` | 包裹详情 | 全部 |
| POST | `/api/packages/{package_code}/repack` | 重新打包 | dispatcher |
| **车辆** | | | |
| GET | `/api/vehicles` | 车辆列表 | 全部 |
| POST | `/api/vehicles` | 新增车辆 | dispatcher |
| GET | `/api/vehicles/{vehicle_code}` | 车辆详情 | 全部 |
| PUT | `/api/vehicles/{vehicle_code}` | 编辑车辆 | dispatcher |
| DELETE | `/api/vehicles/{vehicle_code}` | 删除车辆 | dispatcher |
| **司机** | | | |
| GET | `/api/drivers` | 司机列表 | 全部 |
| POST | `/api/drivers` | 新增司机 | dispatcher |
| GET | `/api/drivers/{driver_code}` | 司机详情 | 全部 |
| PUT | `/api/drivers/{driver_code}` | 编辑司机 | dispatcher |
| DELETE | `/api/drivers/{driver_code}` | 删除司机 | dispatcher |
| **节点** | | | |
| GET | `/api/nodes` | 节点列表 | 全部 |
| GET | `/api/nodes/{node_code}` | 节点详情 | 全部 |
| **存储中心** | | | |
| POST | `/api/nodes/storage-centers` | 新增存储中心 | dispatcher |
| PUT | `/api/nodes/storage-centers/{node_code}` | 编辑存储中心 | dispatcher |
| DELETE | `/api/nodes/storage-centers/{node_code}` | 删除存储中心 | dispatcher |
| **分拣中心** | | | |
| POST | `/api/nodes/sorting-centers` | 新增分拣中心 | dispatcher |
| PUT | `/api/nodes/sorting-centers/{node_code}` | 编辑分拣中心 | dispatcher |
| DELETE | `/api/nodes/sorting-centers/{node_code}` | 删除分拣中心 | dispatcher |

---

**文档结束**
