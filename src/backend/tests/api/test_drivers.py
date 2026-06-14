"""
API测试：司机管理（drivers.py）

测试目标：
- GET /api/drivers：司机列表
- POST /api/drivers：新增司机
- GET /api/drivers/{driver_code}：司机详情
- PUT /api/drivers/{driver_code}：编辑司机
- DELETE /api/drivers/{driver_code}：删除司机

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
from models.driver import Driver


class TestGetDrivers:
    """测试获取司机列表"""

    @pytest.mark.api
    def test_get_drivers_empty(self, client, db_session):
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

        # 获取司机列表
        response = client.get(
            "/api/drivers",
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
    def test_get_drivers_with_data(self, client, db_session):
        """测试有数据时返回司机列表"""
        # 创建测试用户、节点、司机
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

        # 创建测试司机
        driver = Driver(
            driver_code="DRV001",
            name="测试司机",
            phone="13800000001",
            license_type="C1",
            shift="day",
            node_id=node.id,
            status="idle",
        )
        db_session.add(driver)
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 获取司机列表
        response = client.get(
            "/api/drivers",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert len(body["data"]["items"]) == 1
        assert body["data"]["total"] == 1
        assert body["data"]["items"][0]["driver_code"] == "DRV001"


class TestCreateDriver:
    """测试创建司机"""

    @pytest.mark.api
    def test_create_driver_success(self, client, db_session):
        """测试成功创建司机"""
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

        # 创建司机
        response = client.post(
            "/api/drivers",
            json={
                "driver_code": "DRV001",
                "name": "测试司机",
                "phone": "13800000001",
                "license_type": "C1",
                "shift": "day",
                "node_code": "SC001",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert "data" in body
        assert body["data"]["driver_code"] == "DRV001"

    @pytest.mark.api
    def test_create_driver_duplicate_code(self, client, db_session):
        """测试重复司机编号（应该失败）"""
        # 创建测试用户、节点、司机
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

        # 创建测试司机（已存在）
        driver = Driver(
            driver_code="DRV001",
            name="测试司机",
            phone="13800000001",
            license_type="C1",
            shift="day",
            node_id=node.id,
            status="idle",
        )
        db_session.add(driver)
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 创建司机（重复编号）
        response = client.post(
            "/api/drivers",
            json={
                "driver_code": "DRV001",  # 重复
                "name": "测试司机2",
                "phone": "13800000002",
                "license_type": "C1",
                "shift": "night",
                "node_code": "SC001",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应（业务错误）
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
        assert "司机" in body["message"] or "已存在" in body["message"]


class TestDeleteDriver:
    """测试删除司机"""

    @pytest.mark.api
    def test_delete_driver_success(self, client, db_session):
        """测试成功删除司机"""
        # 创建测试用户、节点、司机
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

        # 创建测试司机
        driver = Driver(
            driver_code="DRV001",
            name="测试司机",
            phone="13800000001",
            license_type="C1",
            shift="day",
            node_id=node.id,
            status="idle",
        )
        db_session.add(driver)
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 删除司机
        response = client.delete(
            "/api/drivers/DRV001",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0

    @pytest.mark.api
    def test_delete_driver_not_found(self, client, db_session):
        """测试删除不存在的司机"""
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

        # 删除司机（不存在）
        response = client.delete(
            "/api/drivers/DRV_NONEXIST",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应（业务错误）
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
        assert "司机" in body["message"] or "不存在" in body["message"]
