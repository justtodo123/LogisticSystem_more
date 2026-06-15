"""
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


@pytest.mark.skip(reason="需要重写测试以匹配 RouteService.create_route_planning 方法")
class TestCreateRoute:
    """测试创建路线"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_route_success(self, db_session, test_nodes, test_vehicles):
        """
        测试成功创建路线：
        1. 创建测试节点调度记录（node_dispatch）
        2. 调用 create_route(node_dispatch_id, db)
        3. 验证返回成功，生成 route_code
        4. 验证 routes 表有记录
        """
        # 创建测试节点调度记录
        from models.node_dispatch import NodeDispatch
        import json
        
        node_dispatch = NodeDispatch(
            dispatch_code="ND001",
            dispatch_batch_id=1,  # 假设有一个batch
            vehicle_id=test_vehicles["VEH001"].id,
            driver_id=1,  # 假设有一个driver
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO001"].id,
            level_phase=0,
            status="pending",
            tasks=json.dumps([{"from_node_code": "SC001", "to_node_code": "SO001", "package_codes": ["PKG001"], "is_return": False}]),
        )
        db_session.add(node_dispatch)
        db_session.commit()
        
        # 调用路线服务
        result = await RouteService.create_route(
            node_dispatch_id=node_dispatch.id,
            db=db_session,
        )
        
        # 验证响应
        assert result["code"] == 0
        assert "data" in result
        assert "route_code" in result["data"]
        
        # 验证 routes 表有记录
        route_list = db_session.query(Route).all()
        assert len(route_list) >= 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_route_node_dispatch_not_found(self, db_session):
        """
        测试节点调度记录不存在：
        1. 调用 create_route(999, db)
        2. 验证返回业务错误
        """
        result = await RouteService.create_route(
            node_dispatch_id=999,  # 不存在的ID
            db=db_session,
        )
        
        # 验证响应（业务错误）
        assert result["code"] != 0
        assert "调度" in result["message"] or "不存在" in result["message"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_route_algorithm_error(self, db_session, test_nodes, test_vehicles):
        """
        测试路径规划算法错误：
        1. 创建测试节点调度记录
        2. Mock 路径规划算法抛出异常
        3. 调用 create_route
        4. 验证返回业务错误
        """
        # 创建测试节点调度记录
        from models.node_dispatch import NodeDispatch
        import json
        
        node_dispatch = NodeDispatch(
            dispatch_code="ND001",
            dispatch_batch_id=1,
            vehicle_id=test_vehicles["VEH001"].id,
            driver_id=1,
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO001"].id,
            level_phase=0,
            status="pending",
            tasks=json.dumps([{"from_node_code": "SC001", "to_node_code": "SO001", "package_codes": ["PKG001"], "is_return": False}]),
        )
        db_session.add(node_dispatch)
        db_session.commit()
        
        # Mock 路径规划算法抛出异常
        with patch("services.route_service.route_planning") as mock_route:
            mock_route.side_effect = Exception("模拟路径规划算法失败")
            
            result = await RouteService.create_route(
                node_dispatch_id=node_dispatch.id,
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
        import json
        
        route = Route(
            route_code="RT001",
            dispatch_id=1,
            vehicle_id=test_vehicles["VEH001"].id,
            total_distance=15.5,
            total_time=45.0,
            total_emission=3.1,
            route_segments=json.dumps([{"road_name": "测试路段", "start_lng": 114.28, "start_lat": 30.52, "end_lng": 114.29, "end_lat": 30.51}]),
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
        import json
        
        route = Route(
            route_code="RT001",
            dispatch_id=1,
            vehicle_id=test_vehicles["VEH001"].id,
            total_distance=15.5,
            total_time=45.0,
            total_emission=3.1,
            route_segments=json.dumps([{"road_name": "测试路段", "start_lng": 114.28, "start_lat": 30.52, "end_lng": 114.29, "end_lat": 30.51}]),
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
