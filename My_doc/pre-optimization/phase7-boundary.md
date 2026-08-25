# 阶段7（异常与重规划 F013）边界定义

> **文档版本**：V1.0  
> **日期**：2026-06-22  
> **对应代码分支**：`backend/phase-7`  
> **状态**：✅ 已实现

---

## 1. 阶段目标

异常持久化 + 版本化重规划。当物流过程中发生节点故障或道路异常时，系统记录异常事件并通过版本链实现可追溯的重新调度。

---

## 2. 范围边界

### 2.1 包含（In Scope）

| 维度 | 内容 |
|------|------|
| **数据表** | `exception_events`（1 张新表，13 字段） |
| **API 端点** | 6 个（CRUD + replan + resolve） |
| **异常类型** | `road` → reroute，`node` → redispatch |
| **重规划** | redispatch（F007→F021→F005→F006）、reroute（仅 F006） |
| **版本链** | GlobalSchedule / DispatchBatch / NodeDispatch / Route 四张调度结果表的 version/parent_id/is_replan 字段 |
| **状态联动** | 创建异常时自动将关联订单/货物/包裹状态置为 `exception`；车辆异常自动 disable |
| **服务层** | `ExceptionService`（9 个方法）+ `ReplanService`（2 个方法） |
| **路由注册** | `main.py` 第 69-70 行注册 `exceptions_router` |
| **权限控制** | 读：login；写：dispatcher 角色 |
| **测试** | 29 个可执行 + 3 个占位 = 32 个核心测试 |

### 2.2 不包含（Out of Scope）

| 维度 | 说明 |
|------|------|
| **package 异常** | `exception_type=package`（包裹破损/丢失）已从 API 枚举移除，留后续版本 |
| **新算法** | 不创建新的调度或路径算法，仅组合调用已有服务 |
| **WebSocket** | 无实时推送异常通知 |
| **批量操作** | 不支持批量创建/解决异常 |
| **自动检测** | 异常不由系统自动触发（由用户通过 API 手动创建） |
| **修改现有服务** | 不修改 `ScheduleService` / `DispatchService` / `RouteService`（方案A） |
| **E2E 测试** | 未覆盖端到端测试 |
| **前端联调** | 待阶段7前端完成后联调 |
| **异常归档** | 无自动归档/清理策略 |
| **异常通知** | 无邮件/短信等外部通知 |

---

## 3. API 边界

### 3.1 端点一览

| # | 方法 | 路径 | 认证 | 角色 | 说明 |
|---|------|------|------|------|------|
| 1 | `GET` | `/api/exceptions` | Bearer | any | 分页列表，支持 status/exception_type 筛选 |
| 2 | `POST` | `/api/exceptions` | Bearer | dispatcher | 创建异常事件 |
| 3 | `GET` | `/api/exceptions/{event_code}` | Bearer | any | 单条详情 |
| 4 | `POST` | `/api/exceptions/{event_code}/replan` | Bearer | dispatcher | 触发重规划 |
| 5 | `PUT` | `/api/exceptions/{event_code}` | Bearer | dispatcher | 更新异常（状态/备注） |
| 6 | `PUT` | `/api/exceptions/{event_code}/resolve` | Bearer | dispatcher | 标记已解决 |

### 3.2 枚举约束

| 字段 | 允许值 | 备注 |
|------|--------|------|
| `exception_type` | `road` / `node` | `package` 已移除 |
| `exception_subtype` | `congestion` / `damage` / `road_closed` / `road_accident` / `capacity_limit` / `storage_timeout` / `node_maintenance` / `vehicle_breakdown` | — |
| `recommended_action` | `redispatch` / `reroute` | — |
| `target_type` | `node` / `route` / `vehicle` | — |

### 3.3 参数约束规则

| 条件 | 强制规则 |
|------|---------|
| `recommended_action=reroute` | `target_type` 必须为 `route`，`target_code` 必填 |
| `recommended_action=redispatch` | 建议 `target_type` 为 `node` 或 `vehicle`（非强制） |
| `exception_type` | 仅允许 `road` / `node` |
| `target_type`（若提供） | 仅允许 `node` / `route` / `vehicle` |

---

## 4. 数据模型边界

