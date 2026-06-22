"""
Routes API 测试
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from models.user import User

# 创建测试客户端
@pytest.fixture
def client():
    """创建测试客户端，并覆盖认证依赖"""
    from main import app
    from api.dependencies import get_current_user
    
    # 创建一个Mock用户（dispatcher角色）
    mock_user = MagicMock(spec=User)
    mock_user.role = "dispatcher"
    
    # 覆盖认证依赖
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with TestClient(app) as client:
        yield client
    
    # 测试结束后清除覆盖
    app.dependency_overrides.clear()


class TestPlanRoutes:
    """测试 POST /api/routes/plan 接口"""
    
    @patch('services.route_service.RouteService.create_route_planning')
    def test_success(self, mock_create_route_planning, client):
        """测试成功触发路径规划"""
        from utils.response import success_response
        
        # 模拟 RouteService.create_route_planning 返回成功
        mock_create_route_planning.return_value = success_response(data={
            "batch_code": "BATCH20260614001",
            "status": "completed",
            "routes": []
        })
        
        # 发送请求
        response = client.post(
            "/api/routes/plan",
            json={"batch_code": "BATCH20260614001", "dispatch_codes": None}
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "data" in data
    
    @patch('services.route_service.RouteService.create_route_planning')
    def test_batch_not_found(self, mock_create_route_planning, client):
        """测试批次不存在，返回错误"""
        from utils.response import error_response
        
        # 模拟 RouteService.create_route_planning 返回错误
        mock_create_route_planning.return_value = error_response(code=40001, message="路径规划失败：批次不存在 BATCH_INVALID")
        
        # 发送请求
        response = client.post(
            "/api/routes/plan",
            json={"batch_code": "BATCH_INVALID", "dispatch_codes": None}
        )
        
        # 验证响应
        assert response.status_code == 200  # 业务错误返回200
        data = response.json()
        assert data["code"] != 0


class TestGetRoutes:
    """测试 GET /api/routes 接口"""
    
    @patch('services.route_service.RouteService.get_routes')
    def test_success(self, mock_get_routes, client):
        """测试成功查询路线列表"""
        from utils.response import success_response
        
        # 模拟 RouteService.get_routes 返回成功
        mock_get_routes.return_value = success_response(data={
            "items": [],
            "total": 0
        })
        
        # 发送请求
        response = client.get("/api/routes")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "data" in data


class TestGetRouteDetail:
    """测试 GET /api/routes/{route_code} 接口"""
    
    @patch('services.route_service.RouteService.get_route_detail')
    def test_success(self, mock_get_route_detail, client):
        """测试成功查询路线详情"""
        from utils.response import success_response
        
        # 模拟 RouteService.get_route_detail 返回成功
        mock_get_route_detail.return_value = success_response(data={
            "route_code": "ROUTE20260614001",
            "batch_code": "BATCH20260614001",
            "dispatch_code": "DISP20260614001",
            "vehicle_code": "V001",
            "route_segments": [],
            "total_distance": 15.5,
            "total_time": 45.0,
            "total_emission": 3.1,
            "algorithm_type": "traditional",
            "created_at": "2026-06-14T10:30:00"
        })
        
        # 发送请求
        response = client.get("/api/routes/ROUTE20260614001")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "data" in data
    
    @patch('services.route_service.RouteService.get_route_detail')
    def test_route_not_found(self, mock_get_route_detail, client):
        """测试路线不存在，返回404错误"""
        from utils.response import error_response
        
        # 模拟 RouteService.get_route_detail 返回错误
        mock_get_route_detail.return_value = error_response(code=40400, message="路线不存在：ROUTE_INVALID")
        
        # 发送请求
        response = client.get("/api/routes/ROUTE_INVALID")
        
        # 验证响应
        assert response.status_code == 200  # 业务错误返回200
        data = response.json()
        assert data["code"] == 40400


class TestGetRouteCoordinates:
    """测试 GET /api/routes/by-vehicle/{vehicle_code}/coordinates 接口"""
    
    @patch('services.route_service.RouteService.get_route_coordinates')
    def test_success(self, mock_get_route_coordinates, client):
        """测试成功查询车辆路线坐标"""
        from utils.response import success_response
        
        # 模拟 RouteService.get_route_coordinates 返回成功
        mock_get_route_coordinates.return_value = success_response(data={
            "vehicle_code": "V001",
            "routes": []
        })
        
        # 发送请求
        response = client.get("/api/routes/by-vehicle/V001/coordinates")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "data" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
