"""
API测试：车辆管理（vehicles.py）

测试目标：
- GET /api/vehicles：车辆列表
- POST /api/vehicles：新增车辆
- GET /api/vehicles/{vehicle_code}：车辆详情
- PUT /api/vehicles/{vehicle_code}：编辑车辆
- DELETE /api/vehicles/{vehicle_code}：删除车辆

验证内容：
- HTTP状态码
- 响应数据结构（code, message, data, meta）
- 业务逻辑正确性
"""
import pytest
from fastapi.testclient import TestClient
from models.user import User
from services.auth_service import get_password_hash
from models.node import Node
from models.vehicle import Vehicle


class TestGetVehicles:
    """测试获取车辆列表"""

    @pytest.mark.api
    def test_get_vehicles_empty(self, client, db_session):
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

        # 获取车辆列表
        response = client.get(
            "/api/vehicles",
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
    def test_get_vehicles_with_data(self, client, db_session):
        """测试有数据时返回车辆列表"""
        # 创建测试用户、节点、车辆
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)

        # 创建测试节点
        node = Node(
            node_code="SC001",
            name="存储中心",
            location="测试",
            latitude=30.5,
            longitude=114.3,
            node_type="storage_center",
        )
        db_session.add(node)
        db_session.flush()

        # 创建测试车辆
        vehicle = Vehicle(
            vehicle_code="VEH001",
            model="测试车型",
            capacity=100.0,
            energy_type="fuel",
            node_id=node.id,
            last_arrived_node_id=node.id,
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

        # 获取车辆列表
        response = client.get(
            "/api/vehicles",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert len(body["data"]["items"]) == 1
        assert body["data"]["total"] == 1
        assert body["data"]["items"][0]["vehicle_code"] == "VEH001"


class TestCreateVehicle:
    """测试创建车辆"""

    @pytest.mark.api
    def test_create_vehicle_success(self, client, db_session):
        """测试成功创建车辆"""
        # 创建测试用户、节点
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)

        # 创建测试节点
        node = Node(
            node_code="SC001",
            name="存储中心",
            location="测试",
            latitude=30.5,
            longitude=114.3,
            node_type="storage_center",
        )
        db_session.add(node)
        db_session.flush()
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 创建车辆
        response = client.post(
            "/api/vehicles",
            json={
                "vehicle_code": "VEH001",
                "model": "测试车型",
                "capacity": 100.0,
                "energy_type": "fuel",
                "node_code": "SC001",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert "data" in body
        assert body["data"]["vehicle_code"] == "VEH001"

    @pytest.mark.api
    def test_create_vehicle_duplicate_code(self, client, db_session):
        """测试重复车辆编号（应该失败）"""
        # 创建测试用户、节点、车辆
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)

        # 创建测试节点
        node = Node(
            node_code="SC001",
            name="存储中心",
            location="测试",
            latitude=30.5,
            longitude=114.3,
            node_type="storage_center",
        )
        db_session.add(node)
        db_session.flush()

        # 创建测试车辆（已存在）
        vehicle = Vehicle(
            vehicle_code="VEH001",
            model="测试车型",
            capacity=100.0,
            energy_type="fuel",
            node_id=node.id,
            last_arrived_node_id=node.id,
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

        # 创建车辆（重复编号）
        response = client.post(
            "/api/vehicles",
            json={
                "vehicle_code": "VEH001",  # 重复
                "model": "测试车型2",
                "capacity": 200.0,
                "energy_type": "electric",
                "node_code": "SC001",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应（业务错误）
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
        assert "车辆" in body["message"] or "已存在" in body["message"]


class TestDeleteVehicle:
    """测试删除车辆"""

    @pytest.mark.api
    def test_delete_vehicle_success(self, client, db_session):
        """测试成功删除车辆"""
        # 创建测试用户、节点、车辆
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)

        # 创建测试节点
        node = Node(
            node_code="SC001",
            name="存储中心",
            location="测试",
            latitude=30.5,
            longitude=114.3,
            node_type="storage_center",
        )
        db_session.add(node)
        db_session.flush()

        # 创建测试车辆
        vehicle = Vehicle(
            vehicle_code="VEH001",
            model="测试车型",
            capacity=100.0,
            energy_type="fuel",
            node_id=node.id,
            last_arrived_node_id=node.id,
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

        # 删除车辆
        response = client.delete(
            "/api/vehicles/VEH001",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0

    @pytest.mark.api
    def test_delete_vehicle_not_found(self, client, db_session):
        """测试删除不存在的车辆"""
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

        # 删除车辆（不存在）
        response = client.delete(
            "/api/vehicles/VEH_NONEXIST",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应（业务错误）
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
        assert "车辆" in body["message"] or "不存在" in body["message"]
