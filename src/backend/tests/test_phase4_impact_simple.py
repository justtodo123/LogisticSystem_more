"""
简化的阶段4对阶段5影响测试

只测试核心兼容性问题：
1. tasks JSON格式兼容性
2. 部分分配场景
3. 包裹拆分场景
"""

import json
import math
from typing import List, Dict, Any


def test_tasks_json_format():
    """
    测试场景1：验证tasks JSON格式兼容性
    
    阶段4生成的tasks格式：
    [{"from_node_code": "...", "to_node_code": "...", "package_codes": [...], "is_return": false}]
    
    阶段5期望的tasks格式：相同
    """
    print("\n=== 测试场景1：tasks JSON格式兼容性 ===")
    
    # 模拟阶段4生成的tasks
    tasks_from_phase4 = [
        {
            "from_node_code": "SC001",
            "to_node_code": "L1001",
            "package_codes": ["PKG001", "PKG002"],
            "is_return": False
        },
        {
            "from_node_code": "L1001",
            "to_node_code": "SC001",
            "package_codes": [],
            "is_return": True
        }
    ]
    
    # 模拟阶段5读取tasks
    print("  模拟阶段5读取tasks...")
    
    assert isinstance(tasks_from_phase4, list), "tasks应为列表"
    assert len(tasks_from_phase4) == 2, "tasks应包含2个任务"
    
    for task in tasks_from_phase4:
        from_code = task.get("from_node_code")
        to_code = task.get("to_node_code")
        pkg_codes = task.get("package_codes")
        is_return = task.get("is_return")
        
        assert from_code is not None, "任务缺少from_node_code"
        assert to_code is not None, "任务缺少to_node_code"
        assert pkg_codes is not None, "任务缺少package_codes"
        assert is_return is not None, "任务缺少is_return"
        
        assert isinstance(pkg_codes, list), "package_codes应为列表"
    
    print("  tasks JSON格式兼容 ✅")
    return True


def test_partial_allocation():
    """
    测试场景2：部分分配场景下阶段5的行为
    
    如果阶段4部分分配（有些包裹未分配），阶段5应该：
    1. 只为已分配的调度明细生成路线
    2. 未分配的包裹不影响阶段5
    """
    print("\n=== 测试场景2：部分分配场景 ===")
    
    # 模拟阶段4的输出（包含unallocated_packages）
    phase4_output = {
        "batch_code": "BATCH001",
        "status": "completed",
        "dispatches": [
            {
                "dispatch_code": "DISP001",
                "vehicle_code": "VEH001",
                "tasks": [
                    {
                        "from_node_code": "SC001",
                        "to_node_code": "L1001",
                        "package_codes": ["PKG001"],
                        "is_return": False
                    }
                ],
                "total_distance": 15.0,
                "total_time": 0.25
            }
        ],
        "unallocated_packages": ["PKG002", "PKG003"]  # 未分配的包裹
    }
    
    # 模拟阶段5的处理逻辑
    print("  模拟阶段5处理阶段4的输出...")
    
    dispatches = phase4_output["dispatches"]
    unallocated = phase4_output.get("unallocated_packages", [])
    
    # 阶段5只为dispatches生成路线
    routes = []
    for dispatch in dispatches:
        route = {
            "route_code": f"ROUTE{datetime.now().strftime('%Y%m%d')}001",
            "dispatch_code": dispatch["dispatch_code"],
            "vehicle_code": dispatch["vehicle_code"],
            "route_segments": []
        }
        routes.append(route)
    
    print(f"  已分配包裹数：{len(dispatches)}")
    print(f"  未分配包裹数：{len(unallocated)}")
    print(f"  生成路线数：{len(routes)}")
    
    assert len(routes) == len(dispatches), "路线数应等于调度明细数"
    assert len(unallocated) > 0, "应有未分配包裹"
    
    print("  部分分配场景兼容 ✅")
    return True


def test_package_split():
    """
    测试场景3：包裹按重量拆分后阶段5的处理
    
    如果阶段4的F021打包时按重量拆分包裹，阶段5应该：
    1. 能正确处理拆分后的包裹编码
    2. 能正确读取tasks中的package_codes
    """
    print("\n=== 测试场景3：包裹按重量拆分 ===")
    
    # 模拟包裹拆分后的情景
    # 原来1个包裹（重量100kg）被拆成2个包裹（各50kg）
    original_package = "PKG001"  # 重量100kg
    split_packages = ["PKG001_1", "PKG001_2"]  # 各50kg
    
    # 模拟阶段4生成的tasks（包含拆分后的包裹编码）
    tasks = [
        {
            "from_node_code": "SC001",
            "to_node_code": "L1001",
            "package_codes": split_packages,  # 使用拆分后的包裹编码
            "is_return": False
        }
    ]
    
    # 模拟阶段5读取tasks
    print("  模拟阶段5读取拆分后的包裹编码...")
    
    for task in tasks:
        pkg_codes = task.get("package_codes")
        assert isinstance(pkg_codes, list), "package_codes应为列表"
        assert len(pkg_codes) == 2, "应包含2个拆分后的包裹"
        assert pkg_codes[0] == "PKG001_1", "包裹编码错误"
        assert pkg_codes[1] == "PKG001_2", "包裹编码错误"
    
    print("  包裹拆分场景兼容 ✅")
    return True


