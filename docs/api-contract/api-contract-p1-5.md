# P1-5 API 契约文档 — AI 方案解释 (F015)

> **版本**: V1.0  
> **生成日期**: 2026-06-25  
> **功能编号**: F015  
> **端点**: `POST /api/ai/explain`  
> **状态**: ✅ 已实现（含 DeepSeek 降级策略）

---

## 目录

1. [功能概述](#1-功能概述)
2. [接口定义](#2-接口定义)
3. [请求规范](#3-请求规范)
4. [响应规范](#4-响应规范)
5. [DeepSeek 降级策略](#5-deepseek-降级策略)
6. [错误码](#6-错误码)
7. [数据流转](#7-数据流转)
8. [后端实现要点](#8-后端实现要点)
9. [前端对接指南](#9-前端对接指南)
10. [测试用例](#10-测试用例)
11. [变更记录](#11-变更记录)

---

## 1. 功能概述

### 1.1 业务背景

调度员在查看某一调度方案或批次时，需要理解以下问题：

- **这个方案为什么长这样？** — 算法决策逻辑是什么？
- **有哪些潜在风险？** — 容量不足、时效瓶颈等
- **还能怎么优化？** — 有哪些可行的改进方向？

F015 通过 DeepSeek 大模型，将结构化调度数据转化为自然语言解释，帮助调度员快速理解方案优劣并做出决策。

### 1.2 调用时机

| 场景 | 说明 |
|------|------|
| 查看调度方案详情 | 传入 `schedule_code`，获取该方案的整体解释 |
| 查看批次调度详情 | 传入 `batch_code`，获取该批次的调度解释 |
| 方案对比 | 对多个方案分别调用 `explain`，对比 `key_decisions` 和 `suggestions` |

### 1.3 输出内容

| 字段 | 含义 | 示例 |
|------|------|------|
| `explanation` | 整体解释文本（2~5 句话） | "该方案采用传统贪心算法，优先选择距离最短的 L1 分拣中心…" |
| `key_decisions` | 关键决策列表（3~5 条） | `["选择 SO001 作为中间节点，距离最优", "17件货物分配至3个L1节点"]` |
| `potential_risks` | 潜在风险列表（2~3 条） | `["SO001 容量使用率达 85%，接近上限"]` |
| `suggestions` | 优化建议列表（2~3 条） | `["增加 SO001 容量配置", "考虑 SO003 作为备选分流节点"]` |

---

## 2. 接口定义

### 2.1 基本信息

```
POST /api/ai/explain
```

| 属性 | 值 |
|------|-----|
| **认证** | Bearer Token（登录即可，不限角色） |
| **Content-Type** | `application/json` |
| **超时建议** | 前端 Axios timeout ≥ 70s（DeepSeek 调用最长 60s） |
| **幂等性** | 是（相同输入返回相同解释，不产生副作用） |
| **降级策略** | DeepSeek 不可用时返回空解释 + `meta.degraded=true` |

### 2.2 请求体 Schema

```json
{
  "schedule_code": "string | null",   // 调度方案编码
  "batch_code": "string | null"       // 调度批次编码
}
```

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| `schedule_code` | `string` | 条件 | 与 `batch_code` 至少提供一个 |
| `batch_code` | `string` | 条件 | 与 `schedule_code` 至少提供一个 |

> **优先级**：`schedule_code` 非空时以方案为主，`batch_code` 数据作为补充上下文。

### 2.3 响应体 Schema

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "explanation": "string",          // 整体解释文本
    "key_decisions": ["string"],      // 关键决策列表
    "potential_risks": ["string"],    // 潜在风险列表
    "suggestions": ["string"]         // 优化建议列表
  },
  "meta": {
    "degraded": false,                // 是否降级
    "degraded_reason": null           // 降级原因（仅 degraded=true 时有值）
  }
}
```

---

## 3. 请求规范

### 3.1 正常请求示例

**按方案编码解释**（最常用）：

```json
{
  "schedule_code": "GS20260625001"
}
```

```bash
curl -X POST http://localhost:8000/api/ai/explain \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"schedule_code": "GS20260625001"}'
```

**按批次编码解释**：

```json
{
  "batch_code": "BATCH20260625001"
}
```

**同时传入**（方案为主，批次为补充上下文）：

```json
{
  "schedule_code": "GS20260625001",
  "batch_code": "BATCH20260625001"
}
```

### 3.2 参数校验规则

| 条件 | HTTP 状态 | code | 说明 |
|------|-----------|------|------|
| `schedule_code` 和 `batch_code` 均为空 | 200 | 40001 | 至少一个必须提供 |
| `schedule_code` 不存在 | 200 | 40401 | 指定方案不存在 |
| `batch_code` 不存在 | 200 | 40401 | 指定批次不存在 |
| 两者都不存在 | 200 | 40401 | — |

---

## 4. 响应规范

### 4.1 成功响应（DeepSeek 正常）

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "explanation": "该调度方案共处理17件货物，总里程125.3公里，预计耗时8.5小时。方案采用贪心算法优先为每件货物选择距离最近的1级分拣中心（L1），然后由L1分配至目标0级分拣中心（L2）。评分83分，整体效率较好。",
    "key_decisions": [
      "SO001（武汉1级分拣中心）承接10件货物，为核心中转节点",
      "SO002承接5件货物，作为辅助节点分担压力",
      "SO003承接2件货物，处理偏远区域订单",
      "所有货物路径均为 L0→L1→L2 三段式标准路径"
    ],
    "potential_risks": [
      "SO001容量使用率达85%，若后续追加订单可能出现容量不足",
      "部分路线预计耗时超过2小时，需关注司机排班",
      "新能源车辆覆盖不足，燃油车占比偏高可能增加碳排放"
    ],
    "suggestions": [
      "建议启用SO003作为分流节点，降低SO001负载",
      "为长途路线优先分配电动车，降低碳排放",
      "考虑将部分L2节点的货物合并配送，减少车辆使用数"
    ]
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

### 4.2 降级响应（DeepSeek 不可用）

```json
{
  "code": 0,
  "message": "success",
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

> **前端处理**：检测 `meta.degraded === true` 时，使用 `ElAlert` type="warning" 展示降级提示，不展示"AI 解释成功"。

### 4.3 响应字段约束

| 字段 | 类型 | 非空约束 | 说明 |
|------|------|----------|------|
| `explanation` | `string` | 必有值（降级时为默认文本） | 自然语言解释 |
| `key_decisions` | `string[]` | 可为空数组 `[]` | 关键决策 |
| `potential_risks` | `string[]` | 可为空数组 `[]` | 潜在风险 |
| `suggestions` | `string[]` | 可为空数组 `[]` | 优化建议 |

---

## 5. DeepSeek 降级策略

### 5.1 降级触发条件

| 场景 | `degraded_reason` 示例 |
|------|------------------------|
| API 超时 (>60s) | `"DeepSeek API 调用超时（60秒）"` |
| 网络不可达 | `"DeepSeek API 网络不可达"` |
| API Key 无效 | `"DeepSeek API Key 无效或配额耗尽"` |
| 响应格式异常 | `"DeepSeek 返回格式异常，无法解析"` |
| 其他未预期异常 | `"<异常信息>"` |

### 5.2 降级响应原则（遵守项目宪法第 6 条）

1. **HTTP 200 + code=0**：不返回 5xx 错误，保持接口可用
2. **`meta.degraded=true`**：明确告知前端 AI 服务降级
3. **`data` 字段不为 null**：返回空解释结构，前端无需空值防御
4. **绝不伪造 AI 成功结果**：不编造解释文本

### 5.3 降级流程图

```
用户请求 POST /api/ai/explain
       │
       ▼
 ┌─ 查询 schedule/batch 数据 ─┐
 │        ↓                   │
 │   数据不存在？──── 是 ──→ 返回 40401         │
 │        │ 否                │
 │        ▼                   │
 │   DeepSeek API 调用        │
 │        │                   │
 │   ┌────┴────┐              │
 │  成功       失败             │
 │   │         │              │
 │   ▼         ▼              │
 │ 返回完整   ┌─ 记录异常日志          │
 │ 解释数据   │  meta.degraded=true │
 │           │  data=空解释结构       │
 │           │  返回 code=0         │
 │           └────────────────────  │
 └───────────────────────────────  ┘
```

---

## 6. 错误码

| code | HTTP | 说明 | 触发场景 |
|------|------|------|----------|
| `0` | 200 | 成功 | 正常响应（含降级） |
| `40000` | 400 | 参数校验失败 | 请求体格式错误 |
| `40001` | 200 | 业务参数缺失 | `schedule_code` 和 `batch_code` 均为空 |
| `40100` | 401 | 未登录或 Token 无效 | Token 缺失/格式错误/密钥不匹配 |
| `40101` | 401 | Token 已过期 | JWT 过期 |
| `40401` | 200 | 指定资源不存在 | `schedule_code` 或 `batch_code` 查无记录 |
| `50000` | 500 | 服务器内部错误 | 未预期的服务器异常（非 DeepSeek 降级场景） |

---

## 7. 数据流转

### 7.1 后端处理流程

```
POST /api/ai/explain
       │
       ▼
  ┌──────────────┐
  │ 参数校验      │  ← schedule_code / batch_code 至少一个非空
  └──────┬───────┘
         │ 通过
         ▼
  ┌──────────────┐
  │ 查询数据      │  ← ScheduleService.get_global_schedule()
  │              │    DispatchService.get_dispatch_batch_detail()
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ 构建 Prompt   │  ← 货物路径摘要（最多30条）+ 包裹摘要（最多20个）
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ DeepSeek API  │  ← httpx.AsyncClient timeout=60s
  │    调用       │     system_prompt: 物流调度专家角色
  └──────┬───────┘     user_prompt: 压缩后的方案数据
         │
    ┌────┴────┐
   成功       失败
    │         │
    ▼         ▼
  解析      meta.degraded=true
  JSON      data=空解释
    │         │
    └────┬────┘
         ▼
  ┌──────────────┐
  │ 统一响应格式   │  ← { code, message, data, meta }
  └──────────────┘
```

### 7.2 Prompt 数据压缩策略

为避免数据量过大导致 DeepSeek token 超限或响应超时，传入 DeepSeek 的数据经过压缩：

| 原始数据 | 压缩方式 | 最大条数 |
|----------|----------|----------|
| `goods_schedules` | 每条只保留 `goods_code` + `path` 节点序列 | 30 条 |
| `packages` | 每个只保留 `package_code` + `status` + 前 5 个 `goods_codes` | 20 个 |

**压缩前后 Token 对比**：

| 场景 | 压缩前（估算） | 压缩后（估算） |
|------|---------------|---------------|
| 50 货物 + 100 包裹 | ~8000 tokens | ~1500 tokens |
| 100 货物 + 200 包裹 | ~16000 tokens | ~2000 tokens |

---

## 8. 后端实现要点

### 8.1 关键文件

| 文件 | 职责 |
|------|------|
| `api/ai.py` (L295-L357) | 路由处理：参数校验 → 数据查询 → 调用服务 → 异常降级 |
| `services/deepseek_service.py` (L314-L394) | `explain_schedule()` 方法：Prompt 构建 + DeepSeek API 调用 |
| `schemas/ai.py` (L134-L146) | `AiExplainRequest` / `AiExplainResponse` Pydantic 模型 |

### 8.2 路由层降级处理

```python
# api/ai.py 降级逻辑 (L341-L357)
except Exception as e:
    logger.error(f"方案解释失败：{e}")
    return {
        "code": 0,
        "message": "success",
        "data": {
            "explanation": "AI服务暂时不可用，请稍后重试",
            "key_decisions": [],
            "potential_risks": [],
            "suggestions": []
        },
        "meta": {
            "degraded": True,
            "degraded_reason": str(e)
        }
    }
```

### 8.3 DeepSeek Service 超时配置

- `httpx.AsyncClient(timeout=60.0)` — 60 秒超时
- 使用 `temperature=0.3` 保持解释一致性
- `max_tokens=1024` 限制输出长度

---

## 9. 前端对接指南

### 9.1 API 调用封装

```typescript
// src/api/ai.ts
import request from './request'

/** 方案解释 (F015) */
export function explainSchedule(params: {
  schedule_code?: string
  batch_code?: string
}) {
  return request.post<{
    explanation: string
    key_decisions: string[]
    potential_risks: string[]
    suggestions: string[]
  }>('/ai/explain', params)
}
```

### 9.2 组件用法

```vue
<template>
  <!-- 降级提示 -->
  <el-alert
    v-if="meta?.degraded"
    type="warning"
    :title="'AI 服务暂时不可用'"
    :description="meta.degraded_reason"
    show-icon
    closable
  />

  <!-- 正常展示 -->
  <template v-else-if="explainData">
    <div class="explain-text">{{ explainData.explanation }}</div>
    
    <h4>关键决策</h4>
    <ul>
      <li v-for="(item, i) in explainData.key_decisions" :key="i">
        {{ item }}
      </li>
    </ul>

    <h4>潜在风险</h4>
    <el-tag 
      v-for="(item, i) in explainData.potential_risks" 
      :key="i" 
      type="warning" 
      effect="plain"
    >
      {{ item }}
    </el-tag>

    <h4>优化建议</h4>
    <ul>
      <li v-for="(item, i) in explainData.suggestions" :key="i">
        {{ item }}
      </li>
    </ul>
  </template>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { explainSchedule } from '@/api/ai'

const explainData = ref(null)
const meta = ref(null)
const loading = ref(false)

async function fetchExplain(scheduleCode: string) {
  loading.value = true
  try {
    const res = await explainSchedule({ schedule_code: scheduleCode })
    if (res.data.code === 0) {
      explainData.value = res.data.data
      meta.value = res.data.meta
    }
  } finally {
    loading.value = false
  }
}
</script>
```

### 9.3 前端注意事项

| 注意点 | 说明 |
|--------|------|
| **超时设置** | Axios timeout ≥ 70s（DeepSeek 最长 60s + 网络余量） |
| **降级处理** | `meta.degraded === true` 时显示 Warning Alert，不显示"AI 成功" |
| **空数组防御** | `key_decisions` / `potential_risks` / `suggestions` 可能为空数组 `[]` |
| **加载态** | 按钮/面板显示 Loading，防止用户误以为卡死 |
| **幂等调用** | 相同输入可重复调用，无需防重 |

---

## 10. 测试用例

### 10.1 正常场景

| 用例 | 输入 | 预期 |
|------|------|------|
| TC-EX-01 | `{"schedule_code": "GS20260625001"}` | 返回完整解释（4 字段均非空） |
| TC-EX-02 | `{"batch_code": "BATCH20260625001"}` | 返回完整解释 |
| TC-EX-03 | `{"schedule_code": "...", "batch_code": "..."}` | 以 schedule 为主，batch 为补充 |

### 10.2 异常场景

| 用例 | 输入 | 预期 code | 预期 message |
|------|------|-----------|--------------|
| TC-EX-04 | `{}` | 40001 | `schedule_code和batch_code至少一个必须提供` |
| TC-EX-05 | `{"schedule_code": "NOT_EXIST"}` | 40401 | 指定方案不存在 |
| TC-EX-06 | `{"batch_code": "NOT_EXIST"}` | 40401 | 指定批次不存在 |

### 10.3 降级场景

| 用例 | 条件 | 预期 |
|------|------|------|
| TC-EX-07 | DeepSeek API 超时 | `meta.degraded=true`，`explanation="AI服务暂时不可用…"` |
| TC-EX-08 | DeepSeek 返回非 JSON | `meta.degraded=true`，空解释数组 |
| TC-EX-09 | API Key 无效 | `meta.degraded=true`，空解释数组 |

### 10.4 边界场景

| 用例 | 输入 | 预期 |
|------|------|------|
| TC-EX-10 | 超大批次（100+ 货物） | 正常返回（数据压缩至 30 条货物摘要） |
| TC-EX-11 | 无包裹的方案（draft 状态） | 正常返回（包裹清单显示"无数据"） |
| TC-EX-12 | manager 角色调用 | 正常返回（登录即可，不限角色） |
| TC-EX-13 | 未登录调用 | 返回 40100 |

---

## 11. 变更记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| V1.0 | 2026-06-25 | 初始版本：F015 方案解释 API 契约，含 DeepSeek 降级策略、数据压缩、前后端对接指南 |
