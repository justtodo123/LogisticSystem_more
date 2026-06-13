# 后端 → 前端交付说明

> 本文档面向**前端开发**，按阶段记录后端提供的接口、配置和联调信息。

---

## 全局约定（所有阶段通用）

### 后端服务

| 项目 | 值 |
|------|-----|
| 地址 | `http://localhost:8000` |
| Swagger | `http://localhost:8000/docs` |
| API 前缀 | `/api` |

```bash
# 启动命令
cd src/backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

> 访问时用 `http://localhost:8000`，不要用 `http://0.0.0.0:8000`。

### 统一响应格式

所有接口遵循此格式：

```json
{
  "code": 0,
  "message": "success",
  "data": { ... },
  "meta": { ... }
}
```

| code | 含义 | HTTP 状态码 |
|------|------|-------------|
| `0` | 成功 | 200 |
| `40000` | 参数校验失败 | 400 |
| `40100` | 未登录 | 401 |
| `40101` | Token 过期 | 401 |
| `40300` | 无权限 | 403 |

`meta` 字段（可选）：
```json
{ "degraded": false, "degraded_reason": null }
```
- `degraded = true` 时表示 AI 降级，前端需明确提示用户。

### CORS

后端已允许 `http://localhost:5173` 的跨域请求。

### 前端配置建议

**Vite 代理**（`vite.config.ts`）：
```ts
export default defineConfig({
  server: {
    proxy: { '/api': 'http://localhost:8000' }
  }
})
```

**Axios 封装参考**（`src/api/request.ts`）：
```ts
import axios from 'axios'

const request = axios.create({
  baseURL: '/api',
  timeout: 15000  // 调度接口可能接近 10 秒
})

request.interceptors.response.use(
  (response) => {
    const { code, message, data } = response.data
    if (code !== 0) return Promise.reject(new Error(message))
    return data
  },
  (error) => Promise.reject(error)
)
```

---

## 阶段 0：工程初始化

### 新增接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |

### GET /api/health

响应：
```json
{
  "code": 0,
  "message": "success",
  "data": { "status": "ok" }
}
```

### 联调验证

1. 启动前端 `npm run dev`
2. 访问 `GET /api/health` 返回上述 JSON
3. 确认前后端通信正常

---

## 阶段 1：认证与权限

> 待阶段 1 开发完成后补充。

---

## 阶段 2：基础数据管理

> 待阶段 2 开发完成后补充。

---

## 阶段 3：全局调度

> 待阶段 3 开发完成后补充。

---

## 阶段 4：节点间调度

> 待阶段 4 开发完成后补充。

---

## 阶段 5：路径规划与可视化

> 待阶段 5 开发完成后补充。

---

## 阶段 6：模拟送达

> 待阶段 6 开发完成后补充。

---

## 阶段 7：异常与重规划

> 待阶段 7 开发完成后补充。

---

## 阶段 8：AI 助手与收尾

> 待阶段 8 开发完成后补充。
