"""
服务单元测试：RouteService（路线服务）

测试目标：
- RouteService.create_route_planning 方法的正常流程和异常流程
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
        
        # Mock 路径规划算法 - 修复mock路径
        with patch("algorithms.route_planning.run_route_planning") as mock_route:
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
        
        # Mock 路径规划算法抛出异常 - 修复mock路径
        with patch("algorithms.route_planning.run_route_planning") as mock_route:
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
        )
        db_session.add(route)
        db_session.commit()
        
        # 查询路线列表
        result = await RouteService.get_routes(
            batch_code=None,
            vehicle_code=None,
            page=1,
            page_size=20,
            db=db_session
        )
        
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
        )
        db_session.add(route)
        db_session.commit()
        
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
