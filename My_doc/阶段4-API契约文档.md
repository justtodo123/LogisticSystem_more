# 阶段4：节点间调度 F005 - API 契约文档

> **文档版本**：V1.0  
> **创建日期**：2026年6月14日  
> **开发阶段**：阶段4（节点间调度 F005）  
> **API 基础路径**：`http://localhost:8000/api`  
> **API 协议**：HTTP/JSON，UTF-8  
> **参考资料**：PRD V2.7、系统架构设计说明书 V1.0、阶段4开发文档 V1.0、阶段4实际实现代码

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
| 40001 | 200 | 节点调度失败 | F005 算法无法完成调度（无可用车辆、L0→L1未完成等） |
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

1. F005 节点调度算法：第一次调用（L0→L1），分配车辆与司机
2. 写入 dispatch_batches + node_dispatches（level_phase=0）
3. 第二次调用（L1→L2），分配车辆与司机
4. 写入 node_dispatches（level_phase=1）
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
  "demo_mode": false                // 可选，是否演示模式（跳过L1送达等待），默认 false
}
```

**请求体验证规则**：

| 字段 | 类型 | 必填 | 验证规则 |
|---|---|---|---|
| schedule_code | string | 是 | 全局调度方案编号，必须存在 |
| demo_mode | bool | 否 | 是否演示模式，默认 false |

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
| batch_code | string | 调度批次编号，格式：BATCH + YYYYMMDD + 3位序号 |
| status | string | 批次状态：pending / l0_l1_done / completed / failed |
| dispatches | array | 调度明细列表（L0→L1 + L1→L2） |
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
| 40001 | 节点调度失败：L0→L1未完成，不能执行L1→L2 | demo_mode=false 且 L0→L1 未完成 |
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
  "demo_mode": false
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
        "demo_mode": false,
        "l0_l1_dispatch_count": 5,
        "l1_l2_dispatch_count": 8,
        "created_at": "2026-06-14T10:30:00"
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

**响应字段说明**：

| 字段 | 类型 | 说明 |
|---|---|---|
| items | array | 调度批次列表 |
| items[].batch_code | string | 批次编号 |
| items[].schedule_code | string | 全局调度方案编号 |
| items[].status | string | 批次状态：pending / l0_l1_done / completed / failed |
| items[].demo_mode | bool | 是否演示模式 |
| items[].l0_l1_dispatch_count | int | L0→L1 调度明细数量 |
| items[].l1_l2_dispatch_count | int | L1→L2 调度明细数量 |
| items[].created_at | string | 创建时间（ISO 8601） |
| total | int | 总记录数 |
| page | int | 当前页码 |
| page_size | int | 每页数量 |

**cURL 示例**：

```bash
curl -X GET "http://localhost:8000/api/schedule/batches?page=1&page_size=20" \
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
        "demo_mode": false,
        "l0_l1_dispatch_count": 5,
        "l1_l2_dispatch_count": 8,
        "created_at": "2026-06-14T10:30:00"
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
  page?: number
  page_size?: number
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
  const res = await listDispatchBatches({ page: 1, page_size: 20 })
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
| 正常调度（demo_mode=true） | `{ "schedule_code": "GS20260614001", "demo_mode": true }` | 200, code=0, 返回 batch_code |
| 正常调度（demo_mode=false） | `{ "schedule_code": "GS20260614001", "demo_mode": false }` | 200, code=0, 返回 batch_code |
| 无可用车辆 | 车辆状态=delivering | 200, code=40001, message="没有可用的车辆" |
| L0→L1 未完成 | demo_mode=false 且 L0→L1 未完成 | 200, code=40001, message="L0→L1未完成" |
| 调度方案不存在 | `{ "schedule_code": "GS999" }` | 200, code=40401, message="调度方案不存在" |

### 6.2 调度批次列表测试

| 测试用例 | 请求 | 预期响应 |
|---|---|---|
| 获取列表 | `GET /api/schedule/batches?page=1` | 200, code=0, 返回 items 数组 |
| 按方案筛选 | `GET /api/schedule/batches?schedule_code=GS20260614001` | 200, code=0, 返回该方案的批次 |
| 按状态筛选 | `GET /api/schedule/batches?status=completed` | 200, code=0, 返回 completed 批次 |
| 分页 | `GET /api/schedule/batches?page=1&page_size=10` | 200, code=0, total=1, items.length=1 |

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

---

**文档结束**
