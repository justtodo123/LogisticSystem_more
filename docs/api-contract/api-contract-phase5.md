# 阶段5 API 契约文档 - F006路径规划

**版本**：V1.0  
**日期**：2026-06-14  
**阶段**：阶段5（路径规划与可视化 F006）  
**状态**：✅ 已完成

---

## 1. 文档概述

本文档定义阶段5（F006路径规划）的API契约，包括：
- 路径规划触发接口
- 路线查询接口
- 车辆路线坐标查询接口（供前端可视化）

所有接口遵循统一响应格式 `{code, message, data, meta}`。

---

## 2. API 端点列表

| 方法 | 路径 | 说明 | 认证 | 状态 |
|------|------|------|------|------|
| `POST` | `/api/routes/plan` | 手动触发路径规划 (F006) | Bearer Token (dispatcher) | ✅ |
| `GET` | `/api/routes` | 路线列表（分页、筛选） | Bearer Token | ✅ |
| `GET` | `/api/routes/{code}` | 路线详情（含 route_segments） | Bearer Token | ✅ |
| `GET` | `/api/routes/by-vehicle/{code}/coordinates` | 车辆路线坐标（供可视化） | Bearer Token | ✅ |

---

## 3. API 详细说明

### 3.1 POST /api/routes/plan

**功能**：手动触发路径规划（F006）

为指定批次下的节点调度明细规划路径。通常在F005节点调度完成后自动触发，此接口用于手动重新规划。

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `batch_code` | string | 是 | 调度批次编码 |
| `dispatch_codes` | array[string] | 否 | 节点调度明细编码列表（不传则处理批次下所有dispatch）。注意：空数组 `[]` 与不传效果相同；含空字符串 `[""]` 会查询编码为空串的记录，导致"没有可处理的调度明细"错误 |

**请求体示例**：

```json
{
  "batch_code": "BATCH20260614001",
  "dispatch_codes": null
}
```

**响应格式**：

成功（200）：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "batch_code": "BATCH20260614001",
    "status": "completed",
    "routes": [
      {
        "route_code": "ROUTE20260614001",
        "dispatch_code": "DISP20260614001",
        "vehicle_code": "VEH0021",
        "route_segments": [
          {
            "road_name": "虚拟道路",
            "start_lng": 114.3,
            "start_lat": 30.55,
            "end_lng": 114.230313,
            "end_lat": 30.5
          }
        ],
        "total_distance": 17.374,
        "total_time": 17.374,
        "total_emission": 3.4748,
        "algorithm_type": "traditional"
      }
    ]
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

失败（200，code≠0）：

