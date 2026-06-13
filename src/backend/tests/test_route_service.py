"""
RouteService 服务层测试
"""

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session


class TestCreateRoutePlanning:
    """测试 RouteService.create_route_planning 方法"""
    
    @patch('services.route_service.Route')
    @patch('services.route_service.DispatchBatch')
    @patch('services.route_service.NodeDispatch')
    @patch('services.route_service.run_route_planning')
    async def test_success(self, mock_run_route_planning, mock_node_dispatch, mock_dispatch_batch, mock_route):
        """测试成功创建路径规划"""
        from services.route_service import RouteService
        
        # 模拟 DispatchBatch
        mock_batch_instance = MagicMock()
        mock_batch_instance.id = 1
        mock_batch_instance.status = "completed"
        mock_dispatch_batch.filter.return_value.first.return_value = mock_batch_instance
        
        # 模拟 NodeDispatch
        mock_dispatch_instance = MagicMock()
        mock_dispatch_instance.id = 1
        mock_node_dispatch.filter.return_value.all.return_value = [mock_dispatch_instance]
        
        # 模拟 run_route_planning
        mock_run_route_planning.return_value = {
            "route_code": "ROUTE20260614001",
            "dispatch_id": 1,
            "vehicle_id": 1,
            "route_segments": [{"road_name": "虚拟道路", "start_lng": 114.3, "start_lat": 30.5, "end_lng": 114.4, "end_lat": 30.6}],
            "total_distance": 15.5,
            "total_time": 45.0,
            "total_emission": 3.1,
            "algorithm_type": "traditional"
        }
        
        # 模拟数据库
        mock_db = MagicMock(spec=Session)
        
        # 调用方法
        result = await RouteService.create_route_planning(
            batch_code="BATCH20260614001",
            dispatch_codes=None,
            db=mock_db
        )
        
        # 验证结果
        assert result["code"] == 0
        assert "data" in result
        assert "routes" in result["data"]
    
    @patch('services.route_service.DispatchBatch')
    async def test_batch_not_found(self, mock_dispatch_batch):
        """测试批次不存在，返回错误"""
        from services.route_service import RouteService
        
        # 模拟数据库
        mock_db = MagicMock(spec=Session)
        
        # 设置 db.query().filter().first() 返回 None (模拟批次不存在)
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # 调用方法
        result = await RouteService.create_route_planning(
            batch_code="INVALID_BATCH",
            dispatch_codes=None,
            db=mock_db
        )
        
        # 验证结果
        assert result["code"] != 0
        assert "批次不存在" in result["message"]


class TestGetRoutes:
    """测试 RouteService.get_routes 方法"""
    
    @patch('services.route_service.Route')
    async def test_success(self, mock_route):
        """测试成功查询路线列表"""
        from services.route_service import RouteService
        
        # 模拟 Route 查询
        mock_route_instance = MagicMock()
        mock_route_instance.route_code = "ROUTE20260614001"
        mock_route_instance.total_distance = 15.5
        mock_route_instance.total_time = 45.0
        mock_route_instance.total_emission = 3.1
        mock_route_instance.created_at = MagicMock()
        mock_route_instance.created_at.isoformat.return_value = "2026-06-14T10:30:00"
        mock_route_instance.dispatch_id = 1
        mock_route_instance.vehicle_id = 1
        
        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.offset.return_value.limit.return_value.all.return_value = [mock_route_instance]
        
        mock_route.query.return_value = mock_query
        
        # 模拟数据库
        mock_db = MagicMock(spec=Session)
        
        # 调用方法
        result = await RouteService.get_routes(
            batch_code=None,
            vehicle_code=None,
            page=1,
            page_size=20,
            db=mock_db
        )
        
        # 验证结果
        assert result["code"] == 0
        assert "data" in result
        assert "items" in result["data"]


