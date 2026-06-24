# API 契约文档 · P1-2 全局调度增强

| 字段 | 值 |
| --- | --- |
| **阶段** | P1-2（必做） |
| **功能编号** | P1-03 |
| **文档版本** | V1.0 |
| **创建日期** | 2026-06-24 |
| **参考文档** | [P1-2开发文档-全局调度增强.md](../My_doc/P1-2开发文档-全局调度增强.md) |

---

## 1. 概述

P1-2 为全局调度增加**预览 → 确认**两步流：
- **预览模式**：生成调度方案（F007），仅存入 `global_schedules` 表（status=draft），不执行 F021 打包，不更新订单/货物/包裹状态
- **确认接口**：用户确认后，执行完整 F007 + F021 落库流程（与 MVP 一致），状态更新为 active
- **丢弃接口**：允许用户手动丢弃未确认的 draft 方案
- **列表过滤**：`GET /api/schedule/global` 默认过滤掉 status=draft 的方案

---

## 2. 接口契约

### 2.1 预览调度方案

**接口**：`POST /api/schedule/global`  
**描述**：生成调度方案预览（F007），写入 `global_schedules`（status=draft），不执行 F021，不改订单/货物状态。

#### Request Body

```json
{
  "order_codes": ["O001", "O002"],  // 可选；不传则自动筛选 status=pending 订单
  "algorithm": "traditional",         // ✅ 必填
  "preview": true                      // ✅ 必填：预览模式
}
```

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `order_codes` | `List[str]` | 否 | 订单编号列表；不传则处理所有 `status=pending` 订单 |
| `algorithm` | `str` | **是** | 算法类型：`traditional` / `deepseek` |
| `preview` | `bool` | **是** | `true`=预览模式；P1-2 已移除直接落库功能，必须传 `true` |

> ⚠️ **P1-2 breaking change**：不再支持无 `preview` 参数的直接落库。前端必须先 preview → confirm。

#### Response（成功）

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "schedule_code": "GS20260624001",
    "total_distance": 1234.5,
    "total_time": 23.5,
    "total_goods": 15,
    "score": 567.8,
    "score_display": 85,
    "package_count": 0,
    "version": 1,
    "is_replan": false,
    "status": "draft"
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

#### Response（业务失败）

```json
{
  "code": 40001,
  "message": "全局调度失败: 无法为某货物找到满足条件的 L1 节点",
  "data": null,
  "meta": { "degraded": false, "degraded_reason": null }
}
```

#### Response（重复调度错误）

```json
{
  "code": 40002,
  "message": "订单 O001 已有活跃的调度方案，请先完成或丢弃现有方案",
  "data": null,
  "meta": { "degraded": false, "degraded_reason": null }
}
```

---

### 2.2 确认调度方案

**接口**：`POST /api/schedule/confirm/{schedule_code}`  
**描述**：确认 draft 方案，执行 F021 打包 + 状态更新（与 MVP 一致）。

#### Path Parameters

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `schedule_code` | `str` | draft 方案的调度编号 |

#### Response（成功）

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "schedule_code": "GS20260624001",
    "total_distance": 1234.5,
    "total_time": 23.5,
    "total_goods": 15,
    "score": 567.8,
    "score_display": 85,
    "package_count": 8,
    "version": 1,
    "is_replan": false,
    "status": "active"
  },
  "meta": { "degraded": false, "degraded_reason": null }
}
```

#### Response（订单状态已变化）

```json
{
  "code": 40003,
  "message": "订单 O001 状态已变化（当前: completed），请重新预览",
  "data": null,
  "meta": { "degraded": false, "degraded_reason": null }
}
```

#### Response（confirm 失败，draft 已删除）

```json
{
  "code": 50001,
  "message": "确认失败，draft 已丢弃，请重新预览",
  "data": null,
  "meta": { "degraded": false, "degraded_reason": null }
}
```

---

### 2.3 丢弃 draft 方案

**接口**：`DELETE /api/schedule/draft/{schedule_code}`  
**描述**：手动丢弃未确认的 draft 方案。

#### Path Parameters

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `schedule_code` | `str` | draft 方案的调度编号 |

#### Response（成功）

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "schedule_code": "GS20260624001",
    "status": "discarded"
  },
  "meta": { "degraded": false, "degraded_reason": null }
}
```

> ⚠️ `"discarded"` 是**瞬态响应值**，不写入数据库。draft 被物理删除后，`status: "discarded"` 仅用于告知前端操作结果。

#### Response（方案不存在或非 draft）

```json
{
  "code": 40401,
  "message": "draft 方案不存在或已确认: GS20260624001",
  "data": null,
  "meta": { "degraded": false, "degraded_reason": null }
}
```

---

### 2.4 全局方案列表（变更）

**接口**：`GET /api/schedule/global`  
**变更**：默认过滤 `status=draft`，仅返回 `status=active` 的方案。

#### Query Parameters（新增）

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `status` | `str` | 否 | 按状态筛选：`active` / `draft`；默认 `active` |

#### Response（新增 `status` 字段）

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "schedule_code": "GS20260623001",
        "total_distance": 1234.5,
        "total_time": 23.5,
        "total_goods": 15,
        "score": 567.8,
        "score_display": 85,
        "package_count": 8,
        "version": 1,
        "is_replan": false,
        "status": "active",              // ✅ 新增
        "created_at": "2026-06-23T10:30:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  },
  "meta": { "degraded": false, "degraded_reason": null }
}
```

---

## 3. 错误码表

| 错误码 | 说明 |
| --- | --- |
| 40000 | 参数校验失败 |
| 40001 | 全局调度失败（业务错误） |
| 40002 | 已有活跃方案，不允许重复调度 |
| 40003 | 订单状态已变化，请重新预览 |
| 40401 | draft 方案不存在或已确认 |
| 50001 | 确认失败，draft 已丢弃 |

---

## 4. 测试要点

| 测试项 | 预期结果 |
| --- | --- |
| 预览成功 | preview=True 后，`global_schedules` 中 `status=draft`，订单状态不变 |
| 预览返回 schedule_code | 响应含 `schedule_code` 和 `status: "draft"` |
| 确认成功 | confirm 后 `status=active`，订单 `delivering`，包裹 `packed` |
| 确认失败（订单状态变化） | 订单状态变化后 confirm 报错，draft 被删除 |
| 确认失败（异常） | confirm 异常时 draft 被删除，需重新 preview |
| 丢弃 draft | DELETE draft 后记录被删除 |
| 丢弃非 draft 失败 | 对 active 方案调用 DELETE 返回 40401 |
| 列表默认过滤 draft | GET `/global` 默认不返回 `status=draft` 的方案 |
| 列表按状态筛选 | GET `/global?status=draft` 可查 draft 方案 |
| 重复预览失败 | 对同一批订单重复 preview 返回 40002 |

---

## 5. 版本历史

| 版本 | 日期 | 说明 |
| --- | --- | --- |
| V1.0 | 2026-06-24 | 初版：P1-2 全局调度增强 API 契约 |
