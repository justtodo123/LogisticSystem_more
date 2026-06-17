# 阶段6（模拟送达 F013-1）API 契约文档

**版本**：v1.0  
**创建日期**：2026-06-17  
**最后更新**：2026-06-17  
**作者**：CodeBuddy AI  
**对应阶段**：阶段6（模拟送达 F013-1）  
**实现状态**：✅ 已完成

---

## 1. 文档概述

### 1.1 文档目的

本文档定义阶段6（模拟送达 F013-1）的API契约，包括接口路径、请求/响应格式、认证要求、错误处理等。本文档作为前后端联调的依据，前端可基于本文档进行Mock数据开发。

### 1.2 API基础信息

- **Base URL**：`http://localhost:8000/api`
- **认证方式**：Bearer Token (JWT)
- **响应格式**：统一JSON格式 `{ code, message, data, meta? }`
- **API文档**：`http://localhost:8000/docs`（FastAPI自动生成）

### 1.3 功能范围

阶段6包含以下API：

| API路径 | 方法 | 说明 | 优先级 | 状态 |
|---------|------|------|--------|------|
| `/api/simulation/deliver` | POST | 模拟送达，驱动状态流转（支持自动重新调度） | P0 | ✅ 已实现 |
| `/api/simulation/status/{batch_code}` | GET | 查询送达状态和待重新打包货物 | P1 | ⏳ 待实现 |
| `/api/simulation/deliver-batch` | POST | 批量送达同一批次所有车辆 | P1 | ⏳ 待实现 |

---

## 2. API详细设计

### 2.1 POST /api/simulation/deliver

#### 2.1.1 功能说明

模拟包裹送达操作，驱动状态流转。支持单个/批量送达，并在第一次送达完成后自动触发L1重新打包和第二次F005（L1→L2调度），以及自动重新调度未分配包裹。

**自动触发逻辑**：
- 第一次送达（L0→L1）完成后，系统自动检测 `pending_pack` 状态的货物
- 自动执行F021重新打包（生成L1→L2新包裹）
- 自动触发第二次F005（L1→L2调度，异步执行）
- 自动检测未分配的包裹，如果有空闲车辆，自动重新调度（支持递归重新调度）

#### 2.1.2 认证要求

- **认证方式**：Bearer Token
- **角色要求**：`dispatcher`（调度员）
- **请求头**：
  ```
  Authorization: Bearer <token>
  Content-Type: application/json
  ```

#### 2.1.3 请求参数

**请求体**：
```json
{
  "vehicle_code": "string | null",
  "package_code": "string | null"
}
```

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `vehicle_code` | string | 否 | 车辆编号。如果提供，处理该车辆所有 `in_transit` 包裹 |
| `package_code` | string | 否 | 包裹编号。如果提供，处理指定包裹（必须 `in_transit` 状态） |

**参数组合逻辑**：

| vehicle_code | package_code | 行为 |
|--------------|--------------|------|
| 无 | 无 | 处理所有 `in_transit` 包裹 |
| 有 | 无 | 处理该车辆所有 `in_transit` 包裹 |
| 无 | 有 | 处理指定包裹（必须 `in_transit` 状态） |
| 有 | 有 | 处理指定车辆的指定包裹（必须 `in_transit` 状态） |

#### 2.1.4 响应数据

**成功响应**（HTTP 200）：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "delivered_package_codes": ["PKG001", "PKG002"],
    "status_changed_goods_count": 5,
    "updated_order_count": 1,
    "delivered_order_codes": ["O001"],
    "auto_triggered": {
      "repackaging": true,
      "second_f005": true
    }
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**响应字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `delivered_package_codes` | string[] | 送达包裹编号列表 |
| `status_changed_goods_count` | integer | 状态变更的货物数量 |
| `updated_order_count` | integer | 更新的订单数量 |
| `delivered_order_codes` | string[] | 已送达订单编号列表 |
| `auto_triggered` | object | 自动触发的操作 |
| `auto_triggered.repackaging` | boolean | 是否自动触发了重新打包 |
| `auto_triggered.second_f005` | boolean | 是否自动触发了第二次F005 |
| `auto_triggered.redispatch` | boolean | 是否自动重新调度了未分配包裹 |
| `level_info` | object | 层级信息（L0→L1 和 L1→L2 的送达数量） |

**业务失败响应**（HTTP 200，code≠0）：