class TestGetRouteDetail:
    """测试 RouteService.get_route_detail 方法"""
    
    @patch('services.route_service.Route')
    async def test_success(self, mock_route):
        """测试成功查询路线详情"""
        from services.route_service import RouteService
        
        # 模拟 Route 查询
        mock_route_instance = MagicMock()
        mock_route_instance.route_code = "ROUTE20260614001"
        mock_route_instance.route_segments = [{"road_name": "虚拟道路", "start_lng": 114.3, "start_lat": 30.5, "end_lng": 114.4, "end_lat": 30.6}]
        mock_route_instance.total_distance = 15.5
        mock_route_instance.total_time = 45.0
        mock_route_instance.total_emission = 3.1
        mock_route_instance.algorithm_type = "traditional"
        mock_route_instance.created_at = MagicMock()
        mock_route_instance.created_at.isoformat.return_value = "2026-06-14T10:30:00"
        mock_route_instance.dispatch_id = 1
        mock_route_instance.vehicle_id = 1
        
        mock_route.filter.return_value.first.return_value = mock_route_instance
        
        # 模拟数据库
        mock_db = MagicMock(spec=Session)
        
        # 调用方法
        result = await RouteService.get_route_detail(
            route_code="ROUTE20260614001",
            db=mock_db
        )
        
        # 验证结果
        assert result["code"] == 0
        assert "data" in result
        assert "route_segments" in result["data"]
    
    @patch('services.route_service.Route')
    async def test_route_not_found(self, mock_route):
        """测试路线不存在，返回404错误"""
        from services.route_service import RouteService
        
        # 模拟数据库
        mock_db = MagicMock(spec=Session)
        
        # 设置 db.query().filter().first() 返回 None (模拟路线不存在)
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # 调用方法
        result = await RouteService.get_route_detail(
            route_code="INVALID_ROUTE",
            db=mock_db
        )
        
        # 验证结果
        assert result["code"] == 40400
        assert "路线不存在" in result["message"]


class TestGetRouteCoordinates:
    """测试 RouteService.get_route_coordinates 方法"""
    
    @patch('services.route_service.Route')
    @patch('services.route_service.Vehicle')
    async def test_success(self, mock_vehicle, mock_route):
        """测试成功查询车辆路线坐标"""
        from services.route_service import RouteService
        
        # 模拟 Vehicle 查询
        mock_vehicle_instance = MagicMock()
        mock_vehicle_instance.id = 1
        mock_vehicle.filter.return_value.first.return_value = mock_vehicle_instance
        
        # 模拟 Route 查询
        mock_route_instance = MagicMock()
        mock_route_instance.route_code = "ROUTE20260614001"
        mock_route_instance.route_segments = [{"road_name": "虚拟道路", "start_lng": 114.3, "start_lat": 30.5, "end_lng": 114.4, "end_lat": 30.6}]
        mock_route_instance.total_distance = 15.5
        mock_route_instance.dispatch_id = 1
        
        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_route_instance]
        
        mock_route.query.return_value = mock_query
        
        # 模拟数据库
        mock_db = MagicMock(spec=Session)
        
        # 调用方法
        result = await RouteService.get_route_coordinates(
            vehicle_code="V001",
            batch_code=None,
            db=mock_db
        )
        
        # 验证结果
        assert result["code"] == 0
        assert "data" in result
        assert "routes" in result["data"]
    
    @patch('services.route_service.Vehicle')
    async def test_vehicle_not_found(self, mock_vehicle):
        """测试车辆不存在，返回404错误"""
        from services.route_service import RouteService
        
        # 模拟数据库
        mock_db = MagicMock(spec=Session)
        
        # 设置 db.query().filter().first() 返回 None (模拟车辆不存在)
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # 调用方法
        result = await RouteService.get_route_coordinates(
            vehicle_code="INVALID_VEHICLE",
            batch_code=None,
            db=mock_db
        )
        
        # 验证结果
        assert result["code"] == 40400
        assert "车辆不存在" in result["message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
