# 阶段3：全局调度 F007+F021 - API 契约文档

> **文档版本**：V1.0
> **创建日期**：2026年6月13日
> **开发阶段**：阶段3（全局调度 F007 + 打包 F021）
> **API 基础路径**：`http://localhost:8000/api`
> **API 协议**：HTTP/JSON，UTF-8
> **参考资料**：PRD V2.7、系统架构设计说明书 V1.0、阶段3开发文档 V1.0、阶段3实际实现代码

---

## 1. 文档说明

本文档定义阶段3（全局调度 F007 + 打包 F021）的 API 契约，包括：

- 调度管理接口（触发全局调度、历史方案列表、方案详情）
- 错误码定义
- 请求/响应示例（JSON）
- 前端对接指南

**前端开发者**：请基于此文档进行 Mock 数据开发和接口对接。

**后端开发者**：请确保实现的接口与此文档一致。

---

## 2. API 基本约定

### 2.1 基础信息

| 项 | 约定 |
| --- | --- |
| Base URL | `http://localhost:8000/api` |
| 协议 | HTTP/JSON，UTF-8 |
| 版本 | MVP 不加 `/v1` 前缀 |
| 时间格式 | ISO 8601，`2026-06-13T10:00:00` |
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
  "message": "全局调度失败：没有找到符合条件的订单（status=pending）",
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
      "order_codes": "订单编号列表格式错误"
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
| --- | --- | --- | --- |
| 0 | 200 | 成功 | 接口调用成功 |
| 40000 | 400 | 参数校验失败 | 请求体字段验证失败 |
| 40001 | 200 | 全局调度失败 | F007 算法无法完成调度（无 pending 订单、无满足条件的 L1 等） |
| 40401 | 200 | 调度方案不存在 | GET /api/schedule/global/{code} 方案编号无效 |
| 40100 | 401 | 未登录或 Token 无效 | Token 缺失、格式错误、签名验证失败 |
| 40101 | 401 | Token 已过期 | Token 的 exp 字段已过期 |
| 40300 | 403 | 无操作权限 | manager 角色调用 POST /api/schedule/global |
| 40400 | 404 | 资源不存在 | 请求的资源路径不存在 |
| 50000 | 500 | 服务器内部错误 | 数据库写入失败等未预期异常 |

> **说明**：所有接口（包括 401/403/404/500）均返回统一响应格式 `{code, message, data, meta}`。前端可通过 `response.data.code` 统一判断，无需分别处理 `detail` 字段。

---

## 3. 调度管理 API（F007 + F021）

### 3.1 API 清单

| 方法 | 路径 | 说明 | 认证要求 | 权限要求 |
| --- | --- | --- | --- | --- |
| POST | `/api/schedule/global` | 触发全局调度（F007+F021） | 需要认证 | dispatcher |
| GET | `/api/schedule/global` | 历史调度方案列表 | 需要认证 | dispatcher + manager |
| GET | `/api/schedule/global/{schedule_code}` | 调度方案详情 | 需要认证 | dispatcher + manager |

---

### 3.2 POST /api/schedule/global

**功能**：触发全局调度（F007 全局调度算法 + F021 打包算法）。

**流程**：

1. F007 全局调度算法：为每票货物规划 L0 → L1 → L2 路径
2. F021 打包算法：生成 L0→L1 和 L1→L2 包裹
3. 单事务写入数据库并更新订单/货物状态

**请求**：

- **URL**：`/api/schedule/global`
- **方法**：`POST`
- **Content-Type**：`application/json`
- **认证**：`Authorization: Bearer {access_token}`（dispatcher 角色）
- **请求体**：

```json
{
  "order_codes": ["O001", "O002"],  // 可选，不传则处理所有 status=pending 的订单
  "algorithm": "traditional"         // 算法类型，traditional/deepseek（阶段3仅支持 traditional）
}
```

**请求体验证规则**：

| 字段 | 类型 | 必填 | 验证规则 |
| --- | --- | --- | --- |
| order_codes | List[str] | 否 | 订单编号列表，不传则处理所有 pending 订单 |
| algorithm | string | 否 | 算法类型：traditional / deepseek，默认 traditional |

**响应成功（HTTP 200）**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "schedule_code": "GS20260613001",
    "total_distance": 3044.67,
    "total_time": 471.67,
    "total_goods": 203,
    "score": 1523.45,
    "package_count": 53,
    "version": 1,
    "is_replan": false
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**响应字段说明**：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| schedule_code | string | 调度方案编号，格式：GS + YYYYMMDD + 3位序号 |
| total_distance | float | 总距离（公里） |
| total_time | float | 总时间（小时） |
| total_goods | int | 货物数量 |
| score | float | 调度方案评分（越小越好） |
| package_count | int | 包裹数量（L0→L1 + L1→L2） |
| version | int | 版本号，首次为 1 |
| is_replan | bool | 是否重规划 |

