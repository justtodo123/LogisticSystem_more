"""
<<<<<<< HEAD:src/backend/tests/unit/services/test_route_service.py
服务单元测试：RouteService（路线服务）

测试目标：
- RouteService.create_route 方法的正常流程和异常流程
- 验证服务层业务逻辑、路径规划、错误处理
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from services.route_service import RouteService
from models.route import Route
from models.node_dispatch import NodeDispatch
from models.vehicle import Vehicle
from models.node import Node


class TestCreateRoutePlanning:
    """测试创建路线规划"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_route_planning_success(self, db_session, test_nodes, test_vehicles):
        """
        测试成功创建路线规划：
        1. 创建测试批次和节点调度记录
        2. 调用 create_route_planning(batch_code, dispatch_codes, db)
        3. 验证返回成功
        4. 验证 routes 表有记录
        """
        from models.node_dispatch import NodeDispatch
        from models.dispatch_batch import DispatchBatch
        from models.route import Route
        import json
        
        # 创建测试批次（需要先创建GlobalSchedule，因为DispatchBatch.global_schedule_id是NOT NULL）
        from models.global_schedule import GlobalSchedule
        import json
        global_schedule = GlobalSchedule(
            schedule_code="GS001",
            order_codes=json.dumps([]),
            total_distance=0.0,
            total_time=0.0,
            total_goods=0,
            score=0.0,
            algorithm_type="traditional",
            version=1,
            is_replan=False,
            goods_schedules=json.dumps([])
        )
        db_session.add(global_schedule)
        db_session.commit()
        
        dispatch_batch = DispatchBatch(
            batch_code="BATCH001",
            global_schedule_id=global_schedule.id,
            status="pending"
        )
        db_session.add(dispatch_batch)
        db_session.commit()
        
        # 创建测试节点调度记录
        node_dispatch = NodeDispatch(
            dispatch_code="ND001",
            dispatch_batch_id=dispatch_batch.id,
            vehicle_id=test_vehicles["VEH001"].id,
            driver_id=1,
            level_phase=0,
            tasks=json.dumps([{"from_node_code": "SC001", "to_node_code": "SO001", "package_codes": ["PKG001"], "is_return": False}]),
            total_distance=10.0,
            total_time=30.0,
        )
        db_session.add(node_dispatch)
        db_session.commit()
        
        # Mock 路径规划算法
        with patch("services.route_service.run_route_planning") as mock_route:
            mock_route.return_value = {
                "route_code": "RT001",
                "dispatch_id": node_dispatch.id,
                "vehicle_id": test_vehicles["VEH001"].id,
                "route_segments": [{"road_name": "测试路段", "start_lng": 114.28, "start_lat": 30.52, "end_lng": 114.29, "end_lat": 30.51}],
                "total_distance": 15.5,
                "total_time": 45.0,
                "total_emission": 3.1,
                "algorithm_type": "traditional"
            }
            
            # 调用路线服务
            result = await RouteService.create_route_planning(
                batch_code="BATCH001",
                dispatch_codes=None,
                db=db_session,
            )
        
        # 验证响应
        assert result["code"] == 0
        assert "data" in result
        
        # 验证 routes 表有记录
        db_session.flush()  # 刷新会话，使pending对象同步到数据库
        route_list = db_session.query(Route).all()
        assert len(route_list) >= 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_route_planning_batch_not_found(self, db_session):
        """
        测试批次不存在：
        1. 调用 create_route_planning("NONEXIST", None, db)
        2. 验证返回业务错误
        """
        result = await RouteService.create_route_planning(
            batch_code="NONEXIST",  # 不存在的批次
            dispatch_codes=None,
            db=db_session,
        )
        
        # 验证响应（业务错误）
        assert result["code"] != 0
        assert "批次" in result["message"] or "不存在" in result["message"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_route_planning_algorithm_error(self, db_session, test_nodes, test_vehicles):
        """
        测试路径规划算法错误：
        1. 创建测试批次和节点调度记录
        2. Mock 路径规划算法抛出异常
        3. 调用 create_route_planning
        4. 验证返回业务错误
        """
        from models.node_dispatch import NodeDispatch
        from models.dispatch_batch import DispatchBatch
        import json
        
        # 创建测试批次（需要先创建GlobalSchedule，因为DispatchBatch.global_schedule_id是NOT NULL）
        from models.global_schedule import GlobalSchedule
        import json
        global_schedule = GlobalSchedule(
            schedule_code="GS002",
            order_codes=json.dumps([]),
            total_distance=0.0,
            total_time=0.0,
            total_goods=0,
            score=0.0,
            algorithm_type="traditional",
            version=1,
            is_replan=False,
            goods_schedules=json.dumps([])
        )
        db_session.add(global_schedule)
        db_session.commit()
        
        dispatch_batch = DispatchBatch(
            batch_code="BATCH002",
            global_schedule_id=global_schedule.id,
            status="pending"
        )
        db_session.add(dispatch_batch)
        db_session.commit()
        
        # 创建测试节点调度记录
        node_dispatch = NodeDispatch(
            dispatch_code="ND002",
            dispatch_batch_id=dispatch_batch.id,
            vehicle_id=test_vehicles["VEH001"].id,
            driver_id=1,
            level_phase=0,
            tasks=json.dumps([{"from_node_code": "SC001", "to_node_code": "SO001", "package_codes": ["PKG001"], "is_return": False}]),
            total_distance=10.0,
            total_time=30.0,
        )
        db_session.add(node_dispatch)
        db_session.commit()
        
        # Mock 路径规划算法抛出异常
        with patch("services.route_service.run_route_planning") as mock_route:
            mock_route.side_effect = Exception("模拟路径规划算法失败")
            
            result = await RouteService.create_route_planning(
                batch_code="BATCH002",
                dispatch_codes=None,
                db=db_session,
            )
        
        # 验证响应（业务错误）
        assert result["code"] != 0
        assert "路径规划" in result["message"] or "失败" in result["message"]


class TestGetRoutes:
    """测试查询路线列表"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_routes_empty(self, db_session):
        """测试空数据库返回空列表"""
        result = await RouteService.get_routes(
            batch_code=None,
            vehicle_code=None,
            page=1,
            page_size=20,
            db=db_session
        )
        
        assert result["code"] == 0
        assert result["data"]["items"] == []
        assert result["data"]["total"] == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_routes_with_data(self, db_session, test_nodes, test_vehicles):
        """测试有数据时返回路线列表"""
        # 先创建一条路线记录
        from models.route import Route
        from models.node_dispatch import NodeDispatch
        from models.dispatch_batch import DispatchBatch
        import json
        
        # 创建测试批次和节点调度记录（因为 Route.dispatch_id 是外键）
        # 需要先创建GlobalSchedule，因为DispatchBatch.global_schedule_id是NOT NULL
        from models.global_schedule import GlobalSchedule
        import json
        global_schedule = GlobalSchedule(
            schedule_code="GS003",
            order_codes=json.dumps([]),
            total_distance=0.0,
            total_time=0.0,
            total_goods=0,
            score=0.0,
            algorithm_type="traditional",
            version=1,
            is_replan=False,
            goods_schedules=json.dumps([])
        )
        db_session.add(global_schedule)
        db_session.commit()
        
        dispatch_batch = DispatchBatch(
            batch_code="BATCH_ROUTE001",
            global_schedule_id=global_schedule.id,
            status="pending"
        )
        db_session.add(dispatch_batch)
        db_session.commit()
        
        node_dispatch = NodeDispatch(
            dispatch_code="ND_ROUTE001",
            dispatch_batch_id=dispatch_batch.id,
            vehicle_id=test_vehicles["VEH001"].id,
            driver_id=1,
            level_phase=0,
            tasks=json.dumps([{"from_node_code": "SC001", "to_node_code": "SO001", "package_codes": ["PKG001"], "is_return": False}]),
            total_distance=10.0,
            total_time=30.0,
        )
        db_session.add(node_dispatch)
        db_session.commit()
        
        route = Route(
            route_code="RT001",
            dispatch_id=node_dispatch.id,
            vehicle_id=test_vehicles["VEH001"].id,
            total_distance=15.5,
            total_time=45.0,
            total_emission=3.1,
            route_segments=json.dumps([{"road_name": "测试路段", "start_lng": 114.28, "start_lat": 30.52, "end_lng": 114.29, "end_lat": 30.51}]),
            algorithm_type="traditional"
=======
RouteService 服务层单元测试

测试 RouteService 类的各种方法
使用真实的数据库会话，确保服务层正确性
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
from models.route import Route
from services.route_service import RouteService


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
    ]
    
    for node in nodes:
        db_session.add(node)
    db_session.flush()
    
    # 2. 创建车辆
    vehicles = [
        Vehicle(vehicle_code="VEH001", model="测试车型", capacity=100.0,
                energy_type="fuel", node_id=nodes[0].id,
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
    
    # 4. 创建节点调度明细
    dispatch = NodeDispatch(
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
            }
        ],
        total_distance=50.0,
        total_time=5.0
    )
    db_session.add(dispatch)
    db_session.flush()
    
    # 提交事务
    db_session.commit()
    
    return {
        "nodes": nodes,
        "vehicles": vehicles,
        "batch": batch,
        "dispatch": dispatch
    }


class TestCreateRoutePlanning:
    """测试 RouteService.create_route_planning() 方法"""
    
    @pytest.mark.asyncio
    async def test_success(self, db_session, test_data):
        """
        测试成功创建路径规划
        
        场景：
        1. 批次存在
        2. 有一个调度明细
        3. 成功规划路径并写入数据库
        """
        batch = test_data["batch"]
        
        # 调用服务方法
        result = await RouteService.create_route_planning(
            batch_code=batch.batch_code,
            dispatch_codes=None,
            db=db_session
        )
        
        # 验证结果
        assert result["code"] == 0
        assert "data" in result
        assert "routes" in result["data"]
        assert len(result["data"]["routes"]) == 1
        
        # 提交事务，使Route记录可见
        db_session.commit()
        
        # 验证数据库中创建了Route记录
        routes = db_session.query(Route).all()
        assert len(routes) == 1
        
        # 验证Route记录的字段
        route = routes[0]
        assert route.dispatch_id == test_data["dispatch"].id
        assert route.vehicle_id == test_data["vehicles"][0].id
        assert route.route_segments is not None
        assert route.total_distance > 0
        assert route.total_time > 0
    
    @pytest.mark.asyncio
    async def test_batch_not_found(self, db_session):
        """测试批次不存在，返回错误"""
        # 调用服务方法（使用不存在的批次编码）
        result = await RouteService.create_route_planning(
            batch_code="BATCH_INVALID",
            dispatch_codes=None,
            db=db_session
        )
        
        # 验证结果
        assert result["code"] != 0
        assert "批次不存在" in result["message"]
    
    @pytest.mark.asyncio
    async def test_no_dispatches(self, db_session, test_data):
        """
        测试批次存在但没有调度明细，返回错误
        
        场景：
        手动删除所有调度明细
        """
        batch = test_data["batch"]
        
        # 删除所有调度明细
        db_session.query(NodeDispatch).delete()
        db_session.commit()
        
        # 调用服务方法
        result = await RouteService.create_route_planning(
            batch_code=batch.batch_code,
            dispatch_codes=None,
            db=db_session
        )
        
        # 验证结果
        assert result["code"] != 0
        assert "没有可处理的调度明细" in result["message"]
    
    @pytest.mark.asyncio
    async def test_specific_dispatch_codes(self, db_session, test_data):
        """
        测试指定 dispatch_codes 参数
        
        场景：
        只规划指定的调度明细
        """
        batch = test_data["batch"]
        dispatch = test_data["dispatch"]
        
        # 调用服务方法（指定 dispatch_codes）
        result = await RouteService.create_route_planning(
            batch_code=batch.batch_code,
            dispatch_codes=[dispatch.dispatch_code],
            db=db_session
        )
        
        # 验证结果
        assert result["code"] == 0
        assert len(result["data"]["routes"]) == 1


class TestGetRoutes:
    """测试 RouteService.get_routes() 方法"""
    
    @pytest.mark.asyncio
    async def test_success(self, db_session, test_data):
        """
        测试成功查询路线列表
        
        场景：
        1. 数据库中有一条路线记录
        2. 成功查询并返回
        """
        # 先创建一条路线记录
        from algorithms.route_planning import run_route_planning
        
        dispatch = test_data["dispatch"]
        route_data = run_route_planning(db_session, dispatch.id)
        
        route = Route(
            route_code=route_data["route_code"],
            dispatch_id=route_data["dispatch_id"],
            vehicle_id=route_data["vehicle_id"],
            route_segments=route_data["route_segments"],
            total_distance=route_data["total_distance"],
            total_time=route_data["total_time"],
            total_emission=route_data["total_emission"],
            algorithm_type=route_data["algorithm_type"]
>>>>>>> backend/phase-5:src/backend/tests/test_services/test_route_service.py
        )
        db_session.add(route)
        db_session.commit()
        
<<<<<<< HEAD:src/backend/tests/unit/services/test_route_service.py
        # 查询路线列表
=======
        # 调用服务方法
>>>>>>> backend/phase-5:src/backend/tests/test_services/test_route_service.py
        result = await RouteService.get_routes(
            batch_code=None,
            vehicle_code=None,
            page=1,
            page_size=20,
            db=db_session
        )
        
<<<<<<< HEAD:src/backend/tests/unit/services/test_route_service.py
        assert result["code"] == 0
        assert len(result["data"]["items"]) == 1
        assert result["data"]["total"] == 1
        assert result["data"]["items"][0]["route_code"] == "RT001"


class TestGetRouteDetail:
    """测试查询路线详情"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_route_detail_success(self, db_session, test_nodes, test_vehicles):
        """测试成功获取路线详情"""
        # 先创建一条路线记录
        from models.route import Route
        from models.node_dispatch import NodeDispatch
        from models.dispatch_batch import DispatchBatch
        import json
        
        # 创建测试批次和节点调度记录（因为 Route.dispatch_id 是外键）
        # 需要先创建GlobalSchedule，因为DispatchBatch.global_schedule_id是NOT NULL
        from models.global_schedule import GlobalSchedule
        import json
        global_schedule = GlobalSchedule(
            schedule_code="GS004",
            order_codes=json.dumps([]),
            total_distance=0.0,
            total_time=0.0,
            total_goods=0,
            score=0.0,
            algorithm_type="traditional",
            version=1,
            is_replan=False,
            goods_schedules=json.dumps([])
        )
        db_session.add(global_schedule)
        db_session.commit()
        
        dispatch_batch = DispatchBatch(
            batch_code="BATCH_ROUTE002",
            global_schedule_id=global_schedule.id,
            status="pending"
        )
        db_session.add(dispatch_batch)
        db_session.commit()
        
        node_dispatch = NodeDispatch(
            dispatch_code="ND_ROUTE002",
            dispatch_batch_id=dispatch_batch.id,
            vehicle_id=test_vehicles["VEH001"].id,
            driver_id=1,
            level_phase=0,
            tasks=json.dumps([{"from_node_code": "SC001", "to_node_code": "SO001", "package_codes": ["PKG001"], "is_return": False}]),
            total_distance=10.0,
            total_time=30.0,
        )
        db_session.add(node_dispatch)
        db_session.commit()
        
        route = Route(
            route_code="RT001",
            dispatch_id=node_dispatch.id,
            vehicle_id=test_vehicles["VEH001"].id,
            total_distance=15.5,
            total_time=45.0,
            total_emission=3.1,
            route_segments=json.dumps([{"road_name": "测试路段", "start_lng": 114.28, "start_lat": 30.52, "end_lng": 114.29, "end_lat": 30.51}]),
            algorithm_type="traditional"
=======
        # 验证结果
        assert result["code"] == 0
        assert "data" in result
        assert "items" in result["data"]
        assert len(result["data"]["items"]) == 1
    
    @pytest.mark.asyncio
    async def test_filter_by_batch_code(self, db_session, test_data):
        """
        测试按 batch_code 筛选
        
        场景：
        只查询指定批次的路线
        """
        # 先创建一条路线记录
        from algorithms.route_planning import run_route_planning
        
        dispatch = test_data["dispatch"]
        route_data = run_route_planning(db_session, dispatch.id)
        
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
        
        # 调用服务方法（按 batch_code 筛选）
        result = await RouteService.get_routes(
            batch_code=test_data["batch"].batch_code,
            vehicle_code=None,
            page=1,
            page_size=20,
            db=db_session
        )
        
        # 验证结果
        assert result["code"] == 0
        assert len(result["data"]["items"]) == 1
    
    @pytest.mark.asyncio
    async def test_filter_by_vehicle_code(self, db_session, test_data):
        """
        测试按 vehicle_code 筛选
        
        场景：
        只查询指定车辆的路线
        """
        # 先创建一条路线记录
        from algorithms.route_planning import run_route_planning
        
        dispatch = test_data["dispatch"]
        route_data = run_route_planning(db_session, dispatch.id)
        
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
        
        # 调用服务方法（按 vehicle_code 筛选）
        result = await RouteService.get_routes(
            batch_code=None,
            vehicle_code=test_data["vehicles"][0].vehicle_code,
            page=1,
            page_size=20,
            db=db_session
        )
        
        # 验证结果
        assert result["code"] == 0
        assert len(result["data"]["items"]) == 1
    
    @pytest.mark.asyncio
    async def test_pagination(self, db_session, test_data):
        """
        测试分页功能
        
        场景：
        有多条路线记录，按页码和每页数量返回
        """
        # 先创建多条路线记录
        from algorithms.route_planning import run_route_planning
        
        dispatch = test_data["dispatch"]
        
        for i in range(5):
            route_data = run_route_planning(db_session, dispatch.id)
            
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
        
        # 调用服务方法（分页）
        result = await RouteService.get_routes(
            batch_code=None,
            vehicle_code=None,
            page=1,
            page_size=2,
            db=db_session
        )
        
        # 验证结果
        assert result["code"] == 0
        assert len(result["data"]["items"]) == 2
        assert result["data"]["total"] == 5


class TestGetRouteDetail:
    """测试 RouteService.get_route_detail() 方法"""
    
    @pytest.mark.asyncio
    async def test_success(self, db_session, test_data):
        """
        测试成功查询路线详情
        
        场景：
        1. 路线存在
        2. 成功查询并返回详情
        """
        # 先创建一条路线记录
        from algorithms.route_planning import run_route_planning
        
        dispatch = test_data["dispatch"]
        route_data = run_route_planning(db_session, dispatch.id)
        
        route = Route(
            route_code=route_data["route_code"],
            dispatch_id=route_data["dispatch_id"],
            vehicle_id=route_data["vehicle_id"],
            route_segments=route_data["route_segments"],
            total_distance=route_data["total_distance"],
            total_time=route_data["total_time"],
            total_emission=route_data["total_emission"],
            algorithm_type=route_data["algorithm_type"]
>>>>>>> backend/phase-5:src/backend/tests/test_services/test_route_service.py
        )
        db_session.add(route)
        db_session.commit()
        
<<<<<<< HEAD:src/backend/tests/unit/services/test_route_service.py
        # 获取路线详情
        result = await RouteService.get_route_detail(
            route_code="RT001", db=db_session
        )
        
        assert result["code"] == 0
        assert result["data"]["route_code"] == "RT001"
        assert "route_segments" in result["data"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_route_detail_not_found(self, db_session):
        """测试路线不存在"""
        result = await RouteService.get_route_detail(
            route_code="RT_NONEXIST", db=db_session
        )
        
        assert result["code"] != 0
        assert "路线" in result["message"] or "不存在" in result["message"]
=======
        # 调用服务方法
        result = await RouteService.get_route_detail(
            route_code=route.route_code,
            db=db_session
        )
        
        # 验证结果
        assert result["code"] == 0
        assert "data" in result
        assert "route_segments" in result["data"]
        assert "total_distance" in result["data"]
        assert "total_time" in result["data"]
    
    @pytest.mark.asyncio
    async def test_route_not_found(self, db_session):
        """测试路线不存在，返回404错误"""
        # 调用服务方法（使用不存在的路线编码）
        result = await RouteService.get_route_detail(
            route_code="ROUTE_INVALID",
            db=db_session
        )
        
        # 验证结果
        assert result["code"] == 40400
        assert "路线不存在" in result["message"]


class TestGetRouteCoordinates:
    """测试 RouteService.get_route_coordinates() 方法"""
    
    @pytest.mark.asyncio
    async def test_success(self, db_session, test_data):
        """
        测试成功查询车辆路线坐标
        
        场景：
        1. 车辆存在
        2. 车辆有一条路线记录
        3. 成功查询并返回坐标
        """
        # 先创建一条路线记录
        from algorithms.route_planning import run_route_planning
        
        dispatch = test_data["dispatch"]
        route_data = run_route_planning(db_session, dispatch.id)
        
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
        
        # 调用服务方法
        result = await RouteService.get_route_coordinates(
            vehicle_code=test_data["vehicles"][0].vehicle_code,
            batch_code=None,
            db=db_session
        )
        
        # 验证结果
        assert result["code"] == 0
        assert "data" in result
        assert "routes" in result["data"]
        assert len(result["data"]["routes"]) == 1
        assert "coordinates" in result["data"]["routes"][0]
    
    @pytest.mark.asyncio
    async def test_vehicle_not_found(self, db_session):
        """测试车辆不存在，返回404错误"""
        # 调用服务方法（使用不存在的车辆编码）
        result = await RouteService.get_route_coordinates(
            vehicle_code="VEH_INVALID",
            batch_code=None,
            db=db_session
        )
        
        # 验证结果
        assert result["code"] == 40400
        assert "车辆不存在" in result["message"]
    
    @pytest.mark.asyncio
    async def test_filter_by_batch_code(self, db_session, test_data):
        """
        测试按 batch_code 筛选车辆路线坐标
        
        场景：
        只查询指定批次的路线坐标
        """
        # 先创建一条路线记录
        from algorithms.route_planning import run_route_planning
        
        dispatch = test_data["dispatch"]
        route_data = run_route_planning(db_session, dispatch.id)
        
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
        
        # 调用服务方法（按 batch_code 筛选）
        result = await RouteService.get_route_coordinates(
            vehicle_code=test_data["vehicles"][0].vehicle_code,
            batch_code=test_data["batch"].batch_code,
            db=db_session
        )
        
        # 验证结果
        assert result["code"] == 0
        assert len(result["data"]["routes"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
>>>>>>> backend/phase-5:src/backend/tests/test_services/test_route_service.py
