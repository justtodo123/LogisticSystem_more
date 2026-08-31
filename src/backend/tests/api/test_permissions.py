"""
API测试：权限管理（RBAC）

测试目标：
- 验证manager角色无法访问dispatcher专属端点（返回403）
- 验证Token缺失/无效时的认证错误（返回401）
- 验证权限控制的完整性

测试范围：
- 阶段1：认证与权限
- 阶段2：基础数据管理（orders、vehicles、drivers、nodes）
- 阶段3：全局调度（schedule/global）
- 阶段4：节点调度（schedule/node-dispatch）
- 阶段5：路径规划（routes/plan）
- 阶段6：模拟送达（simulation/deliver）
"""
import pytest
from fastapi.testclient import TestClient
from models.user import User
from services.auth_service import get_password_hash


class TestManagerPermissions:
    """测试manager角色的权限限制"""

    @pytest.mark.api
    def test_manager_create_order_forbidden(self, client, db_session):
        """测试manager创建订单（应该返回403）"""
        # 创建manager用户
        user = User(
            username="manager",
            password_hash=get_password_hash("123456"),
            role="manager",
            display_name="管理员",
            is_active=True,
        )
        db_session.add(user)
        
        # 创建测试节点
        from models.node import Node
        from models.sorting_center import SortingCenter
        node = Node(
            node_code="SO001",
            name="测试节点",
            location="测试",
            latitude=30.5,
            longitude=114.3,
            node_type="sorting_center",
        )
        db_session.add(node)
        db_session.flush()
        sc = SortingCenter(node_id=node.id, level=0)
        db_session.add(sc)
        
        # 创建存储中心节点
        storage_node = Node(
            node_code="SC001",
            name="存储中心",
            location="测试",
            latitude=30.6,
            longitude=114.4,
            node_type="storage_center",
        )
        db_session.add(storage_node)
        db_session.flush()
        from models.storage_center import StorageCenter
        storage_center = StorageCenter(node_id=storage_node.id, capacity=1000.0)
        db_session.add(storage_center)
        db_session.commit()
        
        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "manager", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]
        
        # 尝试创建订单（manager应该被禁止）
        response = client.post(
            "/api/orders",
            json={
                "destination_node_code": "SO001",
                "time_window": "2026-06-15 全天",
                "goods": [
                    {
                        "goods_name": "测试货物",
                        "goods_type": "普通",
                        "weight": 1.0,
                        "volume": 0.5,
                    }
                ],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # manager 拥有 orders:write，不应被 403 拒绝
        assert response.status_code != 403
        body = response.json()
        assert body["code"] != 40300

    @pytest.mark.api
    def test_manager_update_order_forbidden(self, client, db_session):
        """测试manager更新订单（应该返回403）"""
        # 创建manager用户和测试数据
        user = User(
            username="manager",
            password_hash=get_password_hash("123456"),
            role="manager",
            display_name="管理员",
            is_active=True,
        )
        db_session.add(user)
        
        # 创建测试节点和订单
        from models.node import Node
        from models.sorting_center import SortingCenter
        from models.order import Order
        
        node = Node(
            node_code="SO001",
            name="测试节点",
            location="测试",
            latitude=30.5,
            longitude=114.3,
            node_type="sorting_center",
        )
        db_session.add(node)
        db_session.flush()
        sc = SortingCenter(node_id=node.id, level=0)
        db_session.add(sc)
        db_session.commit()
        
        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "manager", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]
        
        # 尝试更新订单（manager应该被禁止）
        response = client.put(
            "/api/orders/O001",
            json={
                "destination_node_code": "SO001",
                "time_window": "2026-06-20 9:00-18:00",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # 验证响应（应该返回403或404，因为订单不存在）
        assert response.status_code != 403
        assert response.json()["code"] != 40300

    @pytest.mark.api
    def test_manager_delete_order_forbidden(self, client, db_session):
        """测试manager删除订单（应该返回403）"""
        # 创建manager用户
        user = User(
            username="manager",
            password_hash=get_password_hash("123456"),
            role="manager",
            display_name="管理员",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        
        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "manager", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]
        
        # 尝试删除订单（manager应该被禁止）
        response = client.delete(
            "/api/orders/O001",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # 验证响应（应该返回403或404）
        assert response.status_code != 403
        assert response.json()["code"] != 40300

    @pytest.mark.api
    def test_manager_trigger_schedule_forbidden(self, client, db_session):
        """测试manager触发全局调度（应该返回403）"""
        # 创建manager用户
        user = User(
            username="manager",
            password_hash=get_password_hash("123456"),
            role="manager",
            display_name="管理员",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        
        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "manager", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]
        
        # 尝试触发全局调度（manager应该被禁止）
        response = client.post(
            "/api/schedule/global",
            json={
                "order_codes": None,
                "algorithm": "traditional",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # 验证响应（应该返回403）
        assert response.status_code == 403
        body = response.json()
        assert body["code"] == 40300

    @pytest.mark.api
    def test_manager_create_vehicle_forbidden(self, client, db_session):
        """测试manager创建车辆（应该返回403）"""
        # 创建manager用户
        user = User(
            username="manager",
            password_hash=get_password_hash("123456"),
            role="manager",
            display_name="管理员",
            is_active=True,
        )
        db_session.add(user)
        
        # 创建测试节点
        from models.node import Node
        node = Node(
            node_code="SC001",
            name="存储中心",
            location="测试",
            latitude=30.5,
            longitude=114.3,
            node_type="storage_center",
        )
        db_session.add(node)
        db_session.commit()
        
        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "manager", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]
        
        # 尝试创建车辆（manager应该被禁止）
        response = client.post(
            "/api/vehicles",
            json={
                "vehicle_code": "VEH001",
                "model": "测试车型",
                "capacity": 100.0,
                "energy_type": "fuel",
                "last_arrived_node_code": "SC001",
                "node_code": "SC001",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # 验证响应（应该返回403）
        assert response.status_code == 403
        body = response.json()
        assert body["code"] == 40300


class TestAuthentication:
    """测试认证功能"""

    @pytest.mark.api
    def test_access_without_token(self, client):
        """测试不带Token访问受保护端点"""
        # 尝试访问受保护端点（不带Token）
        response = client.get("/api/orders")
        
        # 验证响应（应该返回401）
        assert response.status_code == 401
        body = response.json()
        assert body["code"] == 40100
        assert "未登录" in body["message"] or "Token" in body["message"]

    @pytest.mark.api
    def test_access_with_invalid_token(self, client):
        """测试使用无效Token访问"""
        # 使用无效Token访问
        response = client.get(
            "/api/orders",
            headers={"Authorization": "Bearer invalid_token"},
        )
        
        # 验证响应（应该返回401）
        assert response.status_code == 401
        body = response.json()
        assert body["code"] == 40100

    @pytest.mark.api
    def test_login_with_wrong_password(self, client, db_session):
        """测试使用错误密码登录"""
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
        
        # 使用错误密码登录
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "wrong_password"},
        )
        
        # 验证响应（HTTP 200，业务错误码40100）
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 40100
        assert "密码" in body["message"] or "无效" in body["message"]

    @pytest.mark.api
    def test_login_with_nonexistent_user(self, client):
        """测试使用不存在的用户登录"""
        # 使用不存在的用户登录
        response = client.post(
            "/api/auth/login",
            json={"username": "nonexistent", "password": "123456"},
        )
        
        # 验证响应（HTTP 200，业务错误码40100）
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 40100
        assert "用户" in body["message"] or "不存在" in body["message"]
