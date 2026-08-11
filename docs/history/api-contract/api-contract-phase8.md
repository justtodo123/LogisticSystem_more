# 阶段8 API 契约文档 - AI 助手与收尾（F014）

**版本**：V1.0  
**日期**：2026-06-23  
**阶段**：阶段8（AI 助手与收尾 F014）  
**状态**：✅ 已完成（P0 全部实现，P1 占位 501）

---

## 1. 文档概述

本文档定义阶段8（AI 助手集成 DeepSeek）的 API 契约，包括：

- `POST /api/ai/parse` — 自然语言解析 → 调度执行（P0 核心，F014）
- `POST /api/ai/explain` — 方案解释（P1 占位 501）
- `POST /api/ai/review` — 方案审查（P1 占位 501）
- `POST /api/ai/analyze-exception` — 异常分析（P1 占位 501）

所有接口遵循统一响应格式 `{code, message, data, meta}`。

> ⚠️ **P1 端点说明**：`/explain`、`/review`、`/analyze-exception` 已注册路由，返回 `code=50100` + HTTP 200，前端可据此展示"功能开发中"提示，避免 404 混淆。

---

## 2. API 端点列表

| 方法 | 路径 | 说明 | 认证 | 状态 |
|------|------|------|------|------|
| `POST` | `/api/ai/parse` | 自然语言解析 → 调度执行（F014） | Bearer Token | ✅ P0 |
| `POST` | `/api/ai/explain` | 方案解释（F015） | Bearer Token | ⏳ P1 501 |
| `POST` | `/api/ai/review` | 方案审查（F016） | Bearer Token | ⏳ P1 501 |
| `POST` | `/api/ai/analyze-exception` | 异常分析（F017） | Bearer Token | ⏳ P1 501 |

---

## 3. POST /api/ai/parse — 详细说明

### 3.1 功能概述

三步模型：

