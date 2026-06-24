# API 契约文档 - P1-1 阶段：调度展示优化

> **阶段目标**：对全局调度、节点调度、实体 detail 的 API 响应进行展示优化，包括 score 归一化、节点名称返回、货物描述补充、新增 dispatches 查询端点。
>
> **分支**：`backend/p1-1`
>
> **联调门槛**：扩展后的 DTO 可在 Swagger 中自测通过；前端可根据 node_name、score_display、货物描述字段进行展示优化。

---

## 1. 变更概览

| 编号 | 功能 | 涉及端点 / Schema | 变更类型 |
| --- | --- | --- | --- |
| P1-05 | F007 score 归一化 | `GET /api/schedule/global`、`GET /api/schedule/global/{code}` | 响应新增 `score_display` |
| P1-06 | 全局方案 DTO 优化 | `GET /api/schedule/global/{code}` | `goods_schedules` 格式变更 |
| P1-07 | 节点调度 DTO 优化 | `GET /api/schedule/batches/{code}`、`GET /api/schedule/batches/{batch_code}/dispatches` 等 | 响应新增 `node_name`、`package_details`；新增 3 个端点 |

---

## 2. 响应字段变更（按端点）

### 2.1 `GET /api/schedule/global`（全局方案列表）

**变更**：每个 items 元素新增 `score_display` 字段。

**响应示例**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "schedule_code": "GS20260609001",
        "total_distance": 1250.5,
        "total_time": 36.2,
        "total_goods": 50,
        "score": 1250.75,
        "score_display": 85,
        "package_count": 50,
        "version": 1,
        "is_replan": false,
        "created_at": "2026-06-09T10:30:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  },
  "meta": { "degraded": false, "degraded_reason": null }
}
```

**字段说明**：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `score` | float | 原始加权值（越小越好），保留向后兼容 |
| `score_display` | int | 归一化百分制（0~100，**越高越好**）；公式：`100 - min(100, raw_score / max_possible × 100)`；`max_possible` 为历史最大 score（内存缓存，首次查询 DB） |

---

### 2.2 `GET /api/schedule/global/{schedule_code}`（全局方案详情）

**变更**：
1. 新增 `score_display` 字段（同列表）
2. `goods_schedules` 格式变更（P1-06）

**`goods_schedules` 新格式**（P1-06）：

原格式（`path` 为字符串数组）：

```json
{
  "goods_code": "G001",
  "order_code": "O001",
  "path": ["SC001", "SO001", "SO027"]
}
```

新格式（`path` 改为含 `node_name` 的对象数组；新增货物描述字段）：

```json
{
  "goods_code": "G001",
  "goods_name": "电子元件",
  "goods_type": "电子",
  "weight": 12.5,
  "volume": 0.8,
  "node_code": "SC001",
  "order_code": "O001",
  "path": [
    { "node_code": "SC001", "node_name": "武汉存储中心" },
    { "node_code": "SO001", "node_name": "华中分拣中心" },
    { "node_code": "SO027", "node_name": "光谷0级分拣中心" }
  ]
}
```

**响应示例**（部分）：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "schedule_code": "GS20260609001",
    "total_distance": 1250.5,
    "total_time": 36.2,
    "total_goods": 50,
    "score": 1250.75,
    "score_display": 85,
    "package_count": 50,
    "version": 1,
    "is_replan": false,
    "goods_schedules": [ {"/* 见上 */"} ],
    "packages": [ {"/* 同 MVP */"} ],
    "created_at": "2026-06-09T10:30:00"
  },
  "meta": { "degraded": false, "degraded_reason": null }
}
```

---

### 2.3 `GET /api/schedule/batches/{batch_code}`（调度批次详情）

**变更**（P1-07）：
1. 支持过滤参数：`vehicle_code`、`level_phase`
2. `dispatches[].tasks[]` 新增 `from_node_name`、`to_node_name`
3. `dispatches[].tasks[].package_codes` 展开为 `package_details`（含货物详情）

**请求参数**（新增）：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `vehicle_code` | string | 否 | 按车辆编码过滤 dispatches |
| `level_phase` | int | 否 | 按层级阶段过滤（0=L0→L1，1=L1→L2） |

**`tasks` 新格式**（P1-07）：

原格式：

```json
{
  "from_node_code": "SC001",
  "to_node_code": "SO001",
  "package_codes": ["PKG001", "PKG002"],
  "is_return": false
}
```

新格式（新增 `from_node_name`、`to_node_name`；`package_codes` 展开为 `package_details`）：