```json
{
  "code": 40001,
  "message": "路径规划失败：批次不存在 BATCH20260614001",
  "data": null,
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**错误码**：

| code | HTTP状态码 | 说明 |
|------|------------|------|
| 0 | 200 | 成功 |
| 40001 | 200 | 路径规划失败（业务错误，如"批次不存在"、"没有可处理的调度明细"） |
| 40300 | 403 | 无权限（manager角色） |

---

### 3.2 GET /api/routes

**功能**：查询路线列表

可按批次编码、车辆编码筛选，支持分页。

> **注意**：`batch_code` 和 `dispatch_code` 可能为 `null`（当关联的调度批次或调度明细被删除时）。

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `batch_code` | string | 否 | 批次编码（筛选） |
| `vehicle_code` | string | 否 | 车辆编码（筛选） |
| `page` | integer | 否 | 页码（默认1） |
| `page_size` | integer | 否 | 每页数量（默认20） |

**响应格式**：

成功（200）：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "route_code": "ROUTE20260614001",
        "batch_code": "BATCH20260614001",
        "dispatch_code": "DISP20260614001",
        "vehicle_code": "VEH0021",
        "total_distance": 17.374,
        "total_time": 17.374,
        "total_emission": 3.4748,
        "created_at": "2026-06-14T10:30:00"
      }
    ],
    "total": 1
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**错误码**：

| code | HTTP状态码 | 说明 |
|------|------------|------|
| 0 | 200 | 成功 |
| 40300 | 403 | 无权限 |

---

### 3.3 GET /api/routes/{code}

**功能**：查询路线详情

返回路线的完整信息，包括路径路段（route_segments）。

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `code` | string | 是 | 路线编码（路径参数） |

**响应格式**：

成功（200）：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "route_code": "ROUTE20260614001",
    "batch_code": "BATCH20260614001",
    "dispatch_code": "DISP20260614001",
    "vehicle_code": "VEH0021",
    "route_segments": [
      {
        "road_name": "虚拟道路",
        "start_lng": 114.3,
        "start_lat": 30.55,
        "end_lng": 114.230313,
        "end_lat": 30.5
      },
      {
        "road_name": "虚拟道路",
        "start_lng": 114.230313,
        "start_lat": 30.5,
        "end_lng": 114.3,
        "end_lat": 30.55
      }
    ],
    "total_distance": 17.374,
    "total_time": 17.374,
    "total_emission": 3.4748,
    "algorithm_type": "traditional",
    "created_at": "2026-06-14T10:30:00"
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

失败（200，code=40400）：

```json
{
  "code": 40400,
  "message": "路线不存在：ROUTE20260614001",
  "data": null,
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**错误码**：

| code | HTTP状态码 | 说明 |
|------|------------|------|
| 0 | 200 | 成功 |
| 40400 | 200 | 路线不存在 |
| 40300 | 403 | 无权限 |

---

### 3.4 GET /api/routes/by-vehicle/{code}/coordinates

**功能**：查询车辆路线坐标（供前端可视化）

返回指定车辆的路线坐标数据，供前端SVG/Canvas绘制路线图。

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `code` | string | 是 | 车辆编码（路径参数） |
| `batch_code` | string | 否 | 批次编码（筛选） |

**响应格式**：

成功（200）：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "vehicle_code": "VEH0021",
    "routes": [
      {
        "route_code": "ROUTE20260614001",
        "batch_code": "BATCH20260614001",
        "coordinates": [
          [114.3, 30.55],
          [114.230313, 30.5],
          [114.3, 30.55]
        ],
        "total_distance": 17.374
      }
    ]
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

失败（200，code=40400）：

```json
{
  "code": 40400,
  "message": "车辆不存在：VEH0021",
  "data": null,
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**错误码**：

| code | HTTP状态码 | 说明 |
|------|------------|------|
| 0 | 200 | 成功 |
| 40400 | 200 | 车辆不存在 |
| 40300 | 403 | 无权限 |

---

## 4. 数据模型

### 4.1 RoutePlanRequest（请求体）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `batch_code` | string | 是 | 调度批次编码 |
| `dispatch_codes` | array[string] | 否 | 节点调度明细编码列表 |

### 4.2 RouteListResponse（路线列表响应）

| 字段 | 类型 | 说明 |
|------|------|------|
| `route_code` | string | 路线编码 |
| `batch_code` | string\|null | 批次编码（关联丢失时为null） |
| `dispatch_code` | string\|null | 调度明细编码（关联丢失时为null） |
| `vehicle_code` | string | 车辆编码 |
| `total_distance` | float | 总距离（公里） |
| `total_time` | float | 总时间（分钟） |
| `total_emission` | float | 总碳排放（kg） |
| `created_at` | string | 创建时间（ISO 8601） |

### 4.3 RouteDetailResponse（路线详情响应）

| 字段 | 类型 | 说明 |
|------|------|------|
| `route_code` | string | 路线编码 |
| `batch_code` | string\|null | 批次编码（关联丢失时为null） |
| `dispatch_code` | string\|null | 调度明细编码（关联丢失时为null） |
| `vehicle_code` | string | 车辆编码 |
| `route_segments` | array[RouteSegment] | 路径路段 |
| `total_distance` | float | 总距离（公里） |
| `total_time` | float | 总时间（分钟） |
| `total_emission` | float | 总碳排放（kg） |
| `algorithm_type` | string | 算法类型（traditional/deepseek） |
| `created_at` | string | 创建时间（ISO 8601） |

### 4.4 RouteSegment（路径路段）

| 字段 | 类型 | 说明 |
|------|------|------|
| `road_name` | string | 道路名称 |
| `start_lng` | float | 起点经度 |
| `start_lat` | float | 起点纬度 |
| `end_lng` | float | 终点经度 |
| `end_lat` | float | 终点纬度 |

### 4.5 RouteCoordinatesResponse（车辆路线坐标响应）

| 字段 | 类型 | 说明 |
|------|------|------|
| `vehicle_code` | string | 车辆编码 |
| `routes` | array[RouteCoordinate] | 路线坐标列表 |

### 4.6 RouteCoordinate（路线坐标）

| 字段 | 类型 | 说明 |
|------|------|------|
| `route_code` | string | 路线编码 |
| `batch_code` | string | 批次编码 |
| `coordinates` | array[array[float]] | 坐标数组 [[lng, lat], ...] |
| `total_distance` | float | 总距离（公里） |

---

## 5. 算法说明

### 5.1 F006 路径规划算法

**输入**：
- `db`：数据库会话
- `dispatch_id`：节点调度明细ID

**输出**：
- `route_data`：路径规划结果字典

**算法流程**：
1. 查询 NodeDispatch (dispatch_id)
2. 获取车辆信息 (vehicle_id)
3. 解析 tasks (JSON数组)
4. 对每个任务计算路径：
   - 使用 Haversine 公式计算距离
   - 生成 route_segments (P0用直线距离，road_name='虚拟道路')
   - 计算时间（距离 / 平均速度，暂定60km/h）
   - 计算碳排放（燃油车：距离×0.2kg/km，电动车：0）
5. 合并所有任务的 route_segments
6. 计算总距离、总时间、总碳排放
7. 返回 route_data

**关键特性**：
- Haversine 公式：计算两点间球面距离（公里）
- 路径路段（route_segments）：包含道路名称、起点/终点坐标
- 碳排放计算：燃油车 0.2 kg/km，电动车 0
- 2-opt 优化：MVP 不触发，仅实现结构

---

## 6. 测试覆盖

| 测试类型 | 文件 | 测试数 | 状态 |
|---------|------|--------|------|
| 算法层 | `tests/test_algorithms/test_route_planning.py` | 12 | ✅ |
| 服务层 | `tests/test_services/test_route_service.py` | 13 | ✅ |
| API层 | `tests/test_routes_api.py` | 6 | ✅ |
| 集成测试 | `tests/test_routes_integration.py` | 4 | ✅ |
| **总计** | | **35** | **100%** |

---

## 7. 已知问题与设计决策

### 7.1 阶段5已知问题

1. **Decimal序列化错误**：route_segments中的坐标值（Decimal类型）需要转换为float才能JSON序列化，已在`route_planning.py`中修复
2. **route_code重复**：`_generate_route_code`函数需要考虑当前事务中未提交的Route对象，已在`route_planning.py`中修复
3. **2-opt优化未触发**：MVP阶段不触发2-opt优化，仅实现算法结构，预留接口

### 7.2 设计决策

1. **路径规划自动触发**：F005节点调度完成后（status="completed"），自动调用F006路径规划
2. **事务原子性**：routes表写入与F005在同一个事务中，保证原子性
3. **离线可演示**：路径规划使用Haversine公式和计算坐标，不依赖任何地图API

---

## 8. 相关文档

- [项目宪章](../../.codebuddy/CODEBUDDY.md)
- [系统架构设计说明书](../../docs/architecture/系统架构设计说明书.md)
- [MVP开发计划 - 后端](../../docs/MVP开发计划-后端.md)
- [阶段5开发文档](./阶段5开发文档-F006路径规划.md)
- [阶段4 API 契约文档](./阶段4-API契约文档.md)（V1.0）

---

**文档版本历史**：

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| V1.0 | 2026-06-14 | AI | 初始版本，定义阶段5 API契约 |