```
┌──────────────────────────────────────────────────────────────┐
│ Step 1: 确定参数来源 (mode)                                    │
│   message? + weights? → ai / manual / hybrid / default        │
├──────────────────────────────────────────────────────────────┤
│ Step 2: 确定执行目标                                           │
│   schedule_codes 非空 → 版本化重规划 draft                      │
│   schedule_codes 为空 → 新建 draft（全部 pending 订单）         │
├──────────────────────────────────────────────────────────────┤
│ Step 3: execute="dry-run" → 仅返回参数（不写库）                │
│         execute="draft"    → F007 生成 draft 方案              │
│         （需手动调用 confirm 接口执行 F021/F005/F006）           │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 请求参数

**请求体** (`AiParseRequest`)：

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `message` | string | 否 | `null` | 自然语言指令（非空 → DeepSeek 解析） |
| `weights` | object | 否 | `null` | 手动权重覆盖（结构与 `algorithm_config.json` 一致） |
| `schedule_codes` | string[] | 否 | `null` | 目标方案编号列表（非空 → 版本化重规划 draft） |
| `execute` | string | 否 | `"draft"` | `"draft"`=生成 draft 方案 / `"dry-run"`=仅返回参数不落库 |

> **P1-2 变更**：`execute` 从 `boolean` 改为字符串枚举。`"draft"` 模式仅执行 F007（预览），不执行 F021/F005/F006。用户需手动调用 `POST /api/schedule/confirm/{code}` 完成打包和执行。

**工作逻辑矩阵**：

| `message` | `weights` | `mode` | `schedule_codes` | 执行目标 |
|:-:|:-:|:-:|:-:|---|
| ✅ | ❌ | `ai` | ❌ | DeepSeek 新建 |
| ✅ | ❌ | `ai` | ✅ | DeepSeek 重规划 |
| ❌ | ✅ | `manual` | ❌ | 手动新建 |
| ❌ | ✅ | `manual` | ✅ | 手动重规划 |
| ✅ | ✅ | `hybrid` | ❌ | 混合新建 |
| ✅ | ✅ | `hybrid` | ✅ | 混合重规划 |
| ❌ | ❌ | `default` | ❌ | 默认新建 |
| ❌ | ❌ | `default` | ✅ | 默认重规划 |

> 任意组合 × `execute` = 8 种 draft 模式 + 8 种 dry-run 模式，共计 16 种场景。

### 3.3 请求示例

**① AI 重规划（最常用）**：

```json
{
  "message": "优先缩短距离，多用电车",
  "schedule_codes": ["GS20260623001"]
}
```

**② AI 新建调度**：

```json
{
  "message": "优先时效，减少总时间"
}
```

**③ AI 重规划 + 权重覆盖**：

```json
{
  "message": "优先时效",
  "weights": {
    "global_schedule": {
      "weights": {
        "time": 0.7
      }
    }
  },
  "schedule_codes": ["GS20260623001"]
}
```

**④ 纯手动权重重规划**：

```json
{
  "weights": {
    "global_schedule": {
      "weights": {
        "distance": 0.9,
        "time": 0.05,
        "package_count": 0.05
      }
    }
  },
  "schedule_codes": ["GS20260623001"]
}
```

**⑤ 默认参数重规划**：

```json
{
  "schedule_codes": ["GS20260623001"]
}
```

**⑥ dry-run 预览**：

```json
{
  "message": "优先缩短距离，多用电车",
  "execute": "dry-run"
}
```

**⑦ 批量重规划**（⚠️ 只处理第一个方案）：

```json
{
  "message": "缩短距离",
  "schedule_codes": [
    "GS20260623001",
    "GS20260623002",
    "GS20260623003"
  ]
}
```

> **注意**：AI 接口只生成一个 draft 方案，无论 `schedule_codes` 传入几个，只处理第一个方案。如需对多个方案重规划，需多次调用。

**⑧ 手动权重 dry-run**：

```json
{
  "weights": {
    "global_schedule": {
      "weights": {
        "time": 0.7
      }
    }
  },
  "execute": "dry-run"
}
```

### 3.4 响应格式

#### dry-run 成功响应

```json
{
  "code": 0,
  "message": "success (dry-run)",
  "data": {
    "algorithm_params": {
      "global_schedule": {
        "algorithm": "traditional",
        "weights": {
          "distance": 0.7,
          "time": 0.1,
          "package_count": 0.2
        }
      }
    },
    "mode": "ai"
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

> **dry-run 响应简化**：只返回 `algorithm_params` + `mode`，不含 `status`/`reference_codes`/`is_replan` 等字段。

#### AI 重规划成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "schedule_code": "GS20260623010",
    "algorithm_params": {
      "global_schedule": {
        "algorithm": "traditional",
        "weights": {
          "distance": 0.6,
          "time": 0.2,
          "package_count": 0.2
        }
      }
    },
    "mode": "ai",
    "is_replan": true,
    "status": "draft",
    "reference_codes": ["GS20260623008"]
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

> **重规划响应简化**：移除 `replan_results` 字段，重规划与新建响应结构完全一致。只处理 `schedule_codes` 第一个方案（AI 接口只生成一个 draft 方案）。

#### AI 新建调度成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "schedule_code": "GS20260623012",
    "algorithm_params": {
      "global_schedule": {
        "algorithm": "traditional",
        "weights": {
          "distance": 0.7,
          "time": 0.1,
          "package_count": 0.2
        }
      }
    },
    "mode": "ai",
    "is_replan": false,
    "status": "draft",
    "reference_codes": null
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

#### DeepSeek 降级响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "schedule_code": "GS20260623013",
    "algorithm_params": {
      "global_schedule": {
        "algorithm": "traditional",
        "weights": {
          "distance": 0.5,
          "time": 0.3,
          "package_count": 0.2
        }
      }
    },
    "mode": "ai",
    "is_replan": false,
    "status": "draft",
    "reference_codes": null
  },
  "meta": {
    "degraded": true,
    "degraded_reason": "DeepSeek API 调用超时（30秒）"
  }
}
```

### 3.5 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `schedule_code` | string | 生成的新调度方案编号（新建/重规划均返回此字段） |
| `algorithm_params` | object | 最终使用的算法参数（只含 `global_schedule`） |
| `mode` | string | 参数来源模式：`ai` / `manual` / `hybrid` / `default` |
| `is_replan` | boolean | 是否为重规划（新建=false，重规划=true） |
| `status` | string | 执行状态：`"draft"`=已生成 draft 方案（dry-run 响应不含此字段） |
| `reference_codes` | array\|null | 参考的方案编号列表（即入参 `schedule_codes`） |

> **响应结构对齐**：新建和重规划模式响应结构完全一致，仅 `is_replan` 字段区分。dry-run 响应只含 `algorithm_params` + `mode`。

### 3.6 错误码

| code | HTTP 状态码 | 说明 |
|------|------------|------|
| 0 | 200 | 成功 |
| 40000 | 400 | 参数校验失败（Pydantic 自动校验 `AiParseRequest`） |
| 40001 | 200 | 业务失败 — 全局调度失败（无 pending 订单/容量不足等） |
| 40001 | 200 | 业务失败 — 节点调度失败 |
| 40001 | 200 | 业务失败 — 路径规划失败 |
| 40001 | 200 | 业务失败 — 重规划时原方案不存在（`40401` code） |
| 40300 | 403 | 无权限（manager 角色） |
| 50000 | 500 | 服务器内部错误 |

---

## 4. DeepSeek 集成详情

### 4.1 系统上下文注入

`DeepSeekService` 在调用 DeepSeek API 时自动构建上下文：

| 上下文字段 | 来源 | 说明 |
|----------|------|------|
| `order_count` | `OrderService.get_orders(status=pending)` | 待分配订单数 |
| `vehicle_count` | `VehicleService.get_vehicles(status=idle)` | 可用车辆数 |
| `node_count` | `NodeService.get_nodes()` | 节点总数 |
| `pending_orders` | 同上（前10条） | 订单编号、目的地、时效 |
| `reference_schedules` | `GlobalSchedule WHERE schedule_code IN (...)` | 历史方案指标（距离/时间/货物数/评分/version/is_replan） |
| `target_schedule` | 首个 `schedule_code` 的方案 | 重规划目标方案详细指标 |

### 4.2 降级策略

| 失败场景 | 处理方式 | `meta.degraded` | `meta.degraded_reason` |
|---------|---------|:---:|------|
| `DEEPSEEK_API_KEY` 未配置 | 使用默认参数 | `true` | `"DeepSeek API Key 未配置"` |
| 网络超时（30s） | 使用默认参数 | `true` | `"DeepSeek API 调用超时（30秒）"` |
| HTTP 4xx/5xx 错误 | 使用默认参数 | `true` | `"DeepSeek API 返回错误：{status_code}"` |
| 响应 JSON 解析失败 | 使用默认参数 | `true` | `"DeepSeek 返回格式错误，无法解析 JSON"` |
| 其他异常 | 使用默认参数 | `true` | `"DeepSeek API 调用失败：{error}"` |
| 调用成功 | 使用 DeepSeek 参数 | `false` | `null` |

> ⚠️ **绝不伪造 AI 成功结果**：任何 DeepSeek 调用失败场景，均使用 `algorithm_config.json` 默认参数完成调度，并在 `meta.degraded=true` 中明确告知用户。

### 4.3 API 配置

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥（必填） | — |
| `DEEPSEEK_API_BASE` | API 端点 Base URL | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | 模型名称 | `deepseek-chat` |

统一使用 OpenAI `/chat/completions` 格式，同时兼容 DeepSeek 官方 API 与火山引擎 ARK。

### 4.4 调用埋点

每次 DeepSeek API 调用自动写入 `log_events` 表：

| 字段 | 值 |
|------|-----|
| `event_name` | `"deepseek_call"` |
| `event_data` | `{"function": "parse", "success": bool, "degraded": bool}` |

---

## 5. 执行模式对比

### 5.1 新建调度 vs 重规划

| 对比维度 | 新建调度 (`schedule_codes=null`) | 重规划 (`schedule_codes` 非空) |
|---------|-------------------------------|------------------------------|
| 订单范围 | 全部 `pending` 状态订单 | 原方案关联的订单 |
| 调度链路 | F007 preview（仅 draft） | `ReplanService.redispatch(draft_only=True)` |
| 版本链 | version=1，新记录 | version+1，`parent_id` 指向前版 |
| `is_replan` | `false` | `true` |
| 后续确认 | 手动调用 `POST /api/schedule/confirm/{code}` | 手动调用 `POST /api/schedule/confirm/{code}` |

> **P1-2 变更**：AI parse 统一生成 draft 方案，不执行 F021/F005/F006，需手动确认。dry-run 模式除外。

### 5.2 AI 重规划 vs 异常驱动重规划

| 对比维度 | AI 重规划 (`/api/ai/parse`) | 异常驱动重规划 (`/api/exceptions/{code}/replan`) |
|---------|---------------------------|----------------------------------------------|
| 触发方式 | 自然语言 + `schedule_codes` | 异常事件 + `action` |
| 参数来源 | DeepSeek 解析 / 手动 / 默认 | 默认参数（`algorithm_config.json`） |
| 执行模式 | draft only（仅 F007），需手动 confirm | 完整链路 F007→F021→F005→F006 |
| 货物状态处理 | 不修改原方案状态 | 原包裹→exception，原批次→failed |
| 排除参数 | 不支持 | `excluded_nodes` / `excluded_vehicles` |

> **P1-2 变更**：AI 重规划改为 draft 模式，不执行全链路。异常驱动重规划保持完整链路（需立即响应）。

### 5.3 性能参考

| 场景 | 模式 | 典型耗时 |
|------|------|---------|
| dry-run | ai | ~7s（DeepSeek API 调用） |
| AI 重规划 draft | ai+replan | ~8s（DeepSeek + F007 preview） |
| AI 新建 draft | ai | ~8s（DeepSeek + F007 preview） |
| 手动权重重规划 | manual+replan | ~1s（仅 F007 preview） |
| 默认参数重规划 | default+replan | ~1s（仅 F007 preview） |

> **P1-2 性能优化**：draft 模式大幅缩短响应时间（避免 F021/F005/F006 链式执行）。用户确认方案后，F021/F005/F006 在 `confirm` 接口中执行。

---

## 6. P1 占位端点

### 6.1 POST /api/ai/explain

**功能**：方案解释（F015），P1 占位

**响应**：

```json
{
  "code": 50100,
  "message": "F015 方案解释功能正在开发中（P1）",
  "data": null,
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

### 6.2 POST /api/ai/review

**功能**：方案审查（F016），P1 占位

**响应**：

```json
{
  "code": 50100,
  "message": "F016 方案审查功能正在开发中（P1）",
  "data": null,
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

### 6.3 POST /api/ai/analyze-exception

**功能**：异常分析（F017），P1 占位

**响应**：

```json
{
  "code": 50100,
  "message": "F017 异常分析功能正在开发中（P1）",
  "data": null,
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

---

## 7. 前端集成指南

### 7.1 调用流程

```
用户输入自然语言
  → 前端调用 POST /api/ai/parse
  → 后端三步模型处理
  → 返回统一响应

前端需检查:
  1. response.data.code !== 0 → 展示错误信息
  2. response.data.meta.degraded === true → 展示降级提示（ElAlert warning）
  3. response.data.data.mode → 展示参数来源标识
  4. response.data.data.executed === false → dry-run 模式，展示解析参数
```

### 7.2 前端提示文案

| 场景 | 组件 | 文案 |
|------|------|------|
| DeepSeek 降级 | `ElAlert type="warning"` | "DeepSeek API 调用失败，已使用默认算法参数完成调度" |
| dry-run 完成 | `ElAlert type="info"` | "AI 参数解析完成（未执行调度），您可以检查参数后确认执行" |
| AI 重规划成功 | `ElMessage type="success"` | "AI 重规划完成，新方案：{schedule_code}" |
| P1 功能 | `ElAlert type="info"` | "该功能正在开发中（P1），敬请期待" |

### 7.3 按钮防重复

调度接口可能耗时 7-30 秒（含 DeepSeek API 调用），前端按钮必须防重复点击：

```typescript
const loading = ref(false)
async function handleAiParse() {
  if (loading.value) return
  loading.value = true
  try {
    await api.post('/api/ai/parse', payload, { timeout: 60000 })
  } finally {
    loading.value = false
  }
}
```

> ⚠️ **timeout 建议 ≥ 60s**：AI 重规划全链路（DeepSeek + F007→F006）可能超 30 秒。

---

## 8. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| V1.0 | 2026-06-23 | 初始版本：`POST /api/ai/parse` 完整契约 + P1 占位端点 |
| V1.1 | 2026-06-25 | `execute` 改为 `"draft"`/`"dry-run"` 枚举；新建/重规划均生成 draft，需手动 confirm |
| V1.2 | 2026-06-25 | AI 解析只返回 `global_schedule` 权重；响应移除 `replan_results`；dry-run 响应简化 |

---

## 9. 相关文档

- [项目宪章](../../.codebuddy/CODEBUDDY.md)
- [MVP 开发计划 - 后端](../MVP开发计划-后端.md)
- [系统架构设计说明书](../architecture/系统架构设计说明书.md)
- [后端 README](../../src/backend/README.md)
- [阶段7 API 契约文档](api-contract-phase7.md)
- [阶段8 开发文档](../../My_doc/阶段8开发文档.md)（待创建）
