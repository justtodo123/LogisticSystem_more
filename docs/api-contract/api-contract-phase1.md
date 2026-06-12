# 阶段 1：认证与权限 - API 契约文档

**文档版本**：V1.0  
**创建日期**：2026-06-12  
**开发阶段**：阶段 1（认证与权限）  
**API 基础路径**：`http://localhost:8000/api`  
**API 协议**：HTTP/JSON，UTF-8  

---

## 1. 文档说明

本文档定义阶段 1（认证与权限）的 API 契约，包括：
- 认证接口（登录/登出/获取当前用户信息）
- 错误码定义
- 请求/响应示例（JSON）
- Swagger 文档示例

**前端开发者**：请基于此文档进行 Mock 数据开发和接口对接。

**后端开发者**：请确保实现的接口与此文档一致。

---

## 2. 认证方式

### 2.1 登录

用户通过 `POST /api/auth/login` 接口登录，获取 `access_token`。

**请求头**：
```
Content-Type: application/json
```

**请求体**：
```json
{
  "username": "dispatcher",
  "password": "123456"
}
```

**响应成功（HTTP 200）**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkaXNwYXRjaGVyIiwicm9sZSI6ImRpc3BhdGNoZXIiLCJleHAiOjE3MTgyMDgwMDB9.8Z8Z8Z8Z8Z8Z8Z8Z8Z8Z8Z8Z8Z8Z8Z8Z8Z8Z8Z8",
    "token_type": "bearer",
    "expires_in": 86400,
    "role": "dispatcher",
    "display_name": "调度员"
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**响应失败（HTTP 200，密码错误）**：
```json
{
  "code": 40100,
  "message": "用户名或密码错误",
  "data": null,
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

### 2.2 后续请求认证

登录成功后，前端需在后续请求的 `Authorization` 头中携带 `access_token`：

```
Authorization: Bearer {access_token}
```

**示例**：
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 3. API 接口清单

### 3.1 认证接口

| 方法 | 路径 | 说明 | 认证要求 | 权限要求 |
| --- | --- | --- | --- | --- |
| POST | `/api/auth/login` | 登录获取 JWT | 无需认证 | 公开 |
| GET | `/api/auth/me` | 当前用户信息 | 需要认证 | 已认证用户 |
| POST | `/api/auth/logout` | 登出（前端清 Token） | 需要认证 | 已认证用户 |

---

## 4. API 详细定义

### 4.1 POST /api/auth/login

**功能**：用户登录，获取 JWT Token。

**请求**：

- **URL**：`/api/auth/login`
- **方法**：`POST`
- **Content-Type**：`application/json`
- **请求体**：

```json
{
  "username": "string",  // 必填，用户名
  "password": "string"   // 必填，密码（明文）
}
```

**请求体验证规则**：

| 字段 | 类型 | 必填 | 验证规则 |
| --- | --- | --- | --- |
| username | string | 是 | 非空，长度 3-64 |
| password | string | 是 | 非空，长度 6-128 |

**响应成功（HTTP 200）**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "string",      // JWT Token 字符串
    "token_type": "bearer",       // Token 类型（固定为 "bearer"）
    "expires_in": 86400,          // Token 有效期（秒），固定为 86400（24 小时）
    "role": "dispatcher",         // 用户角色（dispatcher / manager）
    "display_name": "调度员"      // 用户显示名称
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**响应失败（HTTP 200，业务错误）**：

| code | message | 说明 |
| --- | --- | --- |
| 40100 | 用户名或密码错误 | 用户名不存在或密码错误 |
| 40100 | 账号未激活，请联系管理员 | 用户 is_active=False |

**cURL 示例**：

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "dispatcher",
    "password": "123456"
  }'
```

**Swagger 示例**：

