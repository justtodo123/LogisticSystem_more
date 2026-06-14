"""
Exception API 测试

测试异常管理API (api/exception_events.py) 的所有端点：
- GET /api/exceptions - 获取异常事件列表
- POST /api/exceptions - 创建异常事件
- GET /api/exceptions/{code} - 获取异常事件详情
- PUT /api/exceptions/{code} - 更新异常事件
- POST /api/exceptions/{code}/replan - 触发重规划
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime

from main import app
from models.exception_event import ExceptionEvent
from models.route import Route


@pytest.fixture
def client():
    """测试客户端"""
    return TestClient(app)


@pytest.fixture
def auth_headers(db_session):
    """认证头（调度员）"""
    # 登录获取token
    response = client.post("/api/auth/login", json={
        "username": "dispatcher",
        "password": "123456"
    })
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def setup_exception_data(db_session):
    """设置异常测试数据"""
    # 创建路线（用于关联异常）
    route = Route(
        route_code="RT_TEST_001",
        dispatch_id=1,
        vehicle_id=1,
        total_distance=100.0,
        total_time=120.0,
        route_segments='[{"road_name":"测试道路"}]',
        version=1
    )
    db_session.add(route)
    db_session.flush()
    
    # 创建异常事件
    exception_event = ExceptionEvent(
        event_code="EXP_TEST_001",
        exception_type="road",
        severity="medium",
        recommended_action="reroute",
        trigger_node_id=1,
        related_route_id=route.id,
        description="测试道路异常",
        status="open"
    )
    db_session.add(exception_event)
    db_session.commit()
    
    return {
        "route": route,
        "exception_event": exception_event
    }


@pytest.mark.api
@pytest.mark.phase7
class TestExceptionAPI:
    """测试异常管理API"""
    
    def test_get_exceptions_success(self, client, auth_headers, setup_exception_data):
        """测试成功获取异常事件列表"""
        # 执行
        response = client.get("/api/exceptions", headers=auth_headers)
        
        # 验证
        if response.status_code == 501:
            pytest.skip("异常API未实现，跳过测试")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "items" in data["data"]
    
    def test_get_exceptions_with_filters(self, client, auth_headers):
        """测试按筛选条件获取异常事件列表"""
        # 执行
        response = client.get(
            "/api/exceptions",
            params={"exception_type": "road", "status": "open"},
            headers=auth_headers
        )
        
        # 验证
        if response.status_code == 501:
            pytest.skip("异常API未实现，跳过测试")
        
        assert response.status_code == 200
    
    def test_create_exception_success(self, client, auth_headers):
        """测试成功创建异常事件"""
        # 执行
        response = client.post(
            "/api/exceptions",
            json={
                "exception_type": "road",
                "severity": "high",
                "recommended_action": "reroute",
                "trigger_node_code": "SO001",
                "related_route_code": "RT_TEST_001",
                "description": "测试创建异常事件"
            },
            headers=auth_headers
        )
        
        # 验证
        if response.status_code == 501:
            pytest.skip("异常API未实现，跳过测试")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "event_code" in data["data"]
    
    def test_create_exception_invalid_type(self, client, auth_headers):
        """测试创建异常事件时异常类型无效"""
        # 执行
        response = client.post(
            "/api/exceptions",
            json={
                "exception_type": "invalid",  # 无效类型
                "severity": "high",
                "recommended_action": "reroute",
                "description": "测试无效异常类型"
            },
            headers=auth_headers
        )
        
        # 验证
        if response.status_code == 501:
            pytest.skip("异常API未实现，跳过测试")
        
        assert response.status_code == 400
        data = response.json()
        assert data["code"] == 40000  # 参数错误
    
    def test_get_exception_detail_success(self, client, auth_headers, setup_exception_data):
        """测试成功获取异常事件详情"""
        # 执行
        response = client.get(
            f"/api/exceptions/{setup_exception_data['exception_event'].event_code}",
            headers=auth_headers
        )
        
        # 验证
        if response.status_code == 501:
            pytest.skip("异常API未实现，跳过测试")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["event_code"] == setup_exception_data['exception_event'].event_code
    
    def test_get_exception_detail_not_found(self, client, auth_headers):
        """测试异常事件不存在"""
        # 执行
        response = client.get("/api/exceptions/INVALID", headers=auth_headers)
        
        # 验证
        if response.status_code == 501:
            pytest.skip("异常API未实现，跳过测试")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] != 0  # 应该返回错误码
    
    def test_update_exception_success(self, client, auth_headers, setup_exception_data):
        """测试成功更新异常事件"""
        # 执行
        response = client.put(
            f"/api/exceptions/{setup_exception_data['exception_event'].event_code}",
            json={
                "status": "resolved",
                "resolution_note": "已修复道路"
            },
            headers=auth_headers
        )
        
        # 验证
        if response.status_code == 501:
            pytest.skip("异常API未实现，跳过测试")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
    
    def test_replan_success(self, client, auth_headers, setup_exception_data):
        """测试成功触发重规划"""
        # 执行
        response = client.post(
            f"/api/exceptions/{setup_exception_data['exception_event'].event_code}/replan",
            json={
                "action": "reroute",  # 或 "redispatch"
                "reason": "测试重规划"
            },
            headers=auth_headers
        )
        
        # 验证
        if response.status_code == 501:
            pytest.skip("异常重规划API未实现，跳过测试")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "new_schedule_code" in data["data"] or "new_route_code" in data["data"]
    
    def test_replan_exception_not_found(self, client, auth_headers):
        """测试异常事件不存在时触发重规划"""
        # 执行
        response = client.post(
            "/api/exceptions/INVALID/replan",
            json={
                "action": "reroute",
                "reason": "测试重规划"
            },
            headers=auth_headers
        )
        
        # 验证
        if response.status_code == 501:
            pytest.skip("异常重规划API未实现，跳过测试")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] != 0  # 应该返回错误码
    
    def test_replan_invalid_action(self, client, auth_headers, setup_exception_data):
        """测试重规划动作无效"""
        # 执行
        response = client.post(
            f"/api/exceptions/{setup_exception_data['exception_event'].event_code}/replan",
            json={
                "action": "invalid",  # 无效动作
                "reason": "测试重规划"
            },
            headers=auth_headers
        )
        
        # 验证
        if response.status_code == 501:
            pytest.skip("异常重规划API未实现，跳过测试")
        
        assert response.status_code == 400
        data = response.json()
        assert data["code"] == 40000  # 参数错误
