"""
阶段4对阶段5影响的全面自动化测试

测试目标：
1. 验证阶段4的修改不会影响阶段5的核心功能
2. 验证数据格式兼容性
3. 验证部分分配场景下阶段5的正确性
4. 验证包裹按重量拆分场景下阶段5的正确性

测试范围：
- 单元测试：route_planning算法
- 集成测试：F005 → F006完整流程
- API测试：路径规划接口
"""

import pytest
import sys
import os
from typing import List, Dict, Any
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base
from models.node import Node
from models.vehicle import Vehicle
from models.driver import Driver
from models.order import Order
from models.goods import Goods
from models.package import Package
from models.global_schedule import GlobalSchedule
from models.dispatch_batch import DispatchBatch
from models.node_dispatch import NodeDispatch
from models.route import Route
from algorithms.global_schedule import global_schedule as run_global_schedule
from algorithms.packaging import packaging as run_packaging
from algorithms.node_dispatch import run_node_dispatch
from algorithms.route_planning import run_route_planning
from services.route_service import RouteService


class TestPhase4ImpactOnPhase5:
    """
    阶段4对阶段5影响的全面测试
    
    测试策略：
    1. 创建测试数据（包含阶段4的新特性：包裹按重量拆分、部分分配）
    2. 执行阶段4（F005节点调度）
    3. 执行阶段5（F006路径规划）
    4. 验证阶段5的输出正确性
    """
    
    @pytest.fixture(scope="function")
    def db_session(self):
        """创建测试数据库会话"""
        # 创建内存SQLite数据库
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        
        Session = sessionmaker(bind=engine)
        session = Session()
        
        yield session
        
        session.close()
        Base.metadata.drop_all(engine)
    
    @pytest.fixture(scope="function")
    def test_data(self, db_session):
        """
        创建测试数据
        
        包含：
        1. 节点（1个存储中心、1个1级分拣中心、2个0级分拣中心）
        2. 车辆（2辆，不同载重）
        3. 司机（2名）
        4. 订单（2个）
        5. 货物（6个，总重量超过小车载重）
        """
        # 1. 创建节点
        nodes = [
            Node(node_code="SC001", name="存储中心1", location="30.5,114.3", 
                 latitude=30.5, longitude=114.3, node_type="storage_center"),
            Node(node_code="L1001", name="1级分拣中心1", location="30.55,114.3", 
                 latitude=30.55, longitude=114.3, node_type="sorting_center"),
            Node(node_code="L2001", name="0级分拣中心1", location="30.52,114.32", 
                 latitude=30.52, longitude=114.32, node_type="sorting_center"),
            Node(node_code="L2002", name="0级分拣中心2", location="30.53,114.33", 
                 latitude=30.53, longitude=114.33, node_type="sorting_center"),
        ]
        
        for node in nodes:
            db_session.add(node)
        db_session.commit()
        
        # 设置节点关系
        nodes[1].sorting_center = type('SortingCenter', (), {'level': 1, 'capacity': 500, 'max_storage_time': 24})()
        nodes[2].sorting_center = type('SortingCenter', (), {'level': 0, 'capacity': None, 'max_storage_time': None})()
        nodes[3].sorting_center = type('SortingCenter', (), {'level': 0, 'capacity': None, 'max_storage_time': None})()
        
        # 2. 创建车辆（2辆，不同载重）
        vehicles = [
            Vehicle(vehicle_code="VEH001", model="小型货车", capacity=50.0, 
                    energy_type="fuel", node_id=nodes[0].id, 
                    last_arrived_node_id=nodes[0].id, status="idle"),
            Vehicle(vehicle_code="VEH002", model="大型货车", capacity=200.0, 
                    energy_type="fuel", node_id=nodes[0].id, 
                    last_arrived_node_id=nodes[0].id, status="idle"),
        ]
        
        for vehicle in vehicles:
            db_session.add(vehicle)
        db_session.commit()
        
        # 3. 创建司机
        drivers = [
            Driver(driver_code="DRV001", name="司机1", node_id=nodes[0].id, status="idle"),
            Driver(driver_code="DRV002", name="司机2", node_id=nodes[0].id, status="idle"),
        ]
        
        for driver in drivers:
            db_session.add(driver)
        db_session.commit()
        
        # 4. 创建订单
        orders = [
            Order(order_code="O001", destination_node_id=nodes[2].id, 
                  time_window="09:00-18:00", status="pending"),
            Order(order_code="O002", destination_node_id=nodes[3].id, 
                  time_window="09:00-18:00", status="pending"),
        ]
        
        for order in orders:
            db_session.add(order)
        db_session.commit()
        
        # 5. 创建货物（6个，总重量超过小车载重）
        goods_list = [
            Goods(goods_code="G001", goods_name="货物1", goods_type="普通", 
                  weight=30.0, volume=1.0, node_id=nodes[0].id, 
                  order_id=orders[0].id, status="pending_pack"),
            Goods(goods_code="G002", goods_name="货物2", goods_type="普通", 
                  weight=30.0, volume=1.0, node_id=nodes[0].id, 
                  order_id=orders[0].id, status="pending_pack"),
            Goods(goods_code="G003", goods_name="货物3", goods_type="普通", 
                  weight=30.0, volume=1.0, node_id=nodes[0].id, 
                  order_id=orders[0].id, status="pending_pack"),
            Goods(goods_code="G004", goods_name="货物4", goods_type="普通", 
                  weight=30.0, volume=1.0, node_id=nodes[0].id, 
                  order_id=orders[1].id, status="pending_pack"),
            Goods(goods_code="G005", goods_name="货物5", goods_type="普通", 
                  weight=30.0, volume=1.0, node_id=nodes[0].id, 
                  order_id=orders[1].id, status="pending_pack"),
            Goods(goods_code="G006", goods_name="货物6", goods_type="普通", 
                  weight=30.0, volume=1.0, node_id=nodes[0].id, 
                  order_id=orders[1].id, status="pending_pack"),
        ]
        
        for goods in goods_list:
            db_session.add(goods)
        db_session.commit()
        
        return {
            "nodes": nodes,
            "vehicles": vehicles,
            "drivers": drivers,
            "orders": orders,
            "goods": goods_list,
        }
    
    def test_full_flow_with_package_split(self, db_session, test_data):
        """
        测试场景1：包裹按重量拆分后，阶段5路径规划正常执行
        
        步骤：
        1. 执行F007全局调度
        2. 执行F021打包（会按重量拆分包裹）
        3. 执行F005节点调度
        4. 执行F006路径规划
        5. 验证路径规划结果正确性
        """
        print("\n=== 测试场景1：包裹按重量拆分后阶段5正常执行 ===")
        
        # 1. 执行F007全局调度
        print("\n步骤1: F007全局调度")
        schedule_result = run_global_schedule(
            order_codes=["O001", "O002"],
            algorithm="traditional",
            db=db_session
        )
        
        schedule_code = schedule_result["schedule_code"]
        print(f"  全局调度完成，schedule_code={schedule_code}")
        
        # 手动创建GlobalSchedule对象
        from models.global_schedule import GlobalSchedule
        global_schedule = GlobalSchedule(
            schedule_code=schedule_code,
            order_codes=[test_data["orders"][0].id, test_data["orders"][1].id],
            goods_schedules=schedule_result["goods_schedules"],
            total_distance=schedule_result["total_distance"],
            total_time=schedule_result["total_time"],
            total_goods=schedule_result["total_goods"],
            score=schedule_result["score"]
        )
        db_session.add(global_schedule)
        db_session.commit()
        
        # 更新订单状态
        for order in test_data["orders"]:
            order.status = "delivering"
        db_session.commit()
        
        # 2. 执行F021打包
        print("\n步骤2: F021打包")
        packages = run_packaging(
            schedule_result=schedule_result,
            schedule_id=global_schedule.id,
            db=db_session
        )
        
        package_codes = [pkg.package_code for pkg in packages]
        print(f"  打包完成，生成了 {len(package_codes)} 个包裹")
        
        # 手动保存Package到数据库
        for pkg in packages:
            db_session.add(pkg)
        db_session.commit()
        
        # 更新货物和包裹状态
        for goods in test_data["goods"]:
            goods.status = "packed"
        for pkg in packages:
            pkg.status = "packed"
        db_session.commit()
        
        # 3. 执行F005节点调度
        print("\n步骤3: F005节点调度")
        dispatch_result = run_node_dispatch(
            db=db_session,
            schedule_code=schedule_code,
            demo_mode=True
        )
        
        batch_code = dispatch_result["batch_code"]
        print(f"  节点调度完成，batch_code={batch_code}")
        print(f"  未分配包裹：{dispatch_result.get('unallocated_packages', [])}")
        
        # 4. 执行F006路径规划
        print("\n步骤4: F006路径规划")
        route_result = RouteService.create_route_planning(
            batch_code=batch_code,
            dispatch_codes=None,
            db=db_session
        )
        
        # 5. 验证路径规划结果
        print("\n步骤5: 验证路径规划结果")
        assert route_result["code"] == 0, f"路径规划失败：{route_result.get('message')}"
        assert "routes" in route_result["data"], "返回数据缺少routes字段"
        assert len(route_result["data"]["routes"]) > 0, "没有生成路线"
        
        # 验证每条路线的数据完整性
        for route_data in route_result["data"]["routes"]:
            assert "route_code" in route_data, "路线缺少route_code"
            assert "dispatch_id" in route_data, "路线缺少dispatch_id"
            assert "vehicle_id" in route_data, "路线缺少vehicle_id"
            assert "route_segments" in route_data, "路线缺少route_segments"
            assert "total_distance" in route_data, "路线缺少total_distance"
            assert "total_time" in route_data, "路线缺少total_time"
            assert "total_emission" in route_data, "路线缺少total_emission"
            
            # 验证route_segments格式
            assert isinstance(route_data["route_segments"], list), "route_segments应为列表"
            for segment in route_data["route_segments"]:
                assert "road_name" in segment, "路段缺少road_name"
                assert "start_lng" in segment, "路段缺少start_lng"
                assert "start_lat" in segment, "路段缺少start_lat"
                assert "end_lng" in segment, "路段缺少end_lng"
                assert "end_lat" in segment, "路段缺少end_lat"
        
        print(f"  路径规划成功，生成了 {len(route_result['data']['routes'])} 条路线")
        print("  所有验证通过 ✅")
        
        return True
    
    def test_partial_allocation_compatibility(self, db_session, test_data):
        """
        测试场景2：部分分配场景下，阶段5只规划已分配包裹的路线
        
        步骤：
        1. 只创建1辆车辆（载重50kg）
        2. 执行F007 → F021 → F005
        3. 验证部分包裹未分配
        4. 执行F006路径规划
        5. 验证只为已分配的调度明细生成路线
        """
        print("\n=== 测试场景2：部分分配场景下阶段5兼容性 ===")
        
        # 删除第二辆车辆，模拟车辆不足场景
        db_session.query(Vehicle).filter(Vehicle.vehicle_code == "VEH002").delete()
        db_session.commit()
        print("  已删除第二辆车辆，模拟车辆不足场景")
        
        # 1. 执行F007全局调度
        print("\n步骤1: F007全局调度")
        schedule_result = run_global_schedule(
            order_codes=["O001", "O002"],
            algorithm="traditional",
            db=db_session
        )
        
        schedule_code = schedule_result["schedule_code"]
        print(f"  全局调度完成，schedule_code={schedule_code}")
        
        # 手动创建GlobalSchedule对象
        from models.global_schedule import GlobalSchedule
        global_schedule = GlobalSchedule(
            schedule_code=schedule_code,
            order_codes=[test_data["orders"][0].id, test_data["orders"][1].id],
            goods_schedules=schedule_result["goods_schedules"],
            total_distance=schedule_result["total_distance"],
            total_time=schedule_result["total_time"],
            total_goods=schedule_result["total_goods"],
            score=schedule_result["score"]
        )
        db_session.add(global_schedule)
        db_session.commit()
        
        # 更新订单状态
        for order in test_data["orders"]:
            order.status = "delivering"
        db_session.commit()
        
        # 2. 执行F021打包
        print("\n步骤2: F021打包")
        packages = run_packaging(
            schedule_result=schedule_result,
            schedule_id=global_schedule.id,
            db=db_session
        )
        
        package_codes = [pkg.package_code for pkg in packages]
        print(f"  打包完成，生成了 {len(package_codes)} 个包裹")
        
        # 手动保存Package到数据库
        for pkg in packages:
            db_session.add(pkg)
        db_session.commit()
        
        # 更新货物和包裹状态
        for goods in test_data["goods"]:
            goods.status = "packed"
        for pkg in packages:
            pkg.status = "packed"
        db_session.commit()
        
        # 3. 执行F005节点调度（预期：部分分配）
        print("\n步骤3: F005节点调度（预期：部分分配）")
        dispatch_result = run_node_dispatch(
            db=db_session,
            schedule_code=schedule_code,
            demo_mode=True
        )
        
        batch_code = dispatch_result["batch_code"]
        unallocated_packages = dispatch_result.get("unallocated_packages", [])
        
        print(f"  节点调度完成，batch_code={batch_code}")
        print(f"  已分配包裹数：{len(dispatch_result.get('allocated_packages', []))}")
        print(f"  未分配包裹数：{len(unallocated_packages)}")
        
        # 4. 执行F006路径规划
        print("\n步骤4: F006路径规划")
        route_result = RouteService.create_route_planning(
            batch_code=batch_code,
            dispatch_codes=None,
            db=db_session
        )
        
        # 5. 验证路径规划结果
        print("\n步骤5: 验证路径规划结果")
        assert route_result["code"] == 0, f"路径规划失败：{route_result.get('message')}"
        
        routes = route_result["data"]["routes"]
        print(f"  路径规划成功，生成了 {len(routes)} 条路线")
        
        # 验证：只为已分配的调度明细生成路线
        dispatches = db_session.query(NodeDispatch).filter(
            NodeDispatch.dispatch_batch_id == db_session.query(DispatchBatch).filter(
                DispatchBatch.batch_code == batch_code
            ).first().id
        ).all()
        
        print(f"  调度明细数：{len(dispatches)}")
        print(f"  路线数：{len(routes)}")
        
        # 路线数应该等于调度明细数
        assert len(routes) == len(dispatches), \
            f"路线数({len(routes)})不等于调度明细数({len(dispatches)})"
        
        print("  所有验证通过 ✅")
        
        return True
    
    def test_tasks_json_format_compatibility(self, db_session):
        """
        测试场景3：验证阶段4生成的tasks JSON格式与阶段5期望的格式兼容
        
        验证要点：
        1. tasks是列表
        2. 每个task包含from_node_code、to_node_code、package_codes、is_return字段
        3. 字段类型正确
        """
        print("\n=== 测试场景3：tasks JSON格式兼容性 ===")
        
        # 创建一个NodeDispatch对象
        dispatch = NodeDispatch(
            dispatch_code="TEST001",
            dispatch_batch_id=1,
            level_phase=0,
            vehicle_id=1,
            driver_id=None,
            tasks=[
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
            ],
            total_distance=15.0,
            total_time=0.25,
            algorithm_type="traditional"
        )
        
        db_session.add(dispatch)
        db_session.commit()
        
        # 读取tasks并验证格式
        print("\n验证tasks JSON格式...")
        
        tasks = dispatch.tasks
        assert isinstance(tasks, list), "tasks应为列表"
        assert len(tasks) == 2, "tasks应包含2个任务"
        
        # 验证第一个任务（运输任务）
        task1 = tasks[0]
        assert "from_node_code" in task1, "任务缺少from_node_code"
        assert "to_node_code" in task1, "任务缺少to_node_code"
        assert "package_codes" in task1, "任务缺少package_codes"
        assert "is_return" in task1, "任务缺少is_return"
        assert task1["is_return"] == False, "第一个任务应为运输任务"
        
        # 验证第二个任务（返程任务）
        task2 = tasks[1]
        assert task2["is_return"] == True, "第二个任务应为返程任务"
        assert task2["package_codes"] == [], "返程任务应无包裹"
        
        print("  tasks JSON格式验证通过 ✅")
        
        # 验证阶段5可以正确读取tasks
        print("\n验证阶段5可以正确读取tasks...")
        
        # 模拟run_route_planning函数的逻辑
        from models.node import Node
        from models.vehicle import Vehicle
        
        # 创建模拟的节点和车辆
        node1 = Node(node_code="SC001", name="测试节点1", location="30.5,114.3", 
                    latitude=30.5, longitude=114.3, node_type="storage_center")
        node2 = Node(node_code="L1001", name="测试节点2", location="30.55,114.3", 
                    latitude=30.55, longitude=114.3, node_type="sorting_center")
        db_session.add(node1)
        db_session.add(node2)
        db_session.commit()
        
        vehicle = Vehicle(vehicle_code="VEH001", model="测试车型", capacity=100.0, 
                        energy_type="fuel", node_id=node1.id, 
                        last_arrived_node_id=node1.id, status="idle")
        db_session.add(vehicle)
        db_session.commit()
        
        # 更新dispatch的vehicle_id
        dispatch.vehicle_id = vehicle.id
        db_session.commit()
        
        # 调用run_route_planning
        try:
            route_data = run_route_planning(db_session, dispatch.id)
            print(f"  路径规划成功：{route_data['route_code']}")
            print(f"  路径路段数：{len(route_data['route_segments'])}")
            print("  阶段5正确读取tasks ✅")
            return True
        except Exception as e:
            pytest.fail(f"阶段5读取tasks失败：{str(e)}")
        
        return False
    
    def test_route_service_error_handling(self, db_session):
        """
        测试场景4：验证阶段5的错误处理
        
        验证要点：
        1. dispatch_id不存在时抛出ValueError
        2. tasks为空时抛出ValueError
        3. 节点不存在时跳过该任务
        """
        print("\n=== 测试场景4：阶段5错误处理 ===")
        
        # 测试1：dispatch_id不存在
        print("\n测试1：dispatch_id不存在")
        try:
            run_route_planning(db_session, 999)
            pytest.fail("应抛出ValueError")
        except ValueError as e:
            print(f"  预期错误：{str(e)}")
            print("  测试通过 ✅")
        
        # 测试2：tasks为空
        print("\n测试2：tasks为空")
        dispatch = NodeDispatch(
            dispatch_code="TEST002",
            dispatch_batch_id=1,
            level_phase=0,
            vehicle_id=1,
            driver_id=None,
            tasks=[],
            total_distance=0,
            total_time=0,
            algorithm_type="traditional"
        )
        db_session.add(dispatch)
        db_session.commit()
        
        try:
            run_route_planning(db_session, dispatch.id)
            pytest.fail("应抛出ValueError")
        except ValueError as e:
            print(f"  预期错误：{str(e)}")
            print("  测试通过 ✅")
        
        # 测试3：节点不存在时跳过该任务
        print("\n测试3：节点不存在时跳过该任务")
        dispatch2 = NodeDispatch(
            dispatch_code="TEST003",
            dispatch_batch_id=1,
            level_phase=0,
            vehicle_id=1,
            driver_id=None,
            tasks=[
                {
                    "from_node_code": "NONEXISTENT1",
                    "to_node_code": "NONEXISTENT2",
                    "package_codes": [],
                    "is_return": False
                }
            ],
            total_distance=0,
            total_time=0,
            algorithm_type="traditional"
        )
        db_session.add(dispatch2)
        db_session.commit()
        
        # 应不抛出异常，但route_segments为空
        route_data = run_route_planning(db_session, dispatch2.id)
        assert len(route_data["route_segments"]) == 0, "节点不存在时route_segments应为空"
        assert route_data["total_distance"] == 0, "节点不存在时total_distance应为0"
        print("  测试通过 ✅")
        
        return True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