**响应失败（HTTP 200，业务错误）**：

| code | message | 说明 |
| --- | --- | --- |
| 40001 | 全局调度失败：没有找到符合条件的订单（status=pending） | 无 pending 订单 |
| 40001 | 全局调度失败：没有找到 1 级分拣中心（L1），请先初始化演示数据 | 无 L1 节点 |
| 40001 | 全局调度失败：无法为货物 GO001_1（订单 O001）找到满足所有硬约束的 L1 分拣中心 | 硬约束不满足 |

**cURL 示例**：

```bash
curl -X POST "http://localhost:8000/api/schedule/global" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -d '{
    "order_codes": null,
    "algorithm": "traditional"
  }'
```

**Swagger 示例**：

```yaml
# Swagger UI 中的示例请求
{
  "order_codes": ["O001", "O002"],
  "algorithm": "traditional"
}

# Swagger UI 中的示例响应（200）
{
  "code": 0,
  "message": "success",
  "data": {
    "schedule_code": "GS20260613001",
    "total_distance": 3044.67,
    "total_time": 471.67,
    "total_goods": 203,
    "score": 1523.45,
    "package_count": 53,
    "version": 1,
    "is_replan": false
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

---

### 3.3 GET /api/schedule/global

**功能**：获取历史全局调度方案列表。

**请求**：

- **URL**：`/api/schedule/global`
- **方法**：`GET`
- **请求头**：`Authorization: Bearer {access_token}`（dispatcher 或 manager 角色）
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页数量，默认 20，最大 100 |
| order_code | string | 否 | 按订单编号筛选 |

**响应成功（HTTP 200）**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "schedule_code": "GS20260613001",
        "total_distance": 3044.67,
        "total_time": 471.67,
        "total_goods": 203,
        "score": 1523.45,
        "package_count": 53,
        "version": 1,
        "is_replan": false,
        "created_at": "2026-06-13T10:30:00"
      }
    ],
    "total": 2,
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
| --- | --- | --- |
| items | array | 调度方案列表 |
| items[].schedule_code | string | 调度方案编号 |
| items[].total_distance | float | 总距离（公里） |
| items[].total_time | float | 总时间（小时） |
| items[].total_goods | int | 货物数量 |
| items[].score | float | 调度方案评分 |
| items[].package_count | int | 包裹数量 |
| items[].version | int | 版本号 |
| items[].is_replan | bool | 是否重规划 |
| items[].created_at | string | 创建时间（ISO 8601） |
| total | int | 总记录数 |
| page | int | 当前页码 |
| page_size | int | 每页数量 |

**cURL 示例**：

```bash
curl -X GET "http://localhost:8000/api/schedule/global?page=1&page_size=20" \
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
        "schedule_code": "GS20260613001",
        "total_distance": 3044.67,
        "total_time": 471.67,
        "total_goods": 203,
        "score": 1523.45,
        "package_count": 53,
        "version": 1,
        "is_replan": false,
        "created_at": "2026-06-13T10:30:00"
      }
    ],
    "total": 2,
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

### 3.4 GET /api/schedule/global/{schedule_code}

**功能**：获取全局调度方案详情（含 goods_schedules 和 packages）。

**请求**：

- **URL**：`/api/schedule/global/{schedule_code}`
- **方法**：`GET`
- **请求头**：`Authorization: Bearer {access_token}`（dispatcher 或 manager 角色）
- **路径参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| schedule_code | string | 是 | 调度方案编号 |

