"""
F006 路径规划算法单元测试

测试 run_route_planning() 函数的各种场景
使用真实的数据库会话，确保算法正确性
"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base
from models.node import Node
from models.vehicle import Vehicle
from models.node_dispatch import NodeDispatch
from models.dispatch_batch import DispatchBatch
from models.global_schedule import GlobalSchedule
from models.package import Package
from algorithms.route_planning import run_route_planning, _haversine, _generate_route_code


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
def test_data(db_session):
    """
    创建测试数据
    
    包含：
    1. 节点（存储中心、分拣中心）
    2. 车辆
    3. 调度批次
    4. 节点调度明细
    """
    # 1. 创建节点
    nodes = [
        Node(node_code="SC001", name="存储中心1", location="武汉",
             latitude=30.5, longitude=114.3, node_type="storage_center"),
        Node(node_code="SO001", name="1级分拣中心1", location="武汉",
             latitude=30.6, longitude=114.4, node_type="sorting_center"),
        Node(node_code="SO010", name="0级分拣中心1", location="武昌",
             latitude=30.54, longitude=114.315, node_type="sorting_center"),
    ]
    
    for node in nodes:
        db_session.add(node)
    db_session.flush()
    
    # 2. 创建车辆
    vehicles = [
        Vehicle(vehicle_code="VEH001", model="测试车型", capacity=100.0,
                energy_type="fuel", node_id=nodes[0].id,
                last_arrived_node_id=nodes[0].id, status="idle"),
        Vehicle(vehicle_code="VEH002", model="测试车型2", capacity=200.0,
                energy_type="electric", node_id=nodes[0].id,
                last_arrived_node_id=nodes[0].id, status="idle"),
    ]
    
    for vehicle in vehicles:
        db_session.add(vehicle)
    db_session.flush()
    
    # 3. 创建调度批次
    batch = DispatchBatch(
        batch_code="BATCH20260617001",
        global_schedule_id=1,
        status="pending",
        demo_mode=True
    )
    db_session.add(batch)
    db_session.flush()
    
    # 4. 创建节点调度明细（L0→L1）
    dispatch_l0_l1 = NodeDispatch(
        dispatch_code="DISP20260617001",
        dispatch_batch_id=batch.id,
        vehicle_id=vehicles[0].id,
        driver_id=None,
        level_phase=0,
        tasks=[
            {
                "from_node_code": "SC001",
                "to_node_code": "SO001",
                "package_codes": ["PKG001"],
                "is_return": False
            },
            {
                "from_node_code": "SO001",
                "to_node_code": "SC001",
                "package_codes": [],
                "is_return": True
            }
        ],
        total_distance=50.0,
        total_time=5.0
    )
    db_session.add(dispatch_l0_l1)
    db_session.flush()
    
    # 5. 创建节点调度明细（L1→L2）
    dispatch_l1_l2 = NodeDispatch(
        dispatch_code="DISP20260617002",
        dispatch_batch_id=batch.id,
        vehicle_id=vehicles[1].id,
        driver_id=None,
        level_phase=1,
        tasks=[
            {
                "from_node_code": "SO001",
                "to_node_code": "SO010",
                "package_codes": ["PKG002"],
                "is_return": False
            }
        ],
        total_distance=30.0,
        total_time=3.0
    )
    db_session.add(dispatch_l1_l2)
    db_session.flush()
    
    # 提交事务
    db_session.commit()
    
    return {
        "nodes": nodes,
        "vehicles": vehicles,
        "batch": batch,
        "dispatch_l0_l1": dispatch_l0_l1,
        "dispatch_l1_l2": dispatch_l1_l2
    }


class TestHaversine:
    """测试 Haversine 距离计算函数"""
    
    def test_same_point(self):
        """测试同一点距离为0"""
        distance = _haversine(30.5, 114.3, 30.5, 114.3)
        assert distance == 0.0
    
    def test_known_distance(self):
        """测试已知距离（武汉站到武昌站）"""
        # 武汉站：30.6026, 114.4166
        # 武昌站：30.5422, 114.3147
        distance = _haversine(30.6026, 114.4166, 30.5422, 114.3147)
        # 实际距离约 12-15 公里
        assert 10.0 < distance < 20.0
    
    def test_negative_coordinates(self):
        """测试负坐标（南半球、西半球）"""
        distance = _haversine(-30.5, -114.3, -30.6, -114.4)
        assert distance > 0


class TestGenerateRouteCode:
    """测试路线编码生成函数"""
    
    def test_generate_first_code(self, db_session):
        """测试生成第一个路线编码"""
        code = _generate_route_code(db_session)
        assert code.startswith("ROUTE")
        # ROUTE(5) + YYYYMMDD(8) + 3位序号 = 16
        assert len(code) == 16
    
    def test_generate_multiple_codes(self, db_session):
        """测试生成多个路线编码，序号递增"""
        code1 = _generate_route_code(db_session)
        
        # 创建一个Route对象并添加到数据库，以模拟已存在的路线
        from models.route import Route
        route = Route(
            route_code=code1,
            dispatch_id=1,
            vehicle_id=1,
            route_segments=[],
            total_distance=0,
            total_time=0,
            total_emission=0,
            algorithm_type="traditional"
        )
        db_session.add(route)
        db_session.commit()
        
        code2 = _generate_route_code(db_session)
        
        # 提取序号
        seq1 = int(code1[-3:])
        seq2 = int(code2[-3:])
        
        assert seq2 == seq1 + 1


class TestRunRoutePlanning:
    """测试 run_route_planning() 函数"""
    
    def test_success_l0_to_l1(self, db_session, test_data):
        """
        测试成功规划 L0→L1 路径
        
        场景：
        1. 从存储中心到1级分拣中心
        2. 包含去程和返程
        """
        dispatch = test_data["dispatch_l0_l1"]
        
        # 调用算法
        route_data = run_route_planning(db_session, dispatch.id)
        
        # 验证返回数据
        assert "route_code" in route_data
        assert "dispatch_id" in route_data
        assert "vehicle_id" in route_data
        assert "route_segments" in route_data
        assert "total_distance" in route_data
        assert "total_time" in route_data
        assert "total_emission" in route_data
        assert "algorithm_type" in route_data
        
        # 验证 route_segments
        assert len(route_data["route_segments"]) == 2  # 去程 + 返程
        assert route_data["route_segments"][0]["road_name"] == "虚拟道路"
        
        # 验证距离和时间
        assert route_data["total_distance"] > 0
        assert route_data["total_time"] > 0
        
        # 验证碳排放（燃油车）
        assert route_data["total_emission"] > 0
    
    def test_success_l1_to_l2(self, db_session, test_data):
        """
        测试成功规划 L1→L2 路径
        
        场景：
        1. 从1级分拣中心到0级分拣中心
        2. 只有去程，没有返程
        """
        dispatch = test_data["dispatch_l1_l2"]
        
        # 调用算法
        route_data = run_route_planning(db_session, dispatch.id)
        
        # 验证返回数据
        assert "route_code" in route_data
        assert len(route_data["route_segments"]) == 1  # 只有去程
        
        # 验证碳排放（电动车）
        vehicle = test_data["vehicles"][1]
        if vehicle.energy_type == "electric":
            assert route_data["total_emission"] == 0.0
    
    def test_dispatch_not_found(self, db_session):
        """测试 dispatch_id 不存在，应该抛出异常"""
        with pytest.raises(ValueError) as exc_info:
            run_route_planning(db_session, 999)
        
        assert "节点调度明细不存在" in str(exc_info.value)
    
    def test_vehicle_not_found(self, db_session, test_data):
        """
        测试车辆不存在，应该抛出异常
        
        场景：
        手动设置一个不存在的 vehicle_id
        """
        dispatch = test_data["dispatch_l0_l1"]
        dispatch.vehicle_id = 999
        db_session.flush()
        
        with pytest.raises(ValueError) as exc_info:
            run_route_planning(db_session, dispatch.id)
        
        assert "车辆不存在" in str(exc_info.value)
    
    def test_empty_tasks(self, db_session, test_data):
        """
        测试任务列表为空，应该返回空的 route_segments
        
        场景：
        手动设置空的 tasks
        """
        dispatch = test_data["dispatch_l0_l1"]
        # 注意：根据 route_planning.py 的代码，如果 tasks 为空或不是列表，会抛出 ValueError
        # 所以这个测试应该验证是否抛出了 ValueError
        dispatch.tasks = None
        db_session.flush()
        
        # 调用算法，应该抛出 ValueError
        with pytest.raises(ValueError) as exc_info:
            run_route_planning(db_session, dispatch.id)
        
        assert "任务列表为空或格式错误" in str(exc_info.value)
    
    def test_invalid_task_format(self, db_session, test_data):
        """
        测试任务格式错误，应该跳过该任务
        
        场景：
        任务缺少 from_node_code 或 to_node_code
        """
        dispatch = test_data["dispatch_l0_l1"]
        dispatch.tasks = [
            {
                "from_node_code": "SC001",
                # 缺少 to_node_code
                "package_codes": ["PKG001"],
                "is_return": False
            }
        ]
        db_session.flush()
        
        # 调用算法
        route_data = run_route_planning(db_session, dispatch.id)
        
        # 验证返回数据（应该跳过无效任务）
        assert len(route_data["route_segments"]) == 0
    
    def test_node_not_found(self, db_session, test_data):
        """
        测试节点不存在，应该跳过该任务
        
        场景：
        任务中的节点编码不存在
        """
        dispatch = test_data["dispatch_l0_l1"]
        dispatch.tasks = [
            {
                "from_node_code": "INVALID_NODE",
                "to_node_code": "SO001",
                "package_codes": ["PKG001"],
                "is_return": False
            }
        ]
        db_session.flush()
        
        # 调用算法
        route_data = run_route_planning(db_session, dispatch.id)
        
        # 验证返回数据（应该跳过无效任务）
        assert len(route_data["route_segments"]) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