1. **没有找到可送达的包裹**（code=40001）：
```json
{
  "code": 40001,
  "message": "没有找到可送达的包裹",
  "data": null,
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

2. **包裹状态不是in_transit**（code=40001）：
```json
{
  "code": 40001,
  "message": "包裹 PKG003 状态不是 in_transit，无法送达",
  "data": null,
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**参数错误响应**（HTTP 400，code=40000）：
```json
{
  "code": 40000,
  "message": "参数校验失败",
  "data": {
    "fields": {
      "package_code": "包裹不存在"
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
{ "code": 40100, "message": "未登录或 Token 无效", "data": null, "meta": { "degraded": false } }

// 无权限
{ "code": 40300, "message": "无操作权限", "data": null, "meta": { "degraded": false } }
```

#### 2.1.5 状态流转规则

**第一次送达（L0→L1）**：

| 实体 | 原状态 | 条件 | 新状态 |
|------|--------|------|--------|
| 包裹 | `in_transit` | 送达 | `delivered` |
| 货物 | `in_transit` | `goods.node_id == order.destination_node_id` | `delivered` |
| 货物 | `in_transit` | `goods.node_id != order.destination_node_id` | `pending_pack` |
| 车辆 | `delivering` | 车辆上所有包裹都送达 | `idle` |
| 司机 | `busy` | 车辆状态变为 `idle` | `idle` |
| 订单 | `delivering` | 订单所有货物都 `delivered` | `completed` |
| 批次 | `pending` | 第一次送达完成 | `l0_l1_done` |

**自动重新打包（F021）**：

| 实体 | 原状态 | 条件 | 新状态 |
|------|--------|------|--------|
| 货物 | `pending_pack` | 重新打包完成 | `packed` |
| 包裹 | - | 生成新包裹（L1→L2） | `packed` |

**第二次送达（L1→L2）**：

| 实体 | 原状态 | 条件 | 新状态 |
|------|--------|------|--------|
| 包裹 | `in_transit` | 送达 | `delivered` |
| 货物 | `in_transit` | `goods.node_id == order.destination_node_id` | `delivered` |
| 车辆 | `delivering` | 车辆上所有包裹都送达 | `idle` |
| 司机 | `busy` | 车辆状态变为 `idle` | `idle` |
| 订单 | `delivering` | 订单所有货物都 `delivered` | `completed` |
| 批次 | `l0_l1_done` | 第二次送达完成 | `completed` |

#### 2.1.6 请求示例

**示例1：无参数调用，处理所有in_transit包裹**
```bash
curl -X POST "http://localhost:8000/api/simulation/deliver" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**示例2：按车辆送达**
```bash
curl -X POST "http://localhost:8000/api/simulation/deliver" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_code": "V001"
  }'
```

**示例3：按包裹送达**
```bash
curl -X POST "http://localhost:8000/api/simulation/deliver" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "package_code": "PKG001"
  }'
