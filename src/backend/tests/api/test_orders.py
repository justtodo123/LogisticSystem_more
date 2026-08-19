"""
API测试：订单管理（orders.py）

测试目标：
- GET /api/orders：订单列表
- POST /api/orders：新增订单
- GET /api/orders/{order_code}：订单详情
- PUT /api/orders/{order_code}：编辑订单
- DELETE /api/orders/{order_code}：删除订单

验证内容：
- HTTP状态码
- 响应数据结构（code, message, data, meta）
- 业务逻辑正确性（权限、参数校验、业务规则）
"""
import pytest
from fastapi.testclient import TestClient
from models.user import User
from services.auth_service import get_password_hash
from models.node import Node
from models.storage_center import StorageCenter
from models.sorting_center import SortingCenter


class TestGetOrders:
    """测试获取订单列表"""

    @pytest.mark.api
    def test_get_orders_empty(self, client, db_session):
        """测试空数据库返回空列表"""
        # 创建测试用户和节点（用于认证）
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)
        
        # 创建测试节点（订单需要目的地节点）
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
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]
        
        # 获取订单列表
        response = client.get(
            "/api/orders",
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
    def test_get_orders_with_data(self, client, db_session):
        """测试有数据时返回订单列表"""
        # 创建测试用户、节点、订单
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
        
        # 创建测试订单（需要直接操作数据库）
        from models.order import Order
        order = Order(
            order_code="O001",
            destination_node_id=node.id,
            time_window="全天",
            status="unassigned",
        )
        db_session.add(order)
        db_session.commit()
        
        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]
        
        # 获取订单列表
        response = client.get(
            "/api/orders",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert len(body["data"]["items"]) == 1
        assert body["data"]["total"] == 1
        assert body["data"]["items"][0]["order_code"] == "O001"


class TestCreateOrder:
    """测试创建订单"""

    @pytest.mark.api
    def test_create_order_success(self, client, db_session):
        """测试成功创建订单"""
        # 创建测试用户和节点
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)
        
        # 创建测试节点（订单需要目的地节点）
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
        
        # 创建测试存储中心（订单需要存储中心）
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
        storage_center = StorageCenter(node_id=storage_node.id, capacity=1000.0)
        db_session.add(storage_center)
        db_session.commit()
        
        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]
        
        # 创建订单
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
        
        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert "data" in body
        assert "order_code" in body["data"]
        assert body["data"]["order_code"].startswith("O")

    @pytest.mark.api
    def test_create_order_missing_goods(self, client, db_session):
        """测试缺少货物参数"""
        # 创建测试用户和节点
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
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]
        
        # 创建订单（缺少goods）
        response = client.post(
            "/api/orders",
            json={
                "destination_node_code": "SO001",
                "time_window": "2026-06-15 全天",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # 验证响应（应该是参数校验错误）
        assert response.status_code == 422  # FastAPI参数校验失败
        # 注意：响应体格式可能不正确，这里只检查状态码


class TestDeleteOrder:
    """测试删除订单"""

    @pytest.mark.api
    def test_delete_order_success(self, client, db_session):
        """测试成功删除订单"""
        # 创建测试用户、节点、订单
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
        
        # 创建测试订单
        from models.order import Order
        order = Order(
            order_code="O001",
            destination_node_id=node.id,
            time_window="全天",
            status="unassigned",  # unassigned状态可以删除
        )
        db_session.add(order)
        db_session.commit()
        
        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]
        
        # 删除订单
        response = client.delete(
            "/api/orders/O001",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        
        # 验证订单已删除
        # 注意：删除可能是软删除或硬删除，这里验证订单不在列表中
        orders = db_session.query(Order).all()
        assert len(orders) == 0

    @pytest.mark.api
    def test_delete_order_delivering_status(self, client, db_session):
        """测试删除配送中的订单（应该失败）"""
        # 创建测试用户、节点、订单
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
        
        # 创建测试订单（delivering状态）
        from models.order import Order
        order = Order(
            order_code="O001",
            destination_node_id=node.id,
            time_window="全天",
            status="in_transit",  # in_transit状态不可删除
        )
        db_session.add(order)
        db_session.commit()
        
        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]
        
        # 删除订单
        response = client.delete(
            "/api/orders/O001",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # 验证响应（应该是业务错误）
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0  # 业务错误
        assert "不允许删除" in body["message"] or "状态" in body["message"]


class TestUpdateOrder:
    """测试更新订单"""

    @pytest.mark.api
    def test_update_order_success(self, client, db_session):
        """测试成功更新订单"""
        # 创建测试用户、节点、订单
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
        
        # 创建另一个节点（用于更新目的地）
        node2 = Node(
            node_code="SO002",
            name="测试节点2",
            location="测试2",
            latitude=30.6,
            longitude=114.4,
            node_type="sorting_center",
        )
        db_session.add(node2)
        db_session.flush()
        sc2 = SortingCenter(node_id=node2.id, level=0)
        db_session.add(sc2)
        db_session.commit()
        
        # 创建测试订单
        from models.order import Order
        order = Order(
            order_code="O001",
            destination_node_id=node.id,
            time_window="全天",
            status="unassigned",
        )
        db_session.add(order)
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 更新订单
        response = client.put(
            "/api/orders/O001",
            json={
                "destination_node_code": "SO002",
                "time_window": "2026-06-20 9:00-18:00",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        
        # 验证数据库已更新
        db_session.refresh(order)
        assert order.destination_node_id == node2.id
        assert order.time_window == "2026-06-20 9:00-18:00"

    @pytest.mark.api
    def test_update_order_not_found(self, client, db_session):
        """测试更新不存在的订单"""
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
        
        # 更新订单（不存在）
        response = client.put(
            "/api/orders/O_NONEXIST",
            json={
                "destination_node_code": "SO001",
                "time_window": "全天",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # 验证响应（业务错误）
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
        assert "订单" in body["message"] or "不存在" in body["message"]

    @pytest.mark.api
    def test_update_order_delivering_status(self, client, db_session):
        """测试更新配送中的订单（应该失败）"""
        # 创建测试用户、节点、订单
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
        
        # 创建测试订单（in_transit状态）
        from models.order import Order
        order = Order(
            order_code="O001",
            destination_node_id=node.id,
            time_window="全天",
            status="in_transit",  # in_transit状态不可更新
        )
        db_session.add(order)
        db_session.commit()
        
        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]
        
        # 更新订单
        response = client.put(
            "/api/orders/O001",
            json={
                "destination_node_code": "SO001",
                "time_window": "2026-06-20 9:00-18:00",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # 验证响应（业务错误）
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
        assert "不允许更新" in body["message"] or "状态" in body["message"]

class TestOrderStatusContract:
    """六态筛选、未知状态拒绝、关闭权限"""

    def _prepare(self, client, db_session, statuses=None):
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)
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
        db_session.add(SortingCenter(node_id=node.id, level=0))
        from models.order import Order
        from core.order_status import ORDER_STATUSES

        created = {}
        for status in (statuses or ORDER_STATUSES):
            order = Order(
                order_code=f"O_{status}",
                destination_node_id=node.id,
                time_window="全天",
                status=status,
            )
            db_session.add(order)
            created[status] = order
        db_session.commit()
        token = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        ).json()["data"]["access_token"]
        return {"Authorization": f"Bearer {token}"}, created

    @pytest.mark.api
    def test_filter_each_six_state(self, client, db_session):
        from core.order_status import ORDER_STATUSES

        headers, _ = self._prepare(client, db_session)
        for status in ORDER_STATUSES:
            response = client.get("/api/orders", params={"status": status}, headers=headers)
            assert response.status_code == 200
            body = response.json()
            assert body["code"] == 0
            assert body["data"]["total"] == 1
            assert body["data"]["items"][0]["status"] == status

    @pytest.mark.api
    def test_filter_unknown_status_rejected(self, client, db_session):
        headers, _ = self._prepare(client, db_session, statuses=["unassigned"])
        response = client.get("/api/orders", params={"status": "pending"}, headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 40000
        assert "pending" in body["message"]
        assert "unassigned" in body["message"]

    @pytest.mark.api
    def test_closed_order_cannot_be_updated(self, client, db_session):
        headers, _ = self._prepare(client, db_session, statuses=["closed"])
        response = client.put(
            "/api/orders/O_closed",
            json={"time_window": "09:00-18:00"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["code"] != 0

    @pytest.mark.api
    def test_close_unassigned_order(self, client, db_session):
        headers, _ = self._prepare(client, db_session, statuses=["unassigned"])
        response = client.post("/api/orders/O_unassigned/close", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["status"] == "closed"

    @pytest.mark.api
    def test_close_in_transit_rejected(self, client, db_session):
        headers, _ = self._prepare(client, db_session, statuses=["in_transit"])
        response = client.post("/api/orders/O_in_transit/close", headers=headers)
        assert response.status_code == 200
        assert response.json()["code"] != 0