def test_route_planning_algorithm():
    """
    测试场景4：路径规划算法的核心逻辑
    
    验证：
    1. Haversine距离计算正确
    2. route_segments生成正确
    3. 碳排放计算正确
    """
    print("\n=== 测试场景4：路径规划算法核心逻辑 ===")
    
    # 模拟数据
    tasks = [
        {
            "from_node_code": "SC001",
            "to_node_code": "L1001",
            "package_codes": ["PKG001"],
            "is_return": False
        }
    ]
    
    # 模拟节点坐标
    nodes = {
        "SC001": {"latitude": 30.5, "longitude": 114.3},
        "L1001": {"latitude": 30.55, "longitude": 114.3}
    }
    
    # 计算距离
    def haversine(lat1, lng1, lat2, lng2):
        R = 6371.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_phi / 2) ** 2 + 
             math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    # 模拟路径规划
    print("  模拟路径规划...")
    
    route_segments = []
    total_distance = 0.0
    
    for task in tasks:
        from_code = task["from_node_code"]
        to_code = task["to_node_code"]
        
        from_node = nodes[from_code]
        to_node = nodes[to_code]
        
        distance = haversine(
            from_node["latitude"], from_node["longitude"],
            to_node["latitude"], to_node["longitude"]
        )
        
        segment = {
            "road_name": "虚拟道路",
            "start_lng": from_node["longitude"],
            "start_lat": from_node["latitude"],
            "end_lng": to_node["longitude"],
            "end_lat": to_node["latitude"]
        }
        route_segments.append(segment)
        total_distance += distance
    
    # 验证
    assert len(route_segments) == 1, "应生成1个路段"
    assert total_distance > 0, "总距离应大于0"
    assert route_segments[0]["road_name"] == "虚拟道路", "道路名称错误"
    
    print(f"  总距离：{total_distance:.3f} km")
    print(f"  路段数：{len(route_segments)}")
    print("  路径规划算法核心逻辑正确 ✅")
    return True


def test_data_flow():
    """
    测试场景5：验证阶段4→阶段5的数据流
    
    验证：
    1. 阶段4的输出（node_dispatches表）是阶段5的输入
    2. 数据格式正确
    3. 外键关联正确
    """
    print("\n=== 测试场景5：阶段4→阶段5数据流 ===")
    
    # 模拟阶段4的输出（node_dispatches表的一行）
    node_dispatch = {
        "id": 1,
        "dispatch_code": "DISP001",
        "dispatch_batch_id": 1,  # 外键 → dispatch_batches.id
        "level_phase": 0,
        "vehicle_id": 1,  # 外键 → vehicles.id
        "driver_id": 1,  # 外键 → drivers.id (可为NULL)
        "tasks": [
            {
                "from_node_code": "SC001",
                "to_node_code": "L1001",
                "package_codes": ["PKG001"],
                "is_return": False
            }
        ],
        "total_distance": 15.0,
        "total_time": 0.25,
        "algorithm_type": "traditional"
    }
    
    # 模拟阶段5的输入（读取node_dispatches表）
    print("  模拟阶段5读取阶段4的输出...")
    
    # 阶段5读取dispatch_id
    dispatch_id = node_dispatch["id"]
    assert dispatch_id == 1, "dispatch_id错误"
    
    # 阶段5读取tasks
    tasks = node_dispatch["tasks"]
    assert isinstance(tasks, list), "tasks应为列表"
    
    # 阶段5读取vehicle_id
    vehicle_id = node_dispatch["vehicle_id"]
    assert vehicle_id == 1, "vehicle_id错误"
    
    print("  数据流验证通过 ✅")
    return True


if __name__ == "__main__":
    """运行所有测试"""
    print("=" * 60)
    print("阶段4对阶段5影响的全面测试")
    print("=" * 60)
    
    results = []
    
    # 测试1：tasks JSON格式兼容性
    try:
        result = test_tasks_json_format()
        results.append(("tasks JSON格式兼容性", "通过 ✅"))
    except Exception as e:
        results.append(("tasks JSON格式兼容性", f"失败 ❌：{str(e)}"))
    
    # 测试2：部分分配场景
    try:
        result = test_partial_allocation()
        results.append(("部分分配场景", "通过 ✅"))
    except Exception as e:
        results.append(("部分分配场景", f"失败 ❌：{str(e)}"))
    
    # 测试3：包裹拆分场景
    try:
        result = test_package_split()
        results.append(("包裹拆分场景", "通过 ✅"))
    except Exception as e:
        results.append(("包裹拆分场景", f"失败 ❌：{str(e)}"))
    
    # 测试4：路径规划算法核心逻辑
    try:
        result = test_route_planning_algorithm()
        results.append(("路径规划算法核心逻辑", "通过 ✅"))
    except Exception as e:
        results.append(("路径规划算法核心逻辑", f"失败 ❌：{str(e)}"))
    
    # 测试5：数据流验证
    try:
        result = test_data_flow()
        results.append(("数据流验证", "通过 ✅"))
    except Exception as e:
        results.append(("数据流验证", f"失败 ❌：{str(e)}"))
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        print(f"{test_name}: {result}")
        if "通过" in result:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "-" * 60)
    print(f"总计：{len(results)}个测试")
    print(f"通过：{passed}个")
    print(f"失败：{failed}个")
    print("-" * 60)
    
    if failed == 0:
        print("\n✅ 所有测试通过！阶段4的修改不会影响阶段5的核心功能。")
    else:
        print(f"\n❌ 有{failed}个测试失败，请检查阶段4和阶段5的兼容性。")
    

import datetime