```yaml
# Swagger UI 中的示例请求
{
  "username": "dispatcher",
  "password": "123456"
}

# Swagger UI 中的示例响应（200）
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 86400,
    "role": "dispatcher",
    "display_name": "调度员"
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

---

### 4.2 GET /api/auth/me

**功能**：获取当前登录用户的信息。

**请求**：

- **URL**：`/api/auth/me`
- **方法**：`GET`
- **请求头**：

```
Authorization: Bearer {access_token}
```

**响应成功（HTTP 200）**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "username": "dispatcher",       // 用户名
    "role": "dispatcher",           // 角色（dispatcher / manager）
    "display_name": "调度员",       // 显示名称
    "is_active": true               // 是否激活
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**响应失败（HTTP 401，Token 无效）**：

```json
{
  "code": 40100,
  "message": "未登录或 Token 无效",
  "data": null,
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**响应失败（HTTP 401，Token 过期）**：

```json
{
  "code": 40101,
  "message": "Token 已过期，请重新登录",
  "data": null,
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**cURL 示例**：

```bash
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Swagger 示例**：

```yaml
# Swagger UI 中的示例响应（200）
{
  "code": 0,
  "message": "success",
  "data": {
    "username": "dispatcher",
    "role": "dispatcher",
    "display_name": "调度员",
    "is_active": true
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

---

### 4.3 POST /api/auth/logout

**功能**：用户登出。后端记录埋点（log_events），前端负责清除 Token。

**请求**：

- **URL**：`/api/auth/logout`
- **方法**：`POST`
- **请求头**：

```
Authorization: Bearer {access_token}
```

- **请求体**：无（或空 JSON `{}`）

**响应成功（HTTP 200）**：

```json
{
  "code": 0,
  "message": "登出成功",
  "data": null,
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**响应失败（HTTP 401，Token 无效）**：

```json
{
  "code": 40100,
  "message": "未登录或 Token 无效",
  "data": null,
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**cURL 示例**：

```bash
curl -X POST "http://localhost:8000/api/auth/logout" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Swagger 示例**：

```yaml
# Swagger UI 中的示例响应（200）
{
  "code": 0,
  "message": "登出成功",
  "data": null,
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

---

## 5. 错误码定义

### 5.1 认证与授权错误码

| code | HTTP 状态码 | 说明 | 触发场景 |
| --- | --- | --- | --- |
| 0 | 200 | 成功 | 接口调用成功 |
| 40000 | 400 | 参数校验失败 | 请求体字段验证失败（如 username 为空） |
| 40100 | 401 | 未登录或 Token 无效 | Token 缺失、格式错误、签名验证失败 |
| 40101 | 401 | Token 已过期 | Token 的 exp 字段已过期 |
| 40300 | 403 | 无权限 | manager 角色调用 POST/PUT/DELETE 接口 |

### 5.2 错误响应格式

**参数错误（HTTP 400）**：

```json
{
  "code": 40000,
  "message": "参数校验失败",
  "data": {
    "fields": {
      "username": "必填",
      "password": "长度至少 6 个字符"
    }
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**认证失败（HTTP 401）**：

```json
{
  "code": 40100,
  "message": "未登录或 Token 无效",
  "data": null,
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**授权失败（HTTP 403）**：

```json
{
  "code": 40300,
  "message": "无权限执行此操作（仅调度员可操作）",
  "data": null,
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

---

## 6. JWT Token 规范

### 6.1 Token 结构

JWT Token 由三部分组成（Header.Payload.Signature）：

**Header**：
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**Payload**：
```json
{
  "sub": "dispatcher",      // 用户名（username）
  "role": "dispatcher",    // 角色（dispatcher / manager）
  "exp": 1718208000        // 过期时间戳（Unix timestamp）
}
```

**Signature**：
```
HMACSHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  JWT_SECRET
)
```

### 6.2 Token 示例

**完整 Token 示例**（解码前）：
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkaXNwYXRjaGVyIiwicm9sZSI6ImRpc3BhdGNoZXIiLCJleHAiOjE3MTgyMDgwMDB9.8Z8Z8Z8Z8Z8Z8Z8Z8Z8Z8Z8Z8Z8Z8Z8Z8Z8Z8Z8
```

**解码后 Payload**：
```json
{
  "sub": "dispatcher",
  "role": "dispatcher",
  "exp": 1718208000
}
```

### 6.3 Token 有效期

- **有效期**：86400 秒（24 小时）
- **过期后行为**：前端需引导用户重新登录
- **MVP 限制**：Token 无法主动失效（登出后仍有效直到过期），P1 可实现 Token 黑名单

---

## 7. 角色权限矩阵

### 7.1 角色定义

| 角色 | 用户名 | 密码 | 权限范围 |
| --- | --- | --- | --- |
| 调度员（dispatcher） | `dispatcher` | `123456` | 全部功能读写 |
| 物流管理者（manager） | `manager` | `123456` | 只读（GET），写操作返回 403 |

### 7.2 权限矩阵

| 接口 | 方法 | dispatcher | manager | 说明 |
| --- | --- | --- | --- | --- |
| `/api/auth/login` | POST | ✅ | ✅ | 公开接口 |
| `/api/auth/me` | GET | ✅ | ✅ | 需要认证 |
| `/api/auth/logout` | POST | ✅ | ✅ | 需要认证 |
| `/api/orders` | GET | ✅ | ✅ | 阶段 2 实现 |
| `/api/orders` | POST | ✅ | ❌ 403 | 阶段 2 实现 |
| `/api/orders/{code}` | PUT | ✅ | ❌ 403 | 阶段 2 实现 |
| `/api/orders/{code}` | DELETE | ✅ | ❌ 403 | 阶段 2 实现 |

**说明**：
- ✅：允许访问
- ❌ 403：返回 HTTP 403，code=40300
- 阶段 1 只需实现认证接口，权限控制逻辑需在阶段 2 及后续阶段应用

---

## 8. 前端对接指南

### 8.1 登录流程

```
1. 用户访问登录页
2. 用户输入用户名/密码，点击登录
3. 前端调用 POST /api/auth/login
4. 后端返回 access_token
5. 前端将 access_token 存储到 Pinia store（或 localStorage）
6. 前端跳转至首页/工作台
```

### 8.2 请求拦截器

前端需配置 Axios 请求拦截器，自动在请求头中附加 Token：

```typescript
// src/api/request.ts

import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const request = axios.create({
  baseURL: '/api',  // Vite 代理转发至 :8000
  timeout: 15000     // 15 秒超时
})

// 请求拦截器：附加 Token
request.interceptors.request.use((config) => {
  const authStore = useAuthStore()
  if (authStore.accessToken) {
    config.headers.Authorization = `Bearer ${authStore.accessToken}`
  }
  return config
})

// 响应拦截器：处理业务错误
request.interceptors.response.use(
  (response) => {
    const { code, message } = response.data
    if (code !== 0) {
      // 业务错误（如 40100、40300）
      if (code === 40100 || code === 40101) {
        // Token 无效/过期，跳转登录页
        const authStore = useAuthStore()
        authStore.logout()
        router.push('/login')
      }
      return Promise.reject(new Error(message))
    }
    return response.data  // 直接返回 data 层
  },
  (error) => {
    // HTTP 错误（如 500）
    return Promise.reject(error)
  }
)

export default request
```

### 8.3 登录页示例

```vue
<!-- src/views/LoginView.vue -->

<template>
  <el-form @submit.prevent="handleLogin">
    <el-form-item label="用户名">
      <el-input v-model="username" />
    </el-form-item>
    <el-form-item label="密码">
      <el-input v-model="password" type="password" />
    </el-form-item>
    <el-button type="primary" @click="handleLogin">登录</el-button>
  </el-form>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import request from '@/api/request'

const username = ref('')
const password = ref('')
const router = useRouter()
const authStore = useAuthStore()

const handleLogin = async () => {
  try {
    const res = await request.post('/auth/login', {
      username: username.value,
      password: password.value
    })
    // 存储 Token 和用户信息
    authStore.setToken(res.data.access_token)
    authStore.setUser(res.data)
    // 跳转首页
    router.push('/')
  } catch (error) {
    ElMessage.error(error.message || '登录失败')
  }
}
</script>
```

### 8.4 路由守卫示例

```typescript
// src/router/index.ts

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('@/views/LoginView.vue') },
    { path: '/', component: () => import('@/views/DashboardView.vue'), meta: { requiresAuth: true } }
  ]
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.accessToken) {
    next('/login')
  } else {
    next()
  }
})

