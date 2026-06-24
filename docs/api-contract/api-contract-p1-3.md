# P1-3（节点到货确认 P1-08）API 契约文档

**版本**：v1.1  
**创建日期**：2026-06-09  
**最后更新**：2026-06-25  
**对应阶段**：P1-3（节点到货确认）  
**实现状态**：✅ 已完成  
**业务设计**：[P1-3 开发文档](../../My_doc/P1-3开发文档.md)

---

## 1. 文档概述

### 1.1 目的

定义 **节点到货确认**（单包裹/批量正常/异常）的 API，驱动 L1→L2 包裹动态生成与状态级联。

**与 MVP 边界**：

| 项 | 说明 |
| --- | --- |
| **新增** | 本契约接口 + 前端新页「节点到货确认」 |
| **不改** | `ExceptionList`、F013 replan、`POST /api/exceptions` 重规划主流程 |
| **改造** | F021 打包：初始仅生成 L0→L1 包裹；L1→L2 包裹在 confirm-arrival 后由 `_trigger_repacking` 动态生成 |
| **改造** | `POST /api/simulation/deliver`：goods.status 保持 `in_transit`，仅更新 node_id |

### 1.2 API 列表

| 路径 | 方法 | 说明 | 状态 |
| --- | --- | --- | --- |
| `/api/simulation/arrival-packages` | GET | 查询某调度方案待确认的到站包裹 | ✅ |
| `/api/simulation/confirm-arrival` | POST | 单个到货确认（正常/异常） | ✅ |
| `/api/simulation/confirm-arrival-batch` | POST | 批量到货确认（事务性，任一失败则全部回滚） | ✅ |

> **说明**：挂在 `/api/simulation` 下与 F013-1 模拟送达同属状态流转，路由定义在 `api/arrival_confirm.py`，核心逻辑在 `services/arrival_confirm_service.py`。

### 1.3 通用约定

- **Base URL**：`http://localhost:8000/api`
- **认证**：无需认证（`GET/POST` 均未加 `Depends(get_current_user)`）
- **响应**：`{ code, message, data, meta? }`
- **状态枚举**：`pending_pack` | `packed` | `in_transit` | `delivered` | `exception`

---

## 2. 业务规则（实现必遵）

### 2.1 查询范围

「待确认到站包裹」= 同一 `schedule_code` 下，满足：

- `status IN ("in_transit", "delivered")`
- 可选过滤：`node_code`（不传则查所有）

### 2.2 单个确认 — 正常路径

对包裹 `P` 确认正常（`is_normal=true`）：

1. `P.status` → `delivered`（调用 `transition_package_status`）
2. 对 `P.goods_items` 中每件货物 `G`：
   - 若 `G.node_id == order.destination_node_id` → `G.status = delivered`
   - 否则 → `G.status = pending_pack`
3. **所有货物状态更新后**，调用 `_trigger_repacking(db, schedule_code)`：
   - 按 `goods_schedules` 中的 `path` 找到货物当前节点之后的下一个节点
   - 按 `order_code` 分组同订单的 `pending_pack` 货物，生成 L1→L2 包裹（`status=packed`）
   - 将参与打包的货物状态从 `pending_pack` 更新为 `packed`
4. 检查订单是否完成：若该订单所有货物 `delivered` → `completed`

> ⚠️ **关键**：`_trigger_repacking` 在 for 循环**外部**调用一次，确保所有同订单货物被正确分组到同一个 L1→L2 包裹。调用前需 `db.flush()` 确保 `pending_pack` 状态已写入（因为 `sessionmaker` 配置了 `autoflush=False`）。

### 2.3 单个确认 — 异常路径

对包裹 `P` 确认异常（`is_normal=false`）：

1. `P.status` → `exception`
2. `P` 内所有货物 → `exception`
3. 关联订单 → `exception`（订单标记异常，但其他货物可继续流转）
4. 写入 `exception_events`（审计用，`exception_type="package"`，不自动触发 replan）
5. **不触发** `_trigger_repacking`

### 2.4 批量确认（事务性）

`confirm_arrival_batch` 包装单个确认：

1. **预校验**：遍历所有包裹，检查包裹存在性
2. **事务性**：逐条调用 `confirm_arrival`（单个确认逻辑）
3. **任一失败则全部回滚**：`db.rollback()` 后返回错误列表
4. 成功时统一 `db.commit()`

### 2.5 P1-3 与 MVP 的关键差异

| 维度 | MVP | P1-3 |
| --- | --- | --- |
| F021 打包时机 | 初始 F007 后生成所有包裹 | 初始仅生成 L0→L1，L1→L2 在 confirm-arrival 后由 `_trigger_repacking` 生成 |
| `deliver` 后 goods 状态 | `in_transit → packed` | `in_transit`（不变），仅更新 `node_id` |
| 下游包裹激活 | deliver 内批量激活（按节点）| confirm-arrival 按货物精确匹配触发 `_trigger_repacking` |
| 异常入口 | 无 | `confirm-arrival`（is_normal=false） |
| 审计日志 | 无 | 异常时写入 `exception_events` |