### 4.1 `exception_events` 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK 自增 | 内部主键 |
| `event_code` | VARCHAR(64) | UNIQUE, NOT NULL, INDEX | `EX` + 时间戳毫秒 |
| `exception_type` | VARCHAR(32) | NOT NULL | `road` / `node` |
| `exception_subtype` | VARCHAR(64) | NULLABLE | 子类型 |
| `target_type` | VARCHAR(32) | NULLABLE | `node` / `route` / `vehicle` |
| `target_code` | VARCHAR(64) | NULLABLE | 关联对象编号 |
| `recommended_action` | VARCHAR(32) | NOT NULL | `reroute` / `redispatch` |
| `related_schedule_code` | VARCHAR(64) | NULLABLE | 关联调度方案 |
| `replan_batch_code` | VARCHAR(64) | NULLABLE | 重规划后新批次编号 |
| `description` | TEXT | NOT NULL | 异常描述 |
| `status` | VARCHAR(32) | NOT NULL, DEFAULT `open` | `open` / `resolved` |
| `resolved_at` | DATETIME | NULLABLE | 解决时间（resolve 时自动设置） |
| `created_at` | DATETIME | NOT NULL, DEFAULT now | 创建时间 |

### 4.2 版本链字段（已存在于调度结果表）

以下四张表在阶段 6/7 前已具备版本链字段，阶段 7 利用它们实现重规划追溯：

| 表 | 版本链字段 |
|----|-----------|
| `global_schedules` | `version`, `parent_id`, `replan_reason`, `is_replan` |
| `dispatch_batches` | `version`, `parent_id`, `replan_reason`, `is_replan` |
| `node_dispatches` | `version`, `parent_id`, `replan_reason`, `is_replan` |
| `routes` | `version`, `parent_id`, `replan_reason`, `is_replan` |

---

## 5. 服务层边界

### 5.1 `ExceptionService` (exception_service.py)

**职责**：异常事件的 CRUD + 触发重规划入口

| 方法 | 可见性 | 说明 |
|------|--------|------|
| `_generate_event_code()` | 私有 | 生成业务编号 |
| `_to_response()` | 私有 | ORM → Pydantic 响应 |
| `_verify_target()` | 私有 | 校验 target_code 实体存在 |
| `create_exception_event()` | 公开 | 创建异常（含状态联动 + 车辆特殊处理） |
| `get_exception_events()` | 公开 | 分页列表查询 |
| `get_exception_event_by_code()` | 公开 | 详情查询 |
| `update_exception()` | 公开 | 更新异常状态/备注 |
| `resolve_exception()` | 公开 | 标记已解决（设置 resolved_at） |
| `trigger_replan()` | 公开 | 入口方法，按 action 分发至 ReplanService |

**不涉及**：通知推送、批量操作、异常自动检测。

### 5.2 `ReplanService` (replan_service.py)

**职责**：执行重规划逻辑，版本链管理

| 方法 | 说明 |
|------|------|
| `redispatch()` | 全链路重调度：F007→F021→F005→F006 |
| `reroute()` | 仅重路径规划：F006 |

**关键设计约束**（方案A）：
- **不修改** `ScheduleService`、`DispatchService`、`RouteService`
- 版本链逻辑完全在 `ReplanService` 内部实现
- 通过调用已有服务完成重规划

### 5.3 调用关系

```
ExceptionService.trigger_replan()
    ├── action=redispatch → ReplanService.redispatch()
    │       ├── ScheduleService (F007 → F021)
    │       ├── DispatchService (F005: L0→L1)
    │       ├── DispatchService (F005: L1→L2)
    │       └── RouteService (F006)
    │
    └── action=reroute → ReplanService.reroute()
            └── RouteService (F006)
```

---

## 6. 异常类型与重规划映射

### 6.1 Road 异常 → Reroute

| 属性 | 值 |
|------|-----|
| `exception_type` | `road` |
| `exception_subtype` | `congestion` / `damage` / `road_closed` / `road_accident` |
| `recommended_action` | `reroute` |
| `target_type` | **必须** `route` |
| `target_code` | **必填**（指定要重新规划的路线编号） |
| 重规划范围 | 仅 F006 路径规划 |
| 前置条件 | 节点调度已完成（Route 记录已存在） |

### 6.2 Node 异常 → Redispatch

| 属性 | 值 |
|------|-----|
| `exception_type` | `node` |
| `exception_subtype` | `capacity_limit` / `storage_timeout` / `node_maintenance` |
| `recommended_action` | `redispatch` |
| `target_type` | 建议 `node` |

### 6.3 Vehicle 异常 → Redispatch