**响应成功（HTTP 200）**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "schedule_code": "GS20260613001",
    "total_distance": 3044.67,
    "total_time": 471.67,
    "total_goods": 203,
    "score": 1523.45,
    "package_count": 53,
    "version": 1,
    "is_replan": false,
    "goods_schedules": [
      {
        "goods_code": "GO001_1",
        "order_code": "O001",
        "path": ["SC001", "L1001", "L2027"]
      }
    ],
    "packages": [
      {
        "package_code": "PKG202606130001",
        "weight": 25.5,
        "volume": 0.8,
        "status": "packed",
        "from_node_code": "SC001",
        "to_node_code": "L1001",
        "goods_items": [
          {
            "goods_code": "GO001_1",
            "order_code": "O001"
          }
        ]
      }
    ],
    "created_at": "2026-06-13T10:30:00"
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**响应字段说明**：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| schedule_code | string | 调度方案编号 |
| total_distance | float | 总距离（公里） |
| total_time | float | 总时间（小时） |
| total_goods | int | 货物数量 |
| score | float | 调度方案评分 |
| package_count | int | 包裹数量 |
| version | int | 版本号 |
| is_replan | bool | 是否重规划 |
| goods_schedules | array | 货物调度计划列表 |
| goods_schedules[].goods_code | string | 货物编号 |
| goods_schedules[].order_code | string | 订单编号 |
| goods_schedules[].path | array | 路径：[L0_code, L1_code, L2_code] |
| packages | array | 包裹列表 |
| packages[].package_code | string | 包裹编号 |
| packages[].weight | float | 包裹重量（kg） |
| packages[].volume | float | 包裹体积（m³） |
| packages[].status | string | 包裹状态：pending_pack / packed |
| packages[].from_node_code | string | 发送地节点编号 |
| packages[].to_node_code | string | 接收地节点编号 |
| packages[].goods_items | array | 包裹内货物列表 |
| packages[].goods_items[].goods_code | string | 货物编号 |
| packages[].goods_items[].order_code | string | 订单编号 |
| created_at | string | 创建时间（ISO 8601） |

**响应失败（HTTP 200，业务错误）**：

| code | message | 说明 |
| --- | --- | --- |
| 40401 | 调度方案不存在：GS20260613999 | 方案编号无效 |

**cURL 示例**：