```json
{
  "from_node_code": "SC001",
  "from_node_name": "武汉存储中心",
  "to_node_code": "SO001",
  "to_node_name": "华中分拣中心",
  "package_details": [
    {
      "package_code": "PKG001",
      "weight": 12.5,
      "volume": 0.8,
      "goods_items": [
        {
          "goods_code": "G001",
          "goods_name": "电子元件",
          "goods_type": "电子",
          "order_code": "O001"
        }
      ]
    }
  ],
  "is_return": false
}
```

**响应示例**（部分）：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "batch_code": "DB001",
    "schedule_code": "GS20260609001",
    "status": "completed",
    "unallocated_packages": [],
    "dispatches": [ {"/* 见上 */"} ]
  },
  "meta": { "degraded": false, "degraded_reason": null }
}
```

---

## 3. 新增端点

### 3.1 `GET /api/schedule/batches/{batch_code}/dispatches`（按批次查询调度明细）

**功能**：查询指定批次下的所有调度明细，支持按车辆、层级阶段过滤。

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `batch_code`（路径） | string | 是 | 批次编码 |
| `vehicle_code` | string | 否 | 按车辆编码过滤 |
| `level_phase` | int | 否 | 按层级阶段过滤（0=L0→L1，1=L1→L2） |

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [ {"/* 同 2.3 的 dispatches 元素 */"} ],
    "total": 5
  },
  "meta": { "degraded": false, "degraded_reason": null }
}
```

---

### 3.2 `GET /api/schedule/{schedule_code}/dispatches`（按方案查询所有调度明细）

**功能**：查询指定方案下所有批次的调度明细（跨批次），支持按车辆、层级阶段过滤。

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `schedule_code`（路径） | string | 是 | 调度方案编码 |
| `vehicle_code` | string | 否 | 按车辆编码过滤 |
| `level_phase` | int | 否 | 按层级阶段过滤（0=L0→L1，1=L1→L2） |

**响应格式**：同 3.1。

---

### 3.3 `GET /api/schedule/dispatches/{dispatch_code}`（查询单个调度明细详情）

**功能**：查询单个调度明细的详情。

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `dispatch_code`（路径） | string | 是 | 调度明细编码 |

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "dispatch_code": "DP001",
    "batch_code": "DB001",
    "vehicle_code": "V001",
    "driver_code": "D001",
    "level_phase": 0,
    "tasks": [ {"/* 同 2.3 的 tasks 元素 */"} ],
    "total_distance": 125.5,
    "total_time": 36.2
  },
  "meta": { "degraded": false, "degraded_reason": null }
}
```

---

## 4. 错误码（新增）

| 错误码 | HTTP 状态码 | 说明 |
| --- | --- | --- |
| 40401 | 404 | 调度方案不存在（`GET /schedule/{schedule_code}/dispatches`） |
| 40402 | 404 | 调度批次不存在（已有） |
| 40403 | 404 | 调度明细不存在（`GET /dispatches/{dispatch_code}`） |

---

## 5. 自测清单

- [ ] `GET /schedule/global` 返回 `score_display`（0~100）
- [ ] `GET /schedule/global/{code}` 返回 `score_display`；`goods_schedules.path` 含 `node_name`；货物描述字段齐全
- [ ] `GET /schedule/batches/{code}` 返回 `tasks[].from_node_name`、`to_node_name`；`package_details` 展开正确
- [ ] `GET /schedule/batches/{code}?vehicle_code=V001` 过滤生效
- [ ] `GET /schedule/batches/{code}?level_phase=0` 过滤生效
- [ ] `GET /schedule/batches/{batch_code}/dispatches` 返回 dispatches 列表
- [ ] `GET /schedule/{schedule_code}/dispatches` 返回跨批次的 dispatches 列表
- [ ] `GET /schedule/dispatches/{dispatch_code}` 返回单个详情
- [ ] 各实体 detail 接口 200（P1-10 不做补充）

---

## 6. 联调说明

- **前端**：可根据 `node_name`、`score_display`、货物描述字段进行展示优化；新增 3 个端点可按批次/方案/单个查询调度明细。
- **向后兼容**：`score` 字段保留；`goods_schedules.path` 格式变更是 **breaking change**，需前端同步适配。
- **演示数据**：使用 `scripts/init_demo_data.py` 重新初始化，或沿用 MVP 演示数据。

---

*文档版本：V1.0 &lt;br&gt;
*创建日期：2026-06-24 &lt;br&gt;
*负责人：后端开发（同学 A）*
