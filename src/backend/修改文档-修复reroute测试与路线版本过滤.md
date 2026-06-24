# 修改文档：修复 reroute 测试 + 路线坐标版本过滤

> 日期：2026-06-23  
> 分支：`backend/fix-reroute`  
> 关联模块：阶段 7（异常与重规划）、阶段 5（路径规划与可视化）

---

## 一、背景

阶段 7 实现了 Reroute（重路径规划）功能，重构了 `reroute()` 调用链：  
`create_route_planning()` → `replan_single_route()`（轻量方法，不查批次、直接对单条 dispatch 调 F006）。

重构后产生两个问题：

| 问题 | 影响 |
|------|------|
| 2 个单元测试 mock 目标未同步更新 | `test_reroute_success`、`test_trigger_replan_reroute_success` 失败（HTTP 40001） |
| 路线坐标查询返回所有版本路线 | 前端可视化新旧路线混杂，用户无法区分 |

本次修改逐一解决上述问题。

---

## 二、改动文件清单

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `tests/unit/services/test_exception_service.py` | 测试修复 | 更新 mock 目标 + 返回值格式 |
| `services/route_service.py` | 功能增强 | `get_route_coordinates` 新增版本过滤 + 响应字段 |

---

## 三、详细改动

### 3.1 测试修复 —— `test_exception_service.py`

**根因**：重构后 `ReplanService.reroute()` 和 `ExceptionService.trigger_replan(action="reroute")` 调用的是 `RouteService.replan_single_route()`，但测试仍 mock `RouteService.create_route_planning()`，mock 未生效，触发真实算法报错。

**改动**（2 处）：

#### 位置 1：`test_reroute_success`（约第 427 行）

```diff
- Mock RouteService.create_route_planning（避免复杂的算法调用）
- 注意：RouteService 在 replan_service.py 中通过局部导入，需 mock 原始模块
- with patch(
-     "services.route_service.RouteService.create_route_planning",
-     new_callable=AsyncMock,
- ) as mock_rp:
-     mock_rp.return_value = success_response(data={
-         "batch_code": "DB_REROUTE_001",
-         "status": "completed",
-         "routes": [{
-             "route_code": "RT_REPLAN_001",
-             ...
-         }]
-     })

+ Mock RouteService.replan_single_route（避免复杂的算法调用）
+ with patch(
+     "services.route_service.RouteService.replan_single_route",
+     new_callable=AsyncMock,
+ ) as mock_rp:
+     mock_rp.return_value = success_response(data={
+         "route_code": "RT_REPLAN_001",
+         "dispatch_code": "ND_REROUTE_001",
+         "vehicle_code": "V_TEST_001",
+         ...
+         "version": 2,
+         "is_replan": True,
+         "replan_reason": "道路拥堵触发重路径规划",
+         "original_route_code": "RT_ORIG_001",
+     })
```

**变更要点**：
- Mock 目标：`create_route_planning` → `replan_single_route`
- 返回值格式：从嵌套 `batch_code + routes[]` 改为扁平 `route_code + version + is_replan + ...`

#### 位置 2：`test_trigger_replan_reroute_success`（约第 742 行）

同上，Mock 目标和返回值格式同步更新。

---

### 3.2 路线坐标版本过滤 —— `route_service.py`

**根因**：`get_route_coordinates()` 查询某车辆的所有 Route 记录，不做版本筛选。重规划后同一车辆存在 version=1（原路线）和 version=2（新路线），全部返回给前端。

**改动位置**：`RouteService.get_route_coordinates()`（约第 387–414 行）

#### 改动 1：新增最高版本过滤

```python
# 3. 查询该车辆的所有 Route（可按 batch_code 筛选）
query = db.query(Route).filter(Route.vehicle_id == vehicle.id)
# ... batch_code 筛选 ...
routes = query.all()

+ # 3.5 只保留最高版本：取所有路线中 version 的最大值，过滤掉低版本
+ if routes:
+     max_version = max(r.version for r in routes)
+     routes = [r for r in routes if r.version == max_version]
```

**逻辑**：
- 无重规划时，所有路线 version=1，全部保留
- 有一次重规划时，version=1 被过滤，只保留 version=2
- 多次重规划时（如 version=1,2,3），只保留 version=3
- 多条路线同版本且同为最高 → 全部保留（如两辆车各自重规划到 version=2）

#### 改动 2：响应新增版本字段

每条路线对象追加三个字段：

```python
route_list.append({
    "route_code": route.route_code,
    "batch_code": batch_code_value,
    "coordinates": coordinates,
    "total_distance": float(route.total_distance),
+   "version": route.version,
+   "is_replan": route.is_replan,
+   "replan_reason": route.replan_reason,
})
```

---

## 四、影响范围

| 影响 | 说明 |
|------|------|
| ✅ 单元测试 | 268 个测试全部通过（修复前 2 个失败） |
| ✅ 路线坐标 API | 返回结果仅含最高版本，前端不再混淆 |
| ✅ 向后兼容 | 无重规划时行为不变（所有路线 version=1 均保留） |
| ⚠️ 前端适配 | 前端尚未消费 `version`/`is_replan`/`replan_reason` 字段（见 `My_doc/前端待适配清单.md`） |

---

## 五、测试验证

```bash
# 全量测试（268 项，全部通过）
python tests/run_tests.py --md

# 异常服务测试（23 项，全部通过）
pytest tests/unit/services/test_exception_service.py tests/integration/test_exception_replan.py -v

# 路线服务测试（16 项，全部通过）
pytest tests/unit/services/test_route_service.py tests/api/test_routes.py -v
```

**API 验证**（重规划后查询车辆路线坐标）：

```json
{
  "code": 0,
  "data": {
    "vehicle_code": "VEHSC00501",
    "routes": [
      {
        "route_code": "ROUTE20260623004",
        "version": 2,
        "is_replan": true,
        "replan_reason": "string"
      },
      {
        "route_code": "ROUTE20260623005",
        "version": 2,
        "is_replan": true,
        "replan_reason": "道路封闭，需重新规划路径"
      }
    ]
  }
}
```

旧版本（version=1）路线已正确过滤，仅返回 version=2 的最高版本路线。
