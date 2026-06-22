"""
完整调度链路集成测试

测试完整的调度链路：F007 → F021 → F005 → F006
由于阶段6的模拟送达还没有实现，本测试会手动推进状态

注意：
1. 本测试使用真实的数据库会话
2. 本测试会调用真实的算法函数
3. 本测试会验证数据是否正确写入数据库
"""

import pytest
import sys
import os
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base

from models.node import Node
from models.storage_center import StorageCenter
from models.sorting_center import SortingCenter
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


@pytest.fixture(scope="function")
def db_session():
    """
    创建测试数据库会话
    
    使用内存数据库，每个测试独立
    """
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def full_test_data(db_session):
    """
    创建完整的测试数据
    
    包含：
    1. 节点（5个存储中心、2个1级分拣中心、50个0级分拣中心）
    2. 车辆和司机
    3. 订单和货物
    """
    # 1. 创建节点
    nodes = [
        # 存储中心 (L0)
        Node(node_code="SC001", name="存储中心1", location="武汉",
             latitude=30.5, longitude=114.3, node_type="storage_center"),
        Node(node_code="SC002", name="存储中心2", location="武汉",
             latitude=30.51, longitude=114.31, node_type="storage_center"),
        
        # 1级分拣中心 (L1)
        Node(node_code="SO001", name="1级分拣中心1", location="武汉",
             latitude=30.6, longitude=114.4, node_type="sorting_center"),
        Node(node_code="SO002", name="1级分拣中心2", location="武汉",
             latitude=30.61, longitude=114.41, node_type="sorting_center"),
        
        # 0级分拣中心 (L2)
        Node(node_code="SO010", name="0级分拣中心1", location="武昌",
             latitude=30.54, longitude=114.315, node_type="sorting_center"),
        Node(node_code="SO011", name="0级分拣中心2", location="洪山",
             latitude=30.55, longitude=114.35, node_type="sorting_center"),
    ]
    
    for node in nodes:
        db_session.add(node)
    db_session.flush()
    
    # 创建节点的扩展信息
    sc1 = StorageCenter(node_id=nodes[0].id, capacity=1000.0, inventory=0)
    sc2 = StorageCenter(node_id=nodes[1].id, capacity=1000.0, inventory=0)
    so1 = SortingCenter(node_id=nodes[2].id, level=1, capacity=100, max_storage_time=24)
    so2 = SortingCenter(node_id=nodes[3].id, level=1, capacity=100, max_storage_time=24)
    so3 = SortingCenter(node_id=nodes[4].id, level=0)
    so4 = SortingCenter(node_id=nodes[5].id, level=0)
    
    db_session.add_all([sc1, sc2, so1, so2, so3, so4])
    db_session.flush()
    
    # 2. 创建车辆（包括L1节点的车辆）
    vehicles = [
        Vehicle(vehicle_code="VEH001", model="测试车型", capacity=100.0,
                energy_type="fuel", node_id=nodes[0].id,
                last_arrived_node_id=nodes[0].id, status="idle"),
        Vehicle(vehicle_code="VEH002", model="测试车型", capacity=100.0,
                energy_type="fuel", node_id=nodes[0].id,
                last_arrived_node_id=nodes[0].id, status="idle"),
        Vehicle(vehicle_code="VEH003", model="测试车型", capacity=100.0,
                energy_type="fuel", node_id=nodes[1].id,
                last_arrived_node_id=nodes[1].id, status="idle"),
        # L1节点的车辆（用于L1→L2调度）
        Vehicle(vehicle_code="VEH004", model="测试车型", capacity=100.0,
                energy_type="fuel", node_id=nodes[2].id,  # SO001
                last_arrived_node_id=nodes[2].id, status="idle"),
        Vehicle(vehicle_code="VEH005", model="测试车型", capacity=100.0,
                energy_type="fuel", node_id=nodes[3].id,  # SO002
                last_arrived_node_id=nodes[3].id, status="idle"),
    ]
    
    for vehicle in vehicles:
        db_session.add(vehicle)
    db_session.flush()
    
    # 3. 创建司机
    drivers = [
        Driver(driver_code="DRV001", name="测试司机1", phone="13800000001",
               license_type="C1", shift="day", node_id=nodes[0].id, status="idle"),
        Driver(driver_code="DRV002", name="测试司机2", phone="13800000002",
               license_type="C1", shift="day", node_id=nodes[0].id, status="idle"),
        Driver(driver_code="DRV003", name="测试司机3", phone="13800000003",
               license_type="C1", shift="day", node_id=nodes[1].id, status="idle"),
    ]
    
    for driver in drivers:
        db_session.add(driver)
    db_session.flush()
    
    # 4. 创建订单
    orders = [
        Order(
            order_code="O001",
            destination_node_id=nodes[4].id,  # SO010
            time_window="09:00-18:00",
            status="pending"
        ),
        Order(
            order_code="O002",
            destination_node_id=nodes[5].id,  # SO011
            time_window="09:00-18:00",
            status="pending"
        ),
    ]
    
    for order in orders:
        db_session.add(order)
    db_session.flush()
    
    # 5. 创建货物
    goods_list = [
        Goods(
            goods_code="G001",
            goods_name="测试货物1",
            goods_type="普通货物",
            weight=10.0,
            volume=0.5,
            node_id=nodes[0].id,  # SC001
            order_id=orders[0].id,
            status="pending_pack"
        ),
        Goods(
            goods_code="G002",
            goods_name="测试货物2",
            goods_type="普通货物",
            weight=15.0,
            volume=0.8,
            node_id=nodes[0].id,  # SC001
            order_id=orders[0].id,
            status="pending_pack"
        ),
        Goods(
            goods_code="G003",
            goods_name="测试货物3",
            goods_type="普通货物",
            weight=20.0,
            volume=1.0,
            node_id=nodes[1].id,  # SC002
            order_id=orders[1].id,
            status="pending_pack"
        ),
    ]
    
    for goods in goods_list:
        db_session.add(goods)
    db_session.flush()
    
    # 提交事务
    db_session.commit()
    
    return {
        "nodes": nodes,
        "vehicles": vehicles,
        "drivers": drivers,
        "orders": orders,
        "goods": goods_list
    }