```

#### 2.1.7 响应示例

**成功响应示例**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "delivered_package_codes": ["PKG001", "PKG002", "PKG003"],
    "status_changed_goods_count": 15,
    "updated_order_count": 2,
    "delivered_order_codes": ["O001", "O002"],
    "auto_triggered": {
      "repackaging": true,
      "second_f005": true
    }
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**业务失败响应示例**：
```json
{
  "code": 40001,
  "message": "包裹 PKG003 状态不是 in_transit，无法送达",
  "data": null,
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

---

### 2.2 GET /api/simulation/status/{batch_code}（P1）

#### 2.2.1 功能说明

查询送达状态和待重新打包货物。用于 `demo_mode=false` 模式下，用户轮询查看第一次送达后的重新打包和第二次F005执行状态。

**实现状态**：⏳ P1功能，待实现

#### 2.2.2 认证要求

- **认证方式**：Bearer Token
- **角色要求**：`dispatcher` / `manager`

#### 2.2.3 请求参数

**路径参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `batch_code` | string | 是 | 批次编码 |

#### 2.2.4 响应数据

**成功响应**（HTTP 200）：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "batch_code": "BATCH001",
    "batch_status": "l0_l1_done",
    "first_delivery": {
      "status": "completed",
      "delivered_packages": ["PKG001", "PKG002"],
      "pending_pack_goods": ["G003", "G004"]
    },
    "repackaging": {
      "status": "completed",
      "new_packages": ["PKG005", "PKG006"]
    },
    "second_f005": {
      "status": "in_progress",
      "message": "第二次调度正在执行中，请稍后查询"
    }
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**响应字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `batch_code` | string | 批次编码 |
| `batch_status` | string | 批次状态：`pending` / `l0_l1_done` / `completed` / `failed` |
| `first_delivery.status` | string | 第一次送达状态：`pending` / `in_progress` / `completed` / `failed` |
| `first_delivery.delivered_packages` | string[] | 已送达包裹编号列表 |
| `first_delivery.pending_pack_goods` | string[] | 待重新打包货物编号列表 |
| `repackaging.status` | string | 重新打包状态：`pending` / `in_progress` / `completed` / `failed` |
| `repackaging.new_packages` | string[] | 新生成的包裹编号列表 |
| `second_f005.status` | string | 第二次F005状态：`pending` / `in_progress` / `completed` / `failed` |
| `second_f005.message` | string | 第二次F005执行信息 |

#### 2.2.5 请求示例

```bash
curl -X GET "http://localhost:8000/api/simulation/status/BATCH001" \
  -H "Authorization: Bearer <token>"
```

---

### 2.3 POST /api/simulation/deliver-batch（P1）

#### 2.3.1 功能说明

批量送达同一批次所有车辆。用于快速完成整个批次的送达操作。

**实现状态**：⏳ P1功能，待实现

#### 2.3.2 认证要求

- **认证方式**：Bearer Token
- **角色要求**：`dispatcher`

#### 2.3.3 请求参数

**请求体**：
```json
{
  "batch_code": "BATCH001"
}
```

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `batch_code` | string | 是 | 批次编码 |

#### 2.3.4 响应数据

**成功响应**（HTTP 200）：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "batch_code": "BATCH001",
    "delivered_vehicle_count": 3,
    "delivered_package_count": 15,
    "status_changed_goods_count": 20,
    "updated_order_count": 2,
    "delivered_order_codes": ["O001", "O002"]
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

#### 2.3.5 请求示例

```bash
curl -X POST "http://localhost:8000/api/simulation/deliver-batch" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "batch_code": "BATCH001"
  }'
```

---

## 3. 数据模型

### 3.1 DeliverRequest

```json
{
  "vehicle_code": "string | null",
  "package_code": "string | null"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `vehicle_code` | string | 否 | 车辆编号 |
| `package_code` | string | 否 | 包裹编号 |

### 3.2 DeliverResponse

```json
{
  "delivered_package_codes": ["PKG001"],
  "status_changed_goods_count": 0,
  "updated_order_count": 0,
  "delivered_order_codes": ["O001"],
  "auto_triggered": {
    "repackaging": false,
    "second_f005": false
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `delivered_package_codes` | string[] | 送达包裹编号列表 |
| `status_changed_goods_count` | integer | 状态变更的货物数量 |
| `updated_order_count` | integer | 更新的订单数量 |
| `delivered_order_codes` | string[] | 已送达订单编号列表 |
| `auto_triggered` | object | 自动触发的操作 |
| `auto_triggered.repackaging` | boolean | 是否自动触发了重新打包 |
| `auto_triggered.second_f005` | boolean | 是否自动触发了第二次F005 |

---

## 4. 错误处理

### 4.1 错误码定义

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| 0 | 200 | 成功 |
| 40000 | 400 | 参数校验失败 |
| 40001 | 200 | 业务错误（如没有可送达的包裹、包裹状态错误等） |
| 40100 | 401 | 未登录或Token无效 |
| 40101 | 401 | Token已过期 |
| 40300 | 403 | 无操作权限 |
| 40400 | 404 | 资源不存在（车辆/包裹/批次不存在） |
| 50000 | 500 | 服务器内部错误 |

### 4.2 错误响应格式

```json
{
  "code": 40001,
  "message": "错误描述信息",
  "data": null,
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**参数错误时的data格式**：
```json
{
  "code": 40000,
  "message": "参数校验失败",
  "data": {
    "fields": {
      "package_code": "包裹不存在"
    }
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

---

## 5. 认证与授权

### 5.1 认证方式

所有API请求必须在请求头中携带JWT Token：

```
Authorization: Bearer <token>
```

**获取Token**：`POST /api/auth/login`

```json
{
  "username": "dispatcher",
  "password": "123456"
}
```

**Token过期时间**：24小时

### 5.2 角色权限

| 角色 | 阶段6API权限 |
|------|-------------|
| `dispatcher` | 全部权限（GET/POST） |
| `manager` | 仅查询权限（GET） |

**前端权限控制**：
- manager角色需 `v-if="role==='dispatcher'"` 隐藏所有写操作按钮
- 后端RBAC Guard会进行二次校验，防止越权操作

---

## 6. 测试建议

### 6.1 单元测试

- 测试文件：`tests/unit/services/test_simulation_service.py`
- 测试覆盖：✅ 56个测试全部通过（2026-06-17）

### 6.2 集成测试

**测试场景1：无参数调用**
1. 调用 `POST /api/simulation/deliver` 不传任何参数
2. 验证所有 `in_transit` 包裹状态变为 `delivered`
3. 验证货物状态流转正确
4. 验证车辆/司机/订单状态流转正确

**测试场景2：demo_mode=false完整流程**
1. 执行 `POST /api/schedule/global`（F007 + F021）
2. 执行 `POST /api/schedule/node-dispatch (demo_mode=false)`（L0→L1调度）
3. 调用 `POST /api/simulation/deliver` 送达L0→L1包裹
4. 验证系统自动执行F021重新打包
5. 验证系统自动触发第二次F005（异步）
6. 轮询 `GET /api/schedule/batches/{batch_code}` 查看批次状态
7. 验证批次状态最终变为 `completed`

**测试场景3：异常边界情况**
1. 包裹状态不是 `in_transit`，返回错误（code=40001）
2. 车辆不存在，返回404（code=40400）
3. 包裹不存在，返回404（code=40400）

---

## 7. 附录

### 7.1 相关文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 阶段6开发文档 | `My_doc/阶段6-模拟送达-开发文档.md` | 详细设计文档 |
| 项目宪章 | `.codebuddy/CODEBUDDY.md` | 项目整体规范 |
| MVP开发计划-后端 | `docs/MVP开发计划-后端.md` | 后端分阶段任务 |

### 7.2 联系方式

- **技术支持**：CodeBuddy AI
- **问题反馈**：通过Git Issues反馈

---

**文档结束**
