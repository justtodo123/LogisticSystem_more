# P1-3（节点到货确认 P1-08）API 契约文档

**版本**：v1.0  
**创建日期**：2026-06-09  
**对应阶段**：P1-3（节点到货确认）  
**实现状态**：⏳ 待实现  
**业务设计**：[P1开发计划 §1.4](../P1开发计划.md#14-p1-08-节点到货确认已对齐)

---

## 1. 文档概述

### 1.1 目的

定义 **节点到货确认**（单包裹正常/异常）的 API，修正货物 → 下游预生成包裹的状态级联。

**与 MVP 边界**：

| 项 | 说明 |
| --- | --- |
| **新增** | 本契约接口 + 前端新页「节点到货确认」 |
| **不改** | `ExceptionList`、F013 replan、`POST /api/exceptions` 重规划主流程 |
| **改造** | `POST /api/simulation/deliver` 的 L1 激活逻辑；F005 分配过滤 `exception` 包裹 |

### 1.2 API 列表

| 路径 | 方法 | 说明 | 状态 |
| --- | --- | --- | --- |
| `/api/simulation/arrival-packages` | GET | 查询某节点待确认的到站包裹 | ⏳ |
| `/api/simulation/confirm-arrival` | POST | 批量确认到站包裹（正常/异常） | ⏳ |

> **说明**：挂在 `/api/simulation` 下与 F013-1 模拟送达同属状态流转；也可独立为 `/api/node-arrival/*`，实现时二选一并在 OpenAPI 保持一致即可。

### 1.3 通用约定

- **Base URL**：`http://localhost:8000/api`
- **认证**：Bearer Token（`dispatcher`）
- **响应**：`{ code, message, data, meta? }`
- **状态枚举**：`pending_pack` | `packed` | `in_transit` | `delivered` | `exception`

---

## 2. 业务规则（实现必遵）

### 2.1 查询范围

「待确认到站包裹」= 同一 `schedule_code` 下，满足：

- `status = in_transit`
- `to_node_id` = 所选节点
- 尚未在本节点完成到货确认（可选：增加 `arrival_confirmed_at` 字段，或用 `delivered`/`exception` 终态表示已确认）

### 2.2 确认「正常」

对包裹 `P`（`in_transit`）在节点 `N` 确认正常：

1. `P.status` → `delivered`
2. 对 `P.goods_items` 中每件货物 `G`：
   - 更新 `G.node_id = N`
   - 若 `G.node_id == order.destination_node_id` → `G.status = delivered`
   - 否则 → `G.status = packed`
   - **仅对 status 变为 `packed` 的 G**：查找同 `schedule_id`、F021 预生成、`from_node_id = N`、`goods_items` 含 `G.goods_code`、且 `status = pending_pack` 的下游包裹 → `packed`
3. 订单：若该订单所有货物 `delivered` → `completed`；否则保持 `delivering`

### 2.3 确认「异常」

对包裹 `P` 确认异常：

1. `P.status` → `exception`
2. `P` 内所有货物 → `exception`
3. **级联下游**：同 `schedule_id` 下，`goods_items` 含任一异常货物 code、且状态为 `pending_pack` 或 `packed` 的预生成包裹 → `exception`
4. 涉及订单：任一货物 `exception` → 订单 `delivering` → `exception`

### 2.4 与 F005 / deliver 的约束

| 场景 | 规则 |
| --- | --- |
| F005 分配 | 仅 `status = packed` 且 **非** `exception` 的包裹可进入 `in_transit` |
| `POST /simulation/deliver` | 不得处理 `exception` 包裹；不得将 `exception` 货物改为 `delivered` |
| L1→L2 终点送达 | 仅处理 `in_transit` 且非 `exception` 的包裹 |

### 2.5 MVP 缺陷对照（本 P1 修复）

当前 `simulation_service.deliver_packages` 在 L0→L1 中间节点送达时，会将 `from_node_id = to_node` 的 **全部** `pending_pack` 包裹激活为 `packed`，**未按货物过滤**。P1-3 应改为 **步骤 2.2 按货物级联**，且 L0→L1 到站确认改走 `confirm-arrival`，避免与旧逻辑冲突。

---

## 3. API 详细设计

### 3.1 GET /api/simulation/arrival-packages

#### 功能

列出指定全局方案、指定节点下，**待工作人员确认** 的到站包裹（`in_transit`）。

#### 请求

**Query**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `schedule_code` | string | 是 | 全局方案编号 |
| `node_code` | string | 是 | 到站节点编号（如 n_2 / SO001） |

**示例**：

```http
GET /api/simulation/arrival-packages?schedule_code=GS20260609001&node_code=SO001
Authorization: Bearer <token>
```

#### 响应 200

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "schedule_code": "GS20260609001",
    "node_code": "SO001",
    "node_name": "分拣中心一号",
    "packages": [
      {
        "package_code": "PKG_C",
        "from_node_code": "SC001",
        "to_node_code": "SO001",
        "status": "in_transit",
        "level_phase": 0,
        "goods_items": [
          { "goods_code": "G001", "order_code": "O001", "goods_name": "货物g_1" }
        ]
      },
      {
        "package_code": "PKG_D",
        "from_node_code": "SC001",
        "to_node_code": "SO001",
        "status": "in_transit",
        "level_phase": 0,
        "goods_items": [
          { "goods_code": "G002", "order_code": "O002", "goods_name": "货物g_2" }
        ]
      }
    ]
  }
}
```

#### 错误

| code | 说明 |
| --- | --- |
| 40001 | 参数缺失或方案/节点不存在 |
| 40300 | 非 dispatcher |

---

### 3.2 POST /api/simulation/confirm-arrival

#### 功能

对同一节点的一批到站包裹，逐条确认 **正常** 或 **异常**，单事务提交级联更新。

#### 请求体

```json
{
  "schedule_code": "GS20260609001",
  "node_code": "SO001",
  "items": [
    { "package_code": "PKG_C", "result": "normal" },
    {
      "package_code": "PKG_D",
      "result": "exception",
      "exception_subtype": "damaged",
      "remark": "节点未收到货物"
    }
  ]
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `schedule_code` | string | 是 | 全局方案编号 |
| `node_code` | string | 是 | 到站节点 |
| `items` | array | 是 | 至少 1 条 |
| `items[].package_code` | string | 是 | 须为 `in_transit` 且 `to_node` 匹配 |
| `items[].result` | string | 是 | `normal` \| `exception` |
| `items[].exception_subtype` | string | 否 | `result=exception` 时建议填写 |
| `items[].remark` | string | 否 | 备注 |

#### 响应 200

```json
{
  "code": 0,
  "message": "到站确认成功",
  "data": {
    "schedule_code": "GS20260609001",
    "node_code": "SO001",
    "normal_packages": ["PKG_C"],
    "exception_packages": ["PKG_D"],
    "activated_downstream_packages": ["PKG_E"],
    "cascade_exception_packages": ["PKG_F"],
    "updated_goods": [
      { "goods_code": "G001", "status": "packed" },
      { "goods_code": "G002", "status": "exception" }
    ],
    "updated_orders": [
      { "order_code": "O001", "status": "delivering" },
      { "order_code": "O002", "status": "exception" }
    ]
  }
}
```

#### 错误

| code | 说明 |
| --- | --- |
| 40001 | 包裹状态非 `in_transit`、不属于该节点、或已确认 |
| 40002 | 同一请求中重复 `package_code` |
| 40300 | 非 dispatcher |

#### 可选：审计记录

可在成功后 **可选** 写入 `exception_events`（`exception_type=package`）用于追溯，**不自动触发 F013 replan**。

---

## 4. 演示验收用例（C/D/E/F 场景）

前置：F007+F021 完成，C/D `in_transit`，E/F `pending_pack`（见开发计划 §1.4.3）。

| 步骤 | 操作 | 断言 |
| --- | --- | --- |
| 1 | `confirm-arrival`：C=normal，D=exception | E=`packed`，F=`exception`，g_2=`exception`，O_2=`exception` |
| 2 | F005 L1→L2 | 仅 E → `in_transit`；F 仍为 `exception` |
| 3 | `simulation/deliver`（L1→L2） | g_1=`delivered`；g_2、F 仍为 `exception` |

---

## 5. 前端页面要点

| 项 | 说明 |
| --- | --- |
| 路由 | 建议 `/arrival-confirm` 或 `/simulation/arrival` |
| 流程 | 选 `schedule_code` → 选 `node_code` → GET 列表 → 每行 Radio 正常/异常 → POST 提交 |
| 展示 | 包裹内货物、订单号；异常时可填 subtype/remark |
| 与 MVP | 侧栏新增入口；`ExceptionList` 保留不变 |

---

## 6. 版本历史

| 版本 | 日期 | 修改内容 |
| --- | --- | --- |
| v1.0 | 2026-06-09 | 初版：节点到货确认 API + 级联规则 |