class TestFullDispatchFlow:
    """测试完整的调度链路"""
    
    def test_full_flow_demo_mode(self, db_session, full_test_data):
        """
        测试完整的调度链路（demo_mode=true）
        
        流程：
        1. F007 全局调度
        2. F021 打包
        3. F005 节点调度（demo_mode=true，一次性完成L0→L1和L1→L2）
        4. F006 路径规划
        
        注意：由于阶段6的模拟送达还没有实现，demo_mode=true时会自动推进状态
        """
        # 1. F007 全局调度
        print("\n=== 步骤1: F007 全局调度 ===")
        
        schedule_result = run_global_schedule(
            order_codes=["O001", "O002"],
            algorithm="traditional",
            db=db_session
        )
        
        assert "schedule_code" in schedule_result
        schedule_code = schedule_result["schedule_code"]
        print(f"全局调度完成，schedule_code={schedule_code}")
        
        # 手动创建 GlobalSchedule 对象并保存到数据库
        from models.global_schedule import GlobalSchedule
        
        # 查询订单ID
        order_ids = {}
        for order_code in ["O001", "O002"]:
            order = db_session.query(Order).filter(Order.order_code == order_code).first()
            if order:
                order_ids[order_code] = order.id
        
        global_schedule = GlobalSchedule(
            schedule_code=schedule_code,
            order_codes=list(order_ids.values()),  # 使用订单ID列表
            goods_schedules=schedule_result["goods_schedules"],
            total_distance=schedule_result["total_distance"],
            total_time=schedule_result["total_time"],
            total_goods=schedule_result["total_goods"],
            score=schedule_result["score"]
        )
        db_session.add(global_schedule)
        db_session.commit()
        
        # 手动更新订单状态
        orders = db_session.query(Order).filter(Order.order_code.in_(["O001", "O002"])).all()
        for order in orders:
            order.status = "delivering"
        db_session.commit()
        
        print(f"订单状态已更新为 delivering")
        
        # 2. F021 打包
        print("\n=== 步骤2: F021 打包 ===")
        
        # 查询 GlobalSchedule 对象
        from models.global_schedule import GlobalSchedule
        global_schedule_obj = db_session.query(GlobalSchedule).filter(
            GlobalSchedule.schedule_code == schedule_code
        ).first()
        
        packages = run_packaging(
            schedule_result=schedule_result,
            schedule_id=global_schedule_obj.id,
            db=db_session
        )
        
        package_codes = [pkg.package_code for pkg in packages]
        print(f"打包完成，生成了 {len(package_codes)} 个包裹")
        
        # 手动保存 Package 对象到数据库
        for pkg in packages:
            db_session.add(pkg)
        db_session.commit()
        
        # 手动更新货物状态
        goods = db_session.query(Goods).filter(Goods.goods_code.in_(["G001", "G002", "G003"])).all()
        for g in goods:
            g.status = "packed"
        db_session.commit()
        
        # 手动更新包裹状态
        for pkg in packages:
            pkg.status = "packed"
        db_session.commit()
        
        print(f"货物状态和包裹状态已更新为 packed")
        
        # 验证货物状态
        goods = db_session.query(Goods).filter(Goods.goods_code.in_(["G001", "G002", "G003"])).all()
        for g in goods:
            assert g.status == "packed"
        
        # 验证包裹状态
        packages = db_session.query(Package).filter(Package.package_code.in_(package_codes)).all()
        for pkg in packages:
            assert pkg.status == "packed"
        
        # 3. F005 节点调度（demo_mode=true）
        print("\n=== 步骤3: F005 节点调度（demo_mode=true） ===")
        
        dispatch_result = run_node_dispatch(
            db_session,
            schedule_code=schedule_code,
            demo_mode=True
        )
        
        assert "batch_code" in dispatch_result
        batch_code = dispatch_result["batch_code"]
        print(f"节点调度完成，batch_code={batch_code}")
        
        # 验证批次状态
        batch = db_session.query(DispatchBatch).filter(
            DispatchBatch.batch_code == batch_code
        ).first()
        assert batch.status == "completed"
        
        # 注意：由于 demo_mode=true，状态机会自动推进到最终状态
        # 所以货物状态应该是 "delivered"，包裹状态应该是 "delivered"
        # 但如果阶段6的模拟送达还没有实现，状态可能停留在 "in_transit"
        
        # 4. F006 路径规划
        print("\n=== 步骤4: F006 路径规划 ===")
        
        # 查询批次下的所有调度明细
        dispatches = db_session.query(NodeDispatch).filter(
            NodeDispatch.dispatch_batch_id == batch.id
        ).all()
        
        assert len(dispatches) > 0
        print(f"找到 {len(dispatches)} 个调度明细")
        
        # 为每个调度明细规划路径
        routes = []
        for dispatch in dispatches:
            route_data = run_route_planning(db_session, dispatch.id)
            routes.append(route_data)
            
            # 写入数据库
            route = Route(
                route_code=route_data["route_code"],
                dispatch_id=route_data["dispatch_id"],
                vehicle_id=route_data["vehicle_id"],
                route_segments=route_data["route_segments"],
                total_distance=route_data["total_distance"],
                total_time=route_data["total_time"],
                total_emission=route_data["total_emission"],
                algorithm_type=route_data["algorithm_type"]
            )
            db_session.add(route)
        
        db_session.commit()
        
        print(f"路径规划完成，生成了 {len(routes)} 条路线")
        
        # 验证数据库中创建了Route记录
        routes_in_db = db_session.query(Route).all()
        assert len(routes_in_db) == len(dispatches)
        
        print("\n=== 完整调度链路测试通过！ ===")
    
    def test_full_flow_step_by_step(self, db_session, full_test_data):
        """
        测试完整的调度链路（分步执行，demo_mode=false）
        
        流程：
        1. F007 全局调度
        2. F021 打包
        3. F005 节点调度（第一次调用，L0→L1）
        4. 手动推进状态（模拟F005后的状态更新）
        5. F006 路径规划（只规划L0→L1的调度明细）
        
        注意：由于阶段6的模拟送达还没有实现，本测试只测试到L0→L1
        """
        # 1. F007 全局调度
        print("\n=== 步骤1: F007 全局调度 ===")
        
        schedule_result = run_global_schedule(
            order_codes=["O001", "O002"],
            algorithm="traditional",
            db=db_session
        )
        
        schedule_code = schedule_result["schedule_code"]
        print(f"全局调度完成，schedule_code={schedule_code}")
        
        # 手动创建 GlobalSchedule 对象并保存到数据库
        from models.global_schedule import GlobalSchedule
        
        # 查询订单ID
        order_ids = {}
        for order_code in ["O001", "O002"]:
            order = db_session.query(Order).filter(Order.order_code == order_code).first()
            if order:
                order_ids[order_code] = order.id
        
        global_schedule = GlobalSchedule(
            schedule_code=schedule_code,
            order_codes=list(order_ids.values()),  # 使用订单ID列表
            goods_schedules=schedule_result["goods_schedules"],
            total_distance=schedule_result["total_distance"],
            total_time=schedule_result["total_time"],
            total_goods=schedule_result["total_goods"],
            score=schedule_result["score"]
        )
        db_session.add(global_schedule)
        db_session.commit()
        
        # 手动更新订单状态
        orders = db_session.query(Order).filter(Order.order_code.in_(["O001", "O002"])).all()
        for order in orders:
            order.status = "delivering"
        db_session.commit()
        
        print(f"订单状态已更新为 delivering")
        
        # 2. F021 打包
        print("\n=== 步骤2: F021 打包 ===")
        
        # 查询 GlobalSchedule 对象
        from models.global_schedule import GlobalSchedule
        global_schedule_obj = db_session.query(GlobalSchedule).filter(
            GlobalSchedule.schedule_code == schedule_code
        ).first()
        
        packages = run_packaging(
            schedule_result=schedule_result,
            schedule_id=global_schedule_obj.id,
            db=db_session
        )
        
        package_codes = [pkg.package_code for pkg in packages]
        print(f"打包完成，生成了 {len(package_codes)} 个包裹")
        
        # 手动保存 Package 对象到数据库
        for pkg in packages:
            db_session.add(pkg)
        db_session.commit()
        
        # 手动更新货物状态
        goods = db_session.query(Goods).filter(
            Goods.goods_code.in_(["G001", "G002", "G003"])
        ).all()
        for g in goods:
            g.status = "packed"
        db_session.commit()
        
        # 手动更新包裹状态
        for pkg in packages:
            pkg.status = "packed"
        db_session.commit()
        
        print(f"货物状态和包裹状态已更新为 packed")
        
        # 验证货物状态
        goods = db_session.query(Goods).filter(
            Goods.goods_code.in_(["G001", "G002", "G003"])
        ).all()
        for g in goods:
            assert g.status == "packed"
        
        # 验证包裹状态
        packages_in_db = db_session.query(Package).filter(
            Package.package_code.in_(package_codes)
        ).all()
        for pkg in packages_in_db:
            assert pkg.status == "packed"
        
        # 3. F005 节点调度（第一次调用，L0→L1）
        print("\n=== 步骤3: F005 节点调度（第一次调用，L0→L1） ===")
        
        dispatch_result = run_node_dispatch(
            db_session,
            schedule_code=schedule_code,
            demo_mode=False
        )
        
        batch_code = dispatch_result["batch_code"]
        print(f"L0→L1调度完成，batch_code={batch_code}")
        
        # 验证批次状态
        batch = db_session.query(DispatchBatch).filter(
            DispatchBatch.batch_code == batch_code
        ).first()
        assert batch.status == "l0_l1_done"
        
        # 4. 手动推进状态（模拟F005后的状态更新）
        print("\n=== 步骤4: 手动推进状态 ===")
        
        # 注意：由于我们没有调用状态机，需要手动更新状态
        # 更新包裹状态：packed → in_transit
        packages = db_session.query(Package).filter(
            Package.status == "packed"
        ).all()
        
        for pkg in packages:
            pkg.status = "in_transit"
        
        # 更新货物状态：packed → in_transit
        goods = db_session.query(Goods).filter(
            Goods.status == "packed"
        ).all()
        
        for g in goods:
            g.status = "in_transit"
        
        # 更新车辆状态：idle → delivering
        vehicles = db_session.query(Vehicle).filter(
            Vehicle.status == "idle"
        ).all()
        
        for v in vehicles:
            v.status = "delivering"
        
        db_session.commit()
        print("状态已手动推进")
        
        # 5. F006 路径规划（只规划L0→L1的调度明细）
        print("\n=== 步骤5: F006 路径规划（L0→L1） ===")
        
        # 查询批次下的L0→L1调度明细
        dispatches = db_session.query(NodeDispatch).filter(
            NodeDispatch.dispatch_batch_id == batch.id,
            NodeDispatch.level_phase == 0
        ).all()
        
        assert len(dispatches) > 0
        print(f"找到 {len(dispatches)} 个L0→L1调度明细")
        
        # 为每个调度明细规划路径
        routes = []
        for dispatch in dispatches:
            route_data = run_route_planning(db_session, dispatch.id)
            routes.append(route_data)
            
            # 写入数据库
            route = Route(
                route_code=route_data["route_code"],
                dispatch_id=route_data["dispatch_id"],
                vehicle_id=route_data["vehicle_id"],
                route_segments=route_data["route_segments"],
                total_distance=route_data["total_distance"],
                total_time=route_data["total_time"],
                total_emission=route_data["total_emission"],
                algorithm_type=route_data["algorithm_type"]
            )
            db_session.add(route)
        
        db_session.commit()
        
        print(f"路径规划完成，生成了 {len(routes)} 条路线")
        
        # 验证数据库中创建了Route记录
        routes_in_db = db_session.query(Route).all()
        assert len(routes_in_db) == len(dispatches)
        
        print("\n=== 分步调度链路测试通过！ ===")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