export default router
```

---

## 9. 后端实现检查清单

### 9.1 FastAPI 路由实现

- [ ] `POST /api/auth/login` 接口已实现
- [ ] `GET /api/auth/me` 接口已实现
- [ ] `POST /api/auth/logout` 接口已实现
- [ ] 所有接口返回统一响应格式 `{ code, message, data, meta }`
- [ ] 登录接口对密码错误返回 code=40100
- [ ] 登录接口对账号未激活返回 code=40100

### 9.2 JWT 工具函数

- [ ] `create_access_token(username, role)` 函数已实现
- [ ] `decode_token(token)` 函数已实现
- [ ] JWT 签名算法为 HS256
- [ ] JWT 过期时间为 86400 秒
- [ ] JWT SECRET 从环境变量读取

### 9.3 认证依赖

- [ ] `get_current_user` 依赖已实现
- [ ] `require_dispatcher` 依赖已实现
- [ ] Token 无效时抛出 HTTP 401（code=40100）
- [ ] Token 过期时抛出 HTTP 401（code=40101）
- [ ] manager 角色调用写接口时抛出 HTTP 403（code=40300）

### 9.4 Swagger 文档

- [ ] Swagger 文档可通过 http://localhost:8000/docs 访问
- [ ] 登录接口有示例请求/响应
- [ ] 受保护接口需在 Swagger 中授权后调用
- [ ] Swagger 中可调试登录接口

---

## 10. 测试用例

### 10.1 登录接口测试

| 测试用例 | 请求 | 预期响应 |
| --- | --- | --- |
| 正确用户名密码 | `{ "username": "dispatcher", "password": "123456" }` | 200, code=0, 返回 access_token |
| 错误密码 | `{ "username": "dispatcher", "password": "wrong" }` | 200, code=40100 |
| 用户不存在 | `{ "username": "nonexist", "password": "123456" }` | 200, code=40100 |
| 账号未激活 | `{ "username": "inactive", "password": "123456" }` | 200, code=40100 |
| 缺少 username | `{ "password": "123456" }` | 400, code=40000 |
| 缺少 password | `{ "username": "dispatcher" }` | 400, code=40000 |

### 10.2 获取当前用户信息测试

| 测试用例 | 请求头 | 预期响应 |
| --- | --- | --- |
| 正确 Token | `Authorization: Bearer {valid_token}` | 200, code=0, 返回用户信息 |
| 无效 Token | `Authorization: Bearer invalid` | 401, code=40100 |
| 过期 Token | `Authorization: Bearer {expired_token}` | 401, code=40101 |
| 缺少 Token | 无 Authorization 头 | 401, code=40100 |

### 10.3 权限测试

| 测试用例 | 用户角色 | 接口 | 预期响应 |
| --- | --- | --- | --- |
| dispatcher 调用写接口 | dispatcher | POST /api/orders | 200, code=0 |
| manager 调用写接口 | manager | POST /api/orders | 403, code=40300 |
| manager 调用读接口 | manager | GET /api/orders | 200, code=0 |

---

## 11. 附录：Postman Collection

### 11.1 Postman Collection JSON

```json
{
  "info": {
    "name": "LogisticsSystem Phase 1 - Auth",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Login - Success",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/api/auth/login",
        "header": [
          { "key": "Content-Type", "value": "application/json" }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"username\": \"dispatcher\",\n  \"password\": \"123456\"\n}"
        }
      },
      "event": [
        {
          "listen": "test",
          "script": {
            "exec": [
              "var jsonData = pm.response.json();",
              "pm.collectionVariables.set('access_token', jsonData.data.access_token);"
            ]
          }
        }
      ]
    },
    {
      "name": "Get Current User",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/api/auth/me",
        "header": [
          { "key": "Authorization", "value": "Bearer {{access_token}}" }
        ]
      }
    },
    {
      "name": "Logout",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/api/auth/logout",
        "header": [
          { "key": "Authorization", "value": "Bearer {{access_token}}" }
        ]
      }
    }
  ]
}
```

**使用说明**：
1. 在 Postman 中导入上述 JSON
2. 设置环境变量 `base_url` 为 `http://localhost:8000`
3. 先运行 "Login - Success"，自动保存 `access_token`
4. 再运行 "Get Current User" 和 "Logout"，会自动使用保存的 Token

---

## 12. 变更历史

| 版本 | 日期 | 修改内容 | 作者 |
| --- | --- | --- | --- |
| V1.0 | 2026-06-12 | 初版：阶段 1 认证与权限 API 契约文档 | AI 开发助手 |

---

**文档结束**