```bash
curl -X GET "http://localhost:8000/api/schedule/global/GS20260613001" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**Swagger 示例**：

```yaml
# Swagger UI 中的示例响应（200）
{
  "code": 0,
  "message": "success",
  "data": {
    "schedule_code": "GS20260613001",
    "total_distance": 3044.67,
    "total_time": 471.67,
    "total_goods": 203,
    "score": 1523.45,
    "package_count": 53,
    "version": 1,
    "is_replan": false,
    "goods_schedules": [
      {
        "goods_code": "GO001_1",
        "order_code": "O001",
        "path": ["SC001", "L1001", "L2027"]
      }
    ],
    "packages": [
      {
        "package_code": "PKG202606130001",
        "weight": 25.5,
        "volume": 0.8,
        "status": "packed",
        "from_node_code": "SC001",
        "to_node_code": "L1001",
        "goods_items": [
          {
            "goods_code": "GO001_1",
            "order_code": "O001"
          }
        ]
      }
    ],
    "created_at": "2026-06-13T10:30:00"
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

---

## 4. 前端对接指南

### 4.1 调度触发流程

```
1. 用户访问调度工作台页
2. 用户点击"开始调度"按钮
3. 前端调用 POST /api/schedule/global
4. 后端返回 schedule_code
5. 前端跳转至调度方案详情页
```

### 4.2 请求拦截器

前端需配置 Axios 请求拦截器，自动在请求头中附加 Token（同阶段1/2）：

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

### 4.3 调度接口调用示例

```typescript
// src/api/schedule.ts

import request from './request'

export interface GlobalScheduleRequest {
  order_codes?: string[]
  algorithm?: string
}

export interface GlobalScheduleResponse {
  schedule_code: string
  total_distance: number
  total_time: number
  total_goods: number
  score: number
  package_count: number
  version: number
  is_replan: boolean
}

export async function createGlobalSchedule(data: GlobalScheduleRequest) {
  return request.post('/schedule/global', data)
}

export async function listGlobalSchedules(params: {
  page?: number
  page_size?: number
  order_code?: string
}) {
  return request.get('/schedule/global', { params })
}

export async function getGlobalSchedule(schedule_code: string) {
  return request.get(`/schedule/global/${schedule_code}`)
}
```

### 4.4 调度工作台页面示例

```vue
<!-- src/views/ScheduleView.vue -->

<template>
  <div>
    <el-button type="primary" @click="handleSchedule" :loading="loading">
      开始调度
    </el-button>

    <el-table :data="schedules">
      <el-table-column prop="schedule_code" label="调度编号" />
      <el-table-column prop="total_distance" label="总距离(km)" />
      <el-table-column prop="total_time" label="总时间(h)" />
      <el-table-column prop="total_goods" label="货物数" />
      <el-table-column prop="package_count" label="包裹数" />
      <el-table-column prop="created_at" label="创建时间" />
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { listGlobalSchedules } from '@/api/schedule'

const schedules = ref([])
const loading = ref(false)

const loadSchedules = async () => {
  const res = await listGlobalSchedules({ page: 1, page_size: 20 })
  schedules.value = res.data.items
}

const handleSchedule = async () => {
  loading.value = true
  try {
    const res = await createGlobalSchedule({ order_codes: null, algorithm: 'traditional' })
    ElMessage.success(`调度成功：${res.data.schedule_code}`)
    loadSchedules()
  } catch (error: any) {
    ElMessage.error(error.message || '调度失败')
  } finally {
    loading.value = false
  }
}

loadSchedules()
</script>
```

---

## 5. 后端实现检查清单

### 5.1 FastAPI 路由实现

- [ ] `POST /api/schedule/global` 接口已实现
- [ ] `GET /api/schedule/global` 接口已实现
- [ ] `GET /api/schedule/global/{schedule_code}` 接口已实现
- [ ] 所有接口返回统一响应格式 `{ code, message, data, meta }`
- [ ] POST 接口对业务错误返回 code=40001
- [ ] GET 接口对方案不存在返回 code=40401

### 5.2 认证与权限

- [ ] `POST /api/schedule/global` 需要 dispatcher 角色（require_dispatcher）
- [ ] `GET /api/schedule/global` 需要认证（get_current_user）
- [ ] `GET /api/schedule/global/{schedule_code}` 需要认证（get_current_user）
- [ ] manager 角色调用 POST 接口时返回 HTTP 403 + code=40300

### 5.3 调度编排服务

- [ ] `ScheduleService.create_global_schedule` 已实现
- [ ] F007 算法调用正确（global_schedule.py）
- [ ] F021 算法调用正确（packaging.py）
- [ ] 单事务写入：global_schedules + packages + 更新 orders/goods 状态
- [ ] 事务回滚：F007/F021 异常时全局回滚

### 5.4 算法实现

- [ ] F007 全局调度算法已实现（global_schedule.py）
- [ ] F021 打包算法已实现（packaging.py）
- [ ] F007 硬约束检查：L1 容量、同订单汇聚、最大存储时长
- [ ] F007 评分公式：score = w1×distance + w2×time + w3×packages

### 5.5 Swagger 文档

- [ ] Swagger 文档可通过 http://localhost:8000/docs 访问
- [ ] 调度接口有示例请求/响应
- [ ] 受保护接口需在 Swagger 中授权后调用

---

## 6. 测试用例

### 6.1 触发全局调度测试

| 测试用例 | 请求 | 预期响应 |
| --- | --- | --- |
| 正常调度（无 pending 订单） | `{ "order_codes": null, "algorithm": "traditional" }` | 200, code=0, 返回 schedule_code |
| 指定订单调度 | `{ "order_codes": ["O001"], "algorithm": "traditional" }` | 200, code=0, 返回 schedule_code |
| 无 pending 订单 | 所有订单已调度 | 200, code=40001, message="没有找到符合条件的订单" |
| 无 L1 节点 | 数据库无 L1 节点 | 200, code=40001, message="没有找到 1 级分拣中心" |
| 算法类型错误 | `{ "algorithm": "deepseek" }` | 200, code=40001, message="阶段3仅支持 traditional 算法" |

### 6.2 历史方案列表测试

| 测试用例 | 请求 | 预期响应 |
| --- | --- | --- |
| 获取列表 | `GET /api/schedule/global?page=1` | 200, code=0, 返回 items 数组 |
| 按订单筛选 | `GET /api/schedule/global?order_code=O001` | 200, code=0, 返回包含 O001 的方案 |
| 分页 | `GET /api/schedule/global?page=1&page_size=10` | 200, code=0, total=2, items.length=2 |

### 6.3 方案详情测试

| 测试用例 | 请求 | 预期响应 |
| --- | --- | --- |
| 正常获取 | `GET /api/schedule/global/GS20260613001` | 200, code=0, 返回方案详情 |
| 方案不存在 | `GET /api/schedule/global/GS999` | 200, code=40401, message="调度方案不存在" |

### 6.4 权限测试

| 测试用例 | 用户角色 | 接口 | 预期响应 |
| --- | --- | --- | --- |
| dispatcher 调用调度 | dispatcher | POST /api/schedule/global | 200, code=0 |
| manager 调用调度 | manager | POST /api/schedule/global | 403, code=40300 |
| manager 查看列表 | manager | GET /api/schedule/global | 200, code=0 |

---

## 7. 变更历史

| 版本 | 日期 | 修改内容 | 作者 |
| --- | --- | --- | --- |
| V1.0 | 2026-06-13 | 初版：阶段3 全局调度 F007+F021 API 契约文档 | AI 开发助手 |

---

**文档结束**
