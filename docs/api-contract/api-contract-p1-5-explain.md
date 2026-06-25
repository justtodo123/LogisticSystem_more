# API 契约文档 · P1-5 AI 方案解释（F015）

| 字段 | 值 |
| --- | --- |
| **阶段** | P1-5（选做） |
| **功能编号** | P1-01 / F015 |
| **文档版本** | V1.0 |
| **创建日期** | 2026-06-25 |
| **参考文档** | [api-contract-phase8.md](./api-contract-phase8.md) · [P1功能概览.md](../P1功能概览.md) |

---

## 1. 概述

F015 **方案解释**：对指定**全局调度方案**（`schedule_code`）生成自然语言解释，说明调度原因、潜在风险与优化建议。

- v1 范围：仅全局方案（与 Dashboard 方案下拉一致）
- 节点间调度解释（`dispatch_code`）留后续扩展
- 当前后端占位：`code=50100`；本契约定义正式实现形状

---

## 2. 接口契约

### 2.1 POST /api/ai/explain

**认证**：Bearer Token

**权限（建议，P1-12）**：

| 角色 | 说明 |
| --- | --- |
| dispatcher | 可调用 |
| manager | 可调用（只读解释，不可 parse 执行调度） |

#### Request Body

```json
{
  "schedule_code": "GS20260625001",
  "detail_level": "detailed"
}
```

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `schedule_code` | `string` | **是** | 全局方案编号 |
| `detail_level` | `string` | 否 | `brief` / `detailed`，默认 `detailed` |

> **后端缺口（2026-06-25）**：当前 [`ai.py`](../../src/backend/api/ai.py) 未定义请求体 Pydantic 模型，实现时需补 `AiExplainRequest`。

#### Response — 成功（`code=0`）

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "schedule_code": "GS20260625001",
    "explanation": "本方案共调度 18 件货物……",
    "sections": {
      "reasoning": "优先将同订单货物汇聚至同一 L1 分拣中心……",
      "risks": ["部分路径总距离较长", "高峰时段时效压力"],
      "suggestions": ["可考虑增加 L1 容量冗余", "对远距离订单单独分批"]
    }
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `data.explanation` | `string` | 自然语言全文（纯文本/Markdown 均可） |
| `data.sections` | `object?` | 结构化分段；各子字段均可选 |
| `data.sections.reasoning` | `string?` | 调度原因 |
| `data.sections.risks` | `string[]?` | 潜在风险 |
| `data.sections.suggestions` | `string[]?` | 优化建议 |
| `meta.degraded` | `boolean` | DeepSeek 失败时为 `true`，`explanation` 为模板兜底文案 |

#### Response — 未实现占位（当前）

HTTP 200，`code=50100`：

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

前端收到 `50100` 时展示 info 提示，不 throw。

#### 错误码

| code | 说明 |
| --- | --- |
| 0 | 成功 |
| 40100 / 40101 | 未授权 |
| 40400 | 方案不存在 |
| 50100 | 功能未实现（占位） |
| 其他 | 业务错误 |

---

## 3. 前端集成要点

- 入口：Dashboard `AiAssistantPanel` →「方案解释」
- 须先在上方方案下拉选中 `schedule_code`
- 请求 `timeout` 建议 ≥ 60s
- `code=50100` 用 `postWithBusinessCode` 处理，不走普通 `request.post` unwrap

---

## 4. 版本历史

| 版本 | 日期 | 说明 |
| --- | --- | --- |
| V1.0 | 2026-06-25 | 初始契约（F015 全局方案解释） |