---

## 3. API 详细设计

### 3.1 GET /api/simulation/arrival-packages

#### 功能

列出指定全局方案下，待确认的到站包裹（`in_transit` 或 `delivered`）。

#### 请求

**Query**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `schedule_code` | string | 是 | 全局方案编号 |
| `node_code` | string | 否 | 到站节点编号（不传则查所有） |

**示例**：

```http
GET /api/simulation/arrival-packages?schedule_code=GS20260625001
Authorization: Bearer <token>
```

#### 响应 200

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "package_code": "PKG202606250001",
      "schedule_code": "GS20260625001",
      "from_node_code": "SC004",
      "to_node_code": "L1001",
      "status": "delivered",
      "arrived_at": "2026-06-25T01:30:00"
    },
    {
      "package_code": "PKG202606250002",
      "schedule_code": "GS20260625001",
      "from_node_code": "SC003",
      "to_node_code": "L1001",
      "status": "delivered",
      "arrived_at": "2026-06-25T01:30:00"
    }
  ],
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

#### 错误

| code | 说明 |
| --- | --- |
| — | 查询失败返回 `code=50000` + 错误信息 |

---

### 3.2 POST /api/simulation/confirm-arrival

#### 功能

对单个包裹进行到站确认（正常或异常），触发级联状态更新。

#### 请求体

