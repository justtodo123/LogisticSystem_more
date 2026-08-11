# 阶段 4 API 契约补充文档

**文档版本**：V1.0  
**日期**：2026-06-17  
**状态**：`Review — 待开发评审`  
**对应阶段**：阶段 4（节点间调度 F005）  
**关联文档**：[系统架构设计说明书 §6.5.3](./系统架构设计说明书.md#653-调度f007f021f005f006)

---

## 目录

1. [修订摘要](#1-修订摘要)
2. [API 变更详情](#2-api-变更详情)
3. [算法逻辑变更](#3-算法逻辑变更)
4. [数据库变更](#4-数据库变更)
5. [测试用例](#5-测试用例)

---

## 1. 修订摘要

### 1.1 变更概述

本次修订为阶段 4（节点间调度 F005）新增以下功能：

| 功能 | 说明 | 影响范围 |
| --- | --- | --- |
| **包裹按重量拆分** | L0→L1 打包时按最小车辆载重拆分，避免单个包裹超重 | `algorithms/packaging.py` |
| **部分分配支持** | 车辆不足时跳过当前分组，记录未分配包裹，不中断流程 | `algorithms/node_dispatch.py` |
| **未分配包裹返回** | API 返回 `unallocated_packages` 字段，标识下次需处理的包裹 | `schemas/dispatch.py`、`services/dispatch_service.py`、`models/dispatch_batch.py` |

### 1.2 变更类型

- **新增字段**：`POST /schedule/node-dispatch` 响应新增 `unallocated_packages`
- **算法优化**：打包逻辑按重量拆分，调度逻辑支持部分分配
- **文档更新**：系统架构设计说明书 §6.5.3、阶段 4 开发文档

---

## 2. API 变更详情

### 2.1 POST /schedule/node-dispatch

#### 2.1.1 接口说明

触发节点调度（F005），分配车辆与司机（L0→L1 和 L1→L2）。

**是否需要前端修改**：否（新增字段为可选，前端可不处理）

#### 2.1.2 请求参数（无变更）

```json
{
  "schedule_code": "GS20260609001",
  "demo_mode": false
}
```

#### 2.1.3 响应参数（新增字段）

**成功响应（HTTP 200）**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "batch_code": "DB20260609001",
    "status": "completed",
    "l0_l1_dispatch_count": 5,
    "l1_l2_dispatch_count": 8,
    "unallocated_packages": ["PKG001", "PKG002"],  // 新增字段
    "route_codes": ["RT001", "RT002"]
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**字段说明**：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `unallocated_packages` | `List[str]` | 否 | 未分配的包裹编码列表。当车辆不足时，部分包裹可能无法分配，这些包裹会保留在原节点（`dispatch_id` 为 NULL、`status` 为 `packed`），下次调用节点调度时自动处理。 |

#### 2.1.4 业务规则

1. **未分配包裹标识**：
   - `packages` 表中 `dispatch_id` 为 NULL
   - `status` 为 `packed`
   - `current_node_code` 为包裹当前所在节点

2. **自动处理**：
   - 下次调用 `POST /schedule/node-dispatch` 时，系统会自动查询所有未分配包裹并处理

3. **部分分配不中断**：
   - 车辆不足时不再报错，跳过当前分组并记录未分配包裹
   - 只要有部分车辆分配成功，批次状态仍为 `completed`

---

### 2.2 GET /api/schedule/batches/{batch_code}

#### 2.2.1 接口说明

获取调度批次详情（含 dispatches）。

**是否需要前端修改**：否（新增字段为可选，前端可不处理）

#### 2.2.2 请求参数（无变更）

```
GET /api/schedule/batches/{batch_code}
```

#### 2.2.3 响应参数（新增字段）

**成功响应（HTTP 200）**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "batch_code": "BATCH20260614001",
    "schedule_code": "GS20260614001",
    "status": "completed",
    "unallocated_packages": ["PKG202606140005", "PKG202606140006"],  // 新增字段
    "dispatches": [
      {
        "dispatch_code": "DISP20260614001",
        "vehicle_code": "VEHSC00101",
        "driver_code": "DRVSC00101",
        "level_phase": 0,
        "tasks": [
          {
            "from_node_code": "SC001",
            "to_node_code": "L1001",
            "package_codes": ["PKG202606140001"],
            "is_return": false
          }
        ],
        "total_distance": 25.3,
        "total_time": 0.42
      }
    ]
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**字段说明**：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `unallocated_packages` | `List[str]` | 否 | 未分配的包裹编码列表。从数据库 `dispatch_batches.unallocated_packages` 字段读取（JSON 字符串）。 |

#### 2.2.4 数据源

- `unallocated_packages` 字段存储在 `dispatch_batches` 表中（JSON 字符串）
- 创建批次时（L0→L1 或 L0→L1+L1→L2）保存
- 查询详情时从数据库读取并返回

---

## 3. 算法逻辑变更

### 3.1 打包算法（F021）变更

**文件**：`algorithms/packaging.py`

#### 3.1.1 新增函数

```python
def get_min_vehicle_capacity(db: Session) -> float:
    """
    查询系统最小车辆载重
    
    返回：
        float: 最小车辆载重（kg），若无可用车则返回 999999.0
    """
```

#### 3.1.2 L0→L1 打包逻辑变更

**原逻辑**：同节点对货物直接打包，不检查重量。

**新逻辑**：
1. 查询系统最小车辆载重 `min_capacity`
2. 同节点对货物按重量分组：
   - 若总重量 ≤ `min_capacity`，打成一个包裹
   - 若总重量 > `min_capacity`，按货物顺序拆分，每组重量 ≤ `min_capacity`
   - 单个超重货物（重量 > `min_capacity`）单独打包

**代码示例**：

```python
# 伪代码
min_capacity = get_min_vehicle_capacity(db)
for node_pair, goods_list in goods_by_node_pair.items():
    total_weight = sum(g.weight for g in goods_list)
    if total_weight <= min_capacity:
        # 打成一个包裹
        create_package(goods_list)
    else:
        # 按重量拆分
        current_group = []
        current_weight = 0
        for goods in goods_list:
            if current_weight + goods.weight > min_capacity:
                create_package(current_group)
                current_group = []
                current_weight = 0
            current_group.append(goods)
            current_weight += goods.weight
        if current_group:
            create_package(current_group)
```

### 3.2 节点调度算法（F005）变更

**文件**：`algorithms/node_dispatch.py`

#### 3.2.1 函数返回值变更

**原返回值**：`List[Dict]`（仅调度明细）

**新返回值**：`Tuple[List[Dict], List[str], List[str]]`（调度明细、已分配包裹、未分配包裹）

```python
def _dispatch_level(
    db: Session,
    level_phase: int,
    packages: List[Package],
    vehicles: List[Vehicle],
    ...
) -> Tuple[List[Dict], List[str], List[str]]:
    """
    参数：
        db: 数据库会话
        level_phase: 层级阶段（0=L0→L1，1=L1→L2）
        packages: 待分配包裹列表
        vehicles: 可用车辆列表
        ...
    
    返回：
        Tuple[
            List[Dict],  # 调度明细列表
            List[str],    # 已分配包裹编码列表
            List[str]     # 未分配包裹编码列表
        ]
    """
```

#### 3.2.2 部分分配逻辑

**原逻辑**：车辆不足时抛出 `ValueError("车辆不足")`。

**新逻辑**：
1. 按目标节点分组包裹
2. 为每个分组分配车辆：
   - 若车辆充足，正常分配
   - 若车辆不足，记录未分配包裹，跳过当前分组
3. 返回三元组（调度明细、已分配包裹、未分配包裹）

**代码示例**：

```python
# 伪代码
for target_node_code, grouped_packages in packages_by_target.items():
    available_vehicles = get_available_vehicles(target_node_code)
    if len(available_vehicles) < len(grouped_packages):
        # 车辆不足，记录未分配包裹
        unallocated_packages.extend([p.package_code for p in grouped_packages])
        continue  # 跳过当前分组，不中断流程
    # 正常分配
    ...
```

---

## 4. 数据库变更

### 4.1 新增字段

**表**：`dispatch_batches`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `unallocated_packages` | `String(2000)` | 未分配的包裹编码列表（JSON 字符串） |

**说明**：
- 存储因车辆不足或载重不够而未分配的包裹编码列表
- 使用 JSON 字符串格式存储，如 `["PKG001", "PKG002"]`
- 若为 NULL，表示该批次所有包裹都已分配

### 4.2 数据状态说明

**未分配包裹的状态**：

| 字段 | 值 | 说明 |
| --- | --- | --- |
| `dispatch_id` | `NULL` | 未分配到任何批次 |
| `status` | `packed` | 已打包，待分配 |
| `current_node_code` | 节点编码 | 包裹当前所在节点 |

**状态流转**：

```
packed (未分配) → in_transit (已分配) → delivered (已送达)
```

### 4.3 迁移脚本（待执行）

**注意**：修改数据库模型后，需要执行以下操作之一：

1. **开发环境**：重新初始化数据库
   ```bash
   cd src/backend
   python scripts/init_demo_data.py
   ```

2. **生产环境**：创建 Alembic 迁移脚本
   ```bash
   cd src/backend
   alembic revision --autogenerate -m "Add unallocated_packages to dispatch_batches"
   alembic upgrade head
   ```

---

## 5. 测试用例

### 5.1 单元测试

**文件**：`tests/test_algorithms/test_packaging.py`

#### 5.1.1 新增测试用例

| 测试用例 | 说明 | 状态 |
| --- | --- | --- |
| `test_l0_l1_packaging_splits_by_weight` | 验证 L0→L1 打包时按最小车辆载重拆分 | ✅ 通过 |
| `test_package_code_uniqueness` | 验证包裹编码唯一性 | ✅ 通过 |
| `test_package_schedule_id_assignment` | 验证包裹与调度方案关联 | ✅ 通过 |

#### 5.1.2 测试代码要点

```python
@pytest.mark.unit
def test_l0_l1_packaging_splits_by_weight(self, db_session, test_nodes, test_orders, test_goods):
    """
    测试 L0→L1 打包时按最小车辆载重拆分：
    如果节点对的总重量超过最小车辆载重，应拆分成多个包裹
    """
    # 设置最小车辆载重（通过创建一辆载重较小的车辆）
    from models.vehicle import Vehicle
    min_capacity_vehicle = Vehicle(
        vehicle_code="V_MIN",
        model="小型货车",
        capacity=50.0,  # 最小载重 50kg
        energy_type="fuel",
        node_id=test_nodes["SC001"].id,
        last_arrived_node_id=test_nodes["SC001"].id,  # 必填字段
        status="idle"
    )
    db_session.add(min_capacity_vehicle)
    db_session.commit()
    
    # 执行打包
    # 验证结果：包裹数量 > 1，每个包裹重量 ≤ 50kg
    ...
```

### 5.2 集成测试（待补充）

| 测试用例 | 说明 | 状态 |
| --- | --- | --- |
| 车辆不足时部分分配 | 验证返回 `unallocated_packages` | ⏳ 待测试 |
| 下次调用自动处理未分配包裹 | 验证流程连续性 | ⏳ 待测试 |

---

## 6. 前端联调要点

### 6.1 前端无需修改

- `unallocated_packages` 为可选字段，前端可不处理
- 若前端需要展示未分配包裹信息，可解析该字段并显示提示

### 6.2 建议前端优化（可选）

1. **展示未分配包裹**：
   - 若 `unallocated_packages` 非空，显示提示信息
   - 提供"重新调度"按钮，触发下次节点调度

2. **状态流转展示**：
   - 在调度批次详情页展示未分配包裹列表
   - 提供手动分配入口（P1 功能）

---

## 7. 版本历史

| 版本 | 日期 | 说明 |
| --- | --- | --- |
| V1.0 | 2026-06-17 | 初始版本，记录阶段 4 API 契约补充 |
| V1.1 | 2026-06-17 | 更新 `GET /api/schedule/batches/{batch_code}` 接口，添加 `unallocated_packages` 字段；更新数据库表结构，新增 `dispatch_batches.unallocated_packages` 字段 |

---

## 8. 附录

### 8.1 相关文件清单

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `algorithms/packaging.py` | 修改 | 新增 `get_min_vehicle_capacity()`，修改 L0→L1 打包逻辑 |
| `algorithms/node_dispatch.py` | 修改 | 修改 `_dispatch_level()` 返回值，支持部分分配；修改批次创建逻辑，保存 `unallocated_packages` |
| `services/dispatch_service.py` | 修改 | 修改 `create_node_dispatch()` 返回结构，新增 `unallocated_packages`；修改 `get_dispatch_batch_detail()`，返回 `unallocated_packages` |
| `schemas/dispatch.py` | 修改 | 新增 `unallocated_packages` 字段 |
| `models/dispatch_batch.py` | 修改 | 新增 `unallocated_packages` 字段（数据库表结构变更） |
| `tests/test_algorithms/test_packaging.py` | 新增 | 新增 3 个测试用例 |

### 8.2 参考文档

- [系统架构设计说明书 §6.5.3](../architecture/系统架构设计说明书.md#653-调度f007f021f005f006)
- [MVP 开发计划-后端 §阶段 4](../MVP开发计划-后端.md#阶段-4节点间调度f005)
- [项目宪章](../CODEBUDDY.md#宪法规则)
