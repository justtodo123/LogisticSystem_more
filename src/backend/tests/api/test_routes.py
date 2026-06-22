"""
API测试：路线管理（routes.py）

测试目标：
- GET /api/routes：路线列表
- GET /api/routes/{route_code}：路线详情
- GET /api/routes/by-vehicle/{vehicle_code}/coordinates：车辆路线坐标

验证内容：
- HTTP状态码
- 响应数据结构（code, message, data, meta）
- 业务逻辑正确性
"""
import pytest
from fastapi.testclient import TestClient
from models.user import User
from services.auth_service import get_password_hash
from models.route import Route
from models.vehicle import Vehicle
from models.node import Node
import json


class TestGetRoutes:
    """测试获取路线列表"""

    @pytest.mark.api
    def test_get_routes_empty(self, client, db_session):
        """测试空数据库返回空列表"""
        # 创建测试用户
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 获取路线列表
        response = client.get(
            "/api/routes",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert "data" in body
        assert "items" in body["data"]
        assert body["data"]["items"] == []
        assert body["data"]["total"] == 0

    @pytest.mark.api
    def test_get_routes_with_data(self, client, db_session):
        """测试有数据时返回路线列表"""
        # 创建测试用户、车辆、路线
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)

        # 创建测试车辆
        vehicle = Vehicle(
            vehicle_code="VEH001",
            model="测试车型",
            capacity=100.0,
            energy_type="fuel",
            node_id=1,
            last_arrived_node_id=1,
            status="idle",
        )
        db_session.add(vehicle)
        db_session.commit()

        # 创建测试批次
        from models.dispatch_batch import DispatchBatch
        batch = DispatchBatch(
            batch_code="BATCH001",
            global_schedule_id=1,
            status="completed"
        )
        db_session.add(batch)
        db_session.flush()

        # 创建测试节点调度
        from models.node_dispatch import NodeDispatch
        node_dispatch = NodeDispatch(
            dispatch_code="ND001",
            dispatch_batch_id=batch.id,
            vehicle_id=vehicle.id,
            level_phase=0,
            tasks=[],
            total_distance=10.0,
            total_time=30.0
        )
        db_session.add(node_dispatch)
        db_session.flush()

        # 创建测试路线
        route = Route(
            route_code="RT001",
            dispatch_id=node_dispatch.id,
            vehicle_id=vehicle.id,
            total_distance=15.5,
            total_time=45.0,
            total_emission=3.1,
            route_segments=[{"road_name": "测试路段", "start_lng": 114.28, "start_lat": 30.52, "end_lng": 114.29, "end_lat": 30.51}],
        )
        db_session.add(route)
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 获取路线列表
        response = client.get(
            "/api/routes",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert len(body["data"]["items"]) == 1
        assert body["data"]["total"] == 1
        assert body["data"]["items"][0]["route_code"] == "RT001"


class TestGetRouteDetail:
    """测试获取路线详情"""

    @pytest.mark.api
    def test_get_route_detail_success(self, client, db_session):
        """测试成功获取路线详情"""
        # 创建测试用户、车辆、路线
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)

        # 创建测试车辆
        vehicle = Vehicle(
            vehicle_code="VEH001",
            model="测试车型",
            capacity=100.0,
            energy_type="fuel",
            node_id=1,
            last_arrived_node_id=1,
            status="idle",
        )
        db_session.add(vehicle)
        db_session.commit()

        # 创建测试路线
        route = Route(
            route_code="RT001",
            dispatch_id=1,
            vehicle_id=vehicle.id,
            total_distance=15.5,
            total_time=45.0,
            total_emission=3.1,
            route_segments=[{"road_name": "测试路段", "start_lng": 114.28, "start_lat": 30.52, "end_lng": 114.29, "end_lat": 30.51}],
        )
        db_session.add(route)
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 获取路线详情
        response = client.get(
            f"/api/routes/RT001",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["route_code"] == "RT001"
        assert "route_segments" in body["data"]

    @pytest.mark.api
    def test_get_route_detail_not_found(self, client, db_session):
        """测试路线不存在"""
        # 创建测试用户
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 获取路线详情（不存在）
        response = client.get(
            "/api/routes/RT_NONEXIST",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应（业务错误）
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
        assert "路线" in body["message"] or "不存在" in body["message"]


class TestGetRouteCoordinates:
    """测试获取车辆路线坐标"""

    @pytest.mark.api
    def test_get_route_coordinates_success(self, client, db_session):
        """测试成功获取车辆路线坐标"""
        # 创建测试用户、车辆、路线
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)

        # 创建测试车辆
        vehicle = Vehicle(
            vehicle_code="VEH001",
            model="测试车型",
            capacity=100.0,
            energy_type="fuel",
            node_id=1,
            last_arrived_node_id=1,
            status="idle",
        )
        db_session.add(vehicle)
        db_session.commit()

        # 创建测试路线
        route = Route(
            route_code="RT001",
            dispatch_id=1,
            vehicle_id=vehicle.id,
            total_distance=15.5,
            total_time=45.0,
            total_emission=3.1,
            route_segments=[{"road_name": "测试路段", "start_lng": 114.28, "start_lat": 30.52, "end_lng": 114.29, "end_lat": 30.51}],
        )
        db_session.add(route)
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 获取车辆路线坐标
        response = client.get(
            f"/api/routes/by-vehicle/VEH001/coordinates",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert "data" in body
        assert "vehicle_code" in body["data"]
        assert body["data"]["vehicle_code"] == "VEH001"

    @pytest.mark.api
    def test_get_route_coordinates_vehicle_not_found(self, client, db_session):
        """测试车辆不存在"""
        # 创建测试用户
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 获取车辆路线坐标（车辆不存在）
        response = client.get(
            "/api/routes/by-vehicle/VEH_NONEXIST/coordinates",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应（业务错误）
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
        assert "车辆" in body["message"] or "不存在" in body["message"]


class TestRouteBoundaries:
    """测试路线管理的边界情况"""

    @pytest.mark.api
    def test_get_route_coordinates_no_routes(self, client, db_session):
        """测试车辆没有路线时的坐标查询"""
        # 创建测试用户、车辆（但没有路线）
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)

        # 创建测试车辆
        vehicle = Vehicle(
            vehicle_code="VEH002",
            model="测试车型2",
            capacity=100.0,
            energy_type="fuel",
            node_id=1,
            last_arrived_node_id=1,
            status="idle",
        )
        db_session.add(vehicle)
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 获取车辆路线坐标（没有路线）
        response = client.get(
            f"/api/routes/by-vehicle/VEH002/coordinates",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应（应该返回空列表或业务错误）
        assert response.status_code == 200
        body = response.json()
        # 可能返回空列表，或者业务错误
        if body["code"] == 0:
            # 返回空列表
            assert "data" in body
            assert "routes" in body["data"]
            assert body["data"]["routes"] == []
        else:
            # 业务错误
            assert body["code"] != 0

    @pytest.mark.api
    def test_get_route_detail_invalid_code(self, client, db_session):
        """测试路线编号格式错误"""
        # 创建测试用户
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 获取路线详情（编号格式错误）
        response = client.get(
            "/api/routes/INVALID_CODE",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应（业务错误）
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
        assert "路线" in body["message"] or "不存在" in body["message"]

    @pytest.mark.api
    def test_get_routes_with_filters(self, client, db_session):
        """测试路线列表的筛选参数"""
        # 创建测试用户
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 测试筛选参数（batch_code不存在）
        response = client.get(
            "/api/routes",
            params={"batch_code": "BATCH_NONEXIST"},
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应（应该返回空列表）
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["items"] == []
        assert body["data"]["total"] == 0