```json
{
  "schedule_code": "GS20260625001",
  "package_code": "PKG001",
  "is_normal": true,
  "exception_subtype": null,
  "remark": null
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `schedule_code` | string | 是 | 调度方案编号 |
| `package_code` | string | 是 | 到站包裹编号 |
| `is_normal` | boolean | 是 | 是否正常到站 |
| `exception_subtype` | string | 否 | 异常子类型（`is_normal=false` 时建议填写，如 `damaged`） |
| `remark` | string | 否 | 备注 |

#### 响应 200（正常）

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "package_status": "delivered",
    "goods_status": "pending_pack",
    "triggered_repacking": true,
    "new_package_code": "PKG17823230982740"
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

| 字段 | 说明 |
| --- | --- |
| `package_status` | 包裹最终状态（正常=`delivered`，异常=`exception`） |
| `goods_status` | 货物状态（正常未到目的地=`pending_pack`，已到=`delivered`） |
| `triggered_repacking` | 是否触发了 F021 重新打包 |
| `new_package_code` | 若触发重新打包，返回新生成的 L1→L2 包裹编号 |

#### 响应 200（异常）

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "package_status": "exception",
    "goods_status": "exception",
    "order_status": "exception",
    "triggered_repacking": false,
    "new_package_code": null
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

#### 错误

| code | 说明 |
| --- | --- |
| 404 | 包裹不存在 |
| 50000 | 到货确认失败（含业务错误，如包裹状态不正确等） |

---

### 3.3 POST /api/simulation/confirm-arrival-batch

#### 功能

批量确认同一调度方案下的一批包裹，**事务性**（任一失败则全部回滚）。

#### 请求体

```json
{
  "schedule_code": "GS20260625001",
  "confirmations": [
    {
      "package_code": "PKG001",
      "is_normal": true
    },
    {
      "package_code": "PKG002",
      "is_normal": false,
      "exception_subtype": "damaged",
      "remark": "包裹破损"
    }
  ]
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `schedule_code` | string | 是 | 调度方案编号（所有包裹必须属于该方案） |
| `confirmations` | array | 是 | 确认列表 |
| `confirmations[].package_code` | string | 是 | 包裹编号 |
| `confirmations[].is_normal` | boolean | 是 | 是否正常到站 |
| `confirmations[].exception_subtype` | string | 否 | 异常子类型（`is_normal=false` 时建议填写） |
| `confirmations[].remark` | string | 否 | 备注 |

#### 响应 200（全部成功）

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 2,
    "success_count": 2,
    "failed_count": 0,
    "results": [
      {
        "package_code": "PKG001",
        "status": "delivered",
        "goods_status": "pending_pack",
        "triggered_repacking": true,
        "new_package_code": "PKG003"
      },
      {
        "package_code": "PKG002",
        "status": "exception",
        "goods_status": "exception",
        "order_status": "exception"
      }
    ],
    "errors": null
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

#### 响应 200（失败，已回滚）

```json
{
  "code": 50000,
  "message": "批量到货确认失败：包裹 XXX 不存在",
  "data": null,
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

> **事务性**：若任一包裹确认失败，全部回滚，返回错误。失败不打印 `success_count`/`failed_count` 细分。

---

## 4. 完整调用流程

### 4.1 正常流程（全部正常）

```
┌──────────────────────────────────────────────────────────┐
│ Step 1  POST /api/schedule/global (preview=true)          │
│         → draft 方案，goods.schedules 含 L0→L1→L2 路径    │
├──────────────────────────────────────────────────────────┤
│ Step 2  POST /api/schedule/confirm/{schedule_code}        │
│         → F021 打包，仅生成 L0→L1 包裹（packed）          │
├──────────────────────────────────────────────────────────┤
│ Step 3  POST /api/schedule/node-dispatch (demo_mode=false)│
│         → F005 L0→L1：包裹 in_transit，货物 in_transit    │
├──────────────────────────────────────────────────────────┤
│ Step 4  POST /api/simulation/deliver                      │
│         → 包裹 delivered，货物 in_transit（不变）          │
│         → 仅更新 goods.node_id = to_node_id               │
├──────────────────────────────────────────────────────────┤
│ Step 5  GET /api/simulation/arrival-packages              │
│         → 查询 delivered 包裹列表                          │
├──────────────────────────────────────────────────────────┤
│ Step 6  POST /api/simulation/confirm-arrival-batch        │
│         → 全部 is_normal=true                             │
│         → goods: in_transit → pending_pack                │
│         → _trigger_repacking 生成 L1→L2 包裹（packed）    │
│         → goods: pending_pack → packed                    │
├──────────────────────────────────────────────────────────┤
│ Step 7  POST /api/schedule/node-dispatch (demo_mode=false)│
│         → F005 L1→L2：新包裹 in_transit                   │
├──────────────────────────────────────────────────────────┤
│ Step 8  POST /api/simulation/deliver                      │
│         → 包裹到达 L2 目的地，delivered                    │
├──────────────────────────────────────────────────────────┤
│ Step 9  POST /api/simulation/confirm-arrival-batch        │
│         → goods: in_transit → delivered (已到目的地)       │
│         → order: delivering → completed                   │
└──────────────────────────────────────────────────────────┘
```

### 4.2 混合流程（部分异常）

以 O_1=正常、O_2=异常为例：

```
Step 1-4: 同正常流程
Step 5:   GET arrival-packages → [C(L0→L1/O_1), D(L0→L1/O_2)]
Step 6:   confirm-arrival-batch:
           C: is_normal=true  → goods pending_pack → _trigger_repacking → 新包裹 E'(L1→L2)
           D: is_normal=false → goods/order exception, 写入 exception_events
Step 7:   F005 L1→L2: 仅 E' 被调度（D 的货物已 exception 不参与打包）
Step 8-9: E' 送达 L2，确认 → O_1 completed，O_2 仍 exception
```

---

## 5. 代码实现文件

| 文件 | 说明 |
| --- | --- |
| `services/arrival_confirm_service.py` | 到货确认核心服务（confirm_arrival / confirm_arrival_batch / _trigger_repacking / get_arrival_packages） |
| `api/arrival_confirm.py` | 到货确认 API 路由（3 个端点） |
| `schemas/arrival_confirm.py` | Pydantic 模型（ArrivalConfirmRequest / BatchArrivalConfirmRequest / 响应模型） |
| `algorithms/packaging.py` | F021 打包算法（初始仅生成 L0→L1 包裹；`_trigger_repacking` 复用 `packing_service.repack_at_l1`） |
| `services/simulation_service.py` | 模拟送达（改造：goods.status 保持 in_transit，仅更新 node_id） |

### 无需改造文件

| 文件 | 原因 |
| --- | --- |
| `services/dispatch_service.py` | F005 算法层已过滤 `exception` 包裹 |
| `algorithms/node_dispatch.py` | 同上 |
| `services/replan_service.py` | P1-3 不触发 replan |

---

## 6. 前端页面要点

| 项 | 说明 |
| --- | --- |
| 路由 | 建议 `/arrival-confirm` 或 `/simulation/arrival` |
| 流程 | 选 `schedule_code` → GET 列表 → 每行 Radio 正常/异常 → POST 批量提交 |
| 展示 | 包裹编号、出发/目的节点、货物列表、订单号；异常时可填 subtype/remark |
| 与 MVP | 侧栏新增入口；`ExceptionList` 保留不变 |

---

## 7. 版本历史

| 版本 | 日期 | 修改内容 |
| --- | --- | --- |
| v1.0 | 2026-06-09 | 初版：节点到货确认 API + 级联规则 |
| v1.1 | 2026-06-25 | 匹配实际实现：修正 API 路径/请求体/响应体、新增 confirm-arrival-batch、更新业务规则（_trigger_repacking/deliver 改造）、标记已完成 |
