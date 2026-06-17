"""
API测试：节点管理（nodes.py）

测试目标：
- GET /api/nodes：节点列表
- POST /api/nodes/storage-centers：新增存储中心
- PUT /api/nodes/storage-centers/{code}：编辑存储中心
- DELETE /api/nodes/storage-centers/{code}：删除存储中心
- POST /api/nodes/sorting-centers：新增分拣中心
- PUT /api/nodes/sorting-centers/{code}：编辑分拣中心
- DELETE /api/nodes/sorting-centers/{code}：删除分拣中心
- GET /api/nodes/{node_code}：节点详情

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
from models.storage_center import StorageCenter
from models.sorting_center import SortingCenter


class TestGetNodes:
    """测试获取节点列表"""

    @pytest.mark.api
    def test_get_nodes_empty(self, client, db_session):
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

        # 获取节点列表
        response = client.get(
            "/api/nodes",
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
    def test_get_nodes_with_data(self, client, db_session):
        """测试有数据时返回节点列表"""
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
        sc = StorageCenter(node_id=node.id, capacity=1000.0, inventory=0)
        db_session.add(sc)
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 获取节点列表
        response = client.get(
            "/api/nodes",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert len(body["data"]["items"]) == 1
        assert body["data"]["total"] == 1
        assert body["data"]["items"][0]["node_code"] == "SC001"


class TestCreateStorageCenter:
    """测试新增存储中心"""

    @pytest.mark.api
    def test_create_storage_center_success(self, client, db_session):
        """测试成功新增存储中心"""
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

        # 新增存储中心
        response = client.post(
            "/api/nodes/storage-centers",
            json={
                "node_code": "SC001",
                "name": "存储中心",
                "location": "测试",
                "latitude": 30.5,
                "longitude": 114.3,
                "capacity": 1000.0,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert "data" in body
        assert body["data"]["node_code"] == "SC001"

    @pytest.mark.api
    def test_create_storage_center_duplicate_code(self, client, db_session):
        """测试重复节点编号（应该失败）"""
        # 创建测试用户、节点
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)

        # 创建测试节点（已存在）
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
        sc = StorageCenter(node_id=node.id, capacity=1000.0, inventory=0)
        db_session.add(sc)
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 新增存储中心（重复编号）
        response = client.post(
            "/api/nodes/storage-centers",
            json={
                "node_code": "SC001",  # 重复
                "name": "存储中心2",
                "location": "测试",
                "latitude": 30.6,
                "longitude": 114.4,
                "capacity": 800.0,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应（业务错误）
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
        assert "节点" in body["message"] or "已存在" in body["message"]


class TestDeleteStorageCenter:
    """测试删除存储中心"""

    @pytest.mark.api
    def test_delete_storage_center_success(self, client, db_session):
        """测试成功删除存储中心"""
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
        sc = StorageCenter(node_id=node.id, capacity=1000.0, inventory=0)
        db_session.add(sc)
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 删除存储中心
        response = client.delete(
            "/api/nodes/storage-centers/SC001",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0

    @pytest.mark.api
    def test_delete_storage_center_not_found(self, client, db_session):
        """测试删除不存在的存储中心"""
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

        # 删除存储中心（不存在）
        response = client.delete(
            "/api/nodes/storage-centers/SC_NONEXIST",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应（业务错误）
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
        assert "节点" in body["message"] or "不存在" in body["message"]


class TestUpdateStorageCenter:
    """测试更新存储中心"""

    @pytest.mark.api
    def test_update_storage_center_success(self, client, db_session):
        """测试成功更新存储中心"""
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
        sc = StorageCenter(node_id=node.id, capacity=1000.0, inventory=0)
        db_session.add(sc)
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 更新存储中心
        response = client.put(
            "/api/nodes/storage-centers/SC001",
            json={
                "name": "更新存储中心",
                "location": "更新位置",
                "latitude": 30.6,
                "longitude": 114.4,
                "capacity": 2000.0,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0

        # 验证数据库已更新
        db_session.refresh(sc)
        assert sc.capacity == 2000.0

    @pytest.mark.api
    def test_update_storage_center_not_found(self, client, db_session):
        """测试更新不存在的存储中心"""
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

        # 更新存储中心（不存在）
        response = client.put(
            "/api/nodes/storage-centers/SC_NONEXIST",
            json={
                "name": "更新存储中心",
                "location": "更新位置",
                "capacity": 2000.0,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应（业务错误）
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
        assert "节点" in body["message"] or "不存在" in body["message"]


class TestUpdateSortingCenter:
    """测试更新分拣中心"""

    @pytest.mark.api
    def test_update_sorting_center_success(self, client, db_session):
        """测试成功更新分拣中心"""
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
            node_code="L1001",
            name="一级分拣中心",
            location="测试",
            latitude=30.5,
            longitude=114.3,
            node_type="sorting_center",
        )
        db_session.add(node)
        db_session.flush()
        sc = SortingCenter(node_id=node.id, level=1, capacity=500, max_storage_time=24)
        db_session.add(sc)
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 更新分拣中心
        response = client.put(
            "/api/nodes/sorting-centers/L1001",
            json={
                "name": "更新分拣中心",
                "location": "更新位置",
                "latitude": 30.6,
                "longitude": 114.4,
                "level": 1,
                "capacity": 1000,
                "max_storage_time": 48,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0

        # 验证数据库已更新
        db_session.refresh(sc)
        assert sc.capacity == 1000
        assert sc.max_storage_time == 48

    @pytest.mark.api
    def test_update_sorting_center_not_found(self, client, db_session):
        """测试更新不存在的分拣中心"""
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

        # 更新分拣中心（不存在）
        response = client.put(
            "/api/nodes/sorting-centers/L1_NONEXIST",
            json={
                "name": "更新分拣中心",
                "location": "更新位置",
                "level": 1,
                "max_storage": 1000,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应（业务错误）
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
        assert "节点" in body["message"] or "不存在" in body["message"]