| 属性 | 值 |
|------|-----|
| `exception_type` | `node`（vehicle 归属 node） |
| `exception_subtype` | `vehicle_breakdown` |
| `recommended_action` | `redispatch` |
| `target_type` | 建议 `vehicle` |
| 特殊处理 | 自动将车辆状态设为 `disabled`，按 `dispatch_id` 批量更新关联包裹和货物 |

---

## 7. 状态流转边界

### 7.1 异常事件自身状态

```
open ──→ resolved (resolve API 触发，设置 resolved_at)
```

- 已 `resolved` 的异常不可再次触发 replan
- 已 `resolved` 的异常不可再次 resolve

### 7.2 创建异常时的级联状态变更

当通过 `POST /api/exceptions` 创建异常事件时，系统自动：

| 关联实体 | 状态变更 |
|---------|---------|
| 关联 `schedule_code` 下的订单 | `delivering` → `exception` |
| 关联 `schedule_code` 下的货物 | `packed` / `in_transit` → `exception` |
| 关联 `schedule_code` 下的包裹 | `packed` / `in_transit` / `pending_pack` → `exception` |
| `target_type=vehicle` 的车辆 | 车辆 → `disabled`，关联包裹/货物批量更新 |

### 7.3 不触发的状态变更

- **不自动触发**重规划（需用户调用 replan API）
- **不自动通知**外部系统
- **不自动修改**节点状态（node_maintenance 不会自动将节点标记为不可用）

---

## 8. 测试边界

### 8.1 测试覆盖

| 类别 | 文件 | 方法数 | 状态 |
|------|------|--------|------|
| 单元测试 | `tests/unit/services/test_exception_service.py` | 19 | ✅ 全部通过 |
| API 测试 | `tests/api/test_exceptions.py` | 10 | ✅ 全部通过 |
| 集成测试 | `tests/integration/test_exception_replan.py` | 4 | 1 有效 + 3 占位 pass |
| 交叉集成 | `tests/integration/test_auto_redispatch.py` | 5 | ✅ 全部通过 |
| 交叉集成 | `tests/integration/test_dispatch_pipeline.py` | 4 | ✅ 全部通过 |

### 8.2 测试覆盖的路径

| 路径 | 覆盖 |
|------|------|
| 正常创建异常 | ✅ |
| 无效 schedule_code | ✅ |
| 异常分页查询 | ✅ |
| 异常筛选（status/type） | ✅ |
| 异常详情（成功/不存在） | ✅ |
| 解决异常（成功/已解决） | ✅ |
| 更新异常 | ✅ |
| redispatch（成功/无 schedule/不存在） | ✅ |
| reroute（成功/无 route/无 dispatch） | ✅ |
| 版本链 | ⚠️ 占位（3 个 pass placeholder） |
| 原方案保留 | ⚠️ 占位（1 个 pass placeholder） |

### 8.3 未覆盖

- 并发创建异常
- 大数据量分页压力测试
- replan 过程中的事务回滚
- 车辆异常时的完整级联状态校验

---

## 9. 已知限制与后续计划

| 限制 | 影响 | 计划 |
|------|------|------|
| 不支持 `package` 异常 | 包裹损坏无法通过异常体系处理 | 后续版本补充 |
| 无自动异常检测 | 需用户手动创建异常事件 | P1 可加入阈值检测 |
| version chain 集成测试为占位 | 重规划版本链未通过完整集成验证 | 待前端联调时补充 |
| reroute 不排除故障路段 | 重路径规划可能再次经过原故障点 | 后续可加入 excluded_edges |
| 无回调/通知 | resolve 后前端需轮询 | P1 可加 WebSocket |
| redispatch 无容量递增策略 | 重调度可能再次过载同一节点 | 后续可加 excluded_nodes |

---

## 10. 相关文件索引

| 文件 | 说明 |
|------|------|
| `src/backend/models/exception_event.py` | ORM 模型（13 字段） |
| `src/backend/schemas/exception_event.py` | Pydantic 请求/响应 Schema |
| `src/backend/services/exception_service.py` | 异常 CRUD 服务（9 方法） |
| `src/backend/services/replan_service.py` | 重规划服务（2 方法） |
| `src/backend/api/exception_events.py` | API 路由（6 端点） |
| `src/backend/main.py` | 路由注册（第 69-70 行） |
| `tests/unit/services/test_exception_service.py` | 单元测试（19 项） |
| `tests/api/test_exceptions.py` | API 测试（10 项） |
| `tests/integration/test_exception_replan.py` | 集成测试（4 项） |
| `docs/api-contract/api-contract-phase7.md` | API 契约文档 V1.1 |
