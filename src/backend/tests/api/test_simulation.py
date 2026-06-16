"""
API测试：模拟送达（simulation.py）

测试目标：
- POST /api/simulation/deliver：模拟送达接口

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
from models.package import Package
from models.vehicle import Vehicle
import json


class TestDeliverPackages:
    """测试模拟送达接口"""

    @pytest.mark.api
    def test_deliver_success(self, client, db_session):
        """测试成功模拟送达"""
        # 创建测试用户、节点、包裹、车辆
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)
        
        # 创建测试节点
        node_sc = Node(
            node_code="SC001",
            name="存储中心",
            location="测试",
            latitude=30.5,
            longitude=114.3,
            node_type="storage_center",
        )
        db_session.add(node_sc)
        db_session.flush()
        sc = StorageCenter(node_id=node_sc.id, capacity=1000.0, inventory=0)
        db_session.add(sc)
        
        node_so = Node(
            node_code="SO001",
            name="分拣中心",
            location="测试",
            latitude=30.6,
            longitude=114.4,
            node_type="sorting_center",
        )
        db_session.add(node_so)
        db_session.flush()
        so = SortingCenter(node_id=node_so.id, level=1)
        db_session.add(so)
        db_session.commit()
        
        # 创建测试包裹（状态为in_transit）
        package = Package(
            package_code="PKG001",
            from_node_id=node_sc.id,
            to_node_id=node_so.id,
            weight=10.0,
            volume=0.5,
            status="in_transit",
            goods_items=json.dumps([{"goods_code": "G001", "order_code": "O001"}]),
        )
        db_session.add(package)
        
        # 创建测试车辆
        vehicle = Vehicle(
            vehicle_code="VEH001",
            model="测试车型",
            capacity=100.0,
            energy_type="fuel",
            node_id=node_sc.id,
            last_arrived_node_id=node_sc.id,
            status="delivering",
        )
        db_session.add(vehicle)
        db_session.commit()
        
        # 更新包裹的vehicle_id
        package.vehicle_id = vehicle.id
        db_session.commit()
        
        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]
        
        # 模拟送达
        response = client.post(
            "/api/simulation/deliver",
            json={"vehicle_code": "VEH001", "package_code": "PKG001"},
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert "data" in body
        assert "delivered_package_codes" in body["data"]
        assert "PKG001" in body["data"]["delivered_package_codes"]

    @pytest.mark.api
    def test_deliver_no_params(self, client, db_session):
        """测试不传参数（处理所有in_transit包裹）"""
        # 创建测试用户、节点、包裹、车辆
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)
        
        # 创建测试节点
        node_sc = Node(
            node_code="SC001",
            name="存储中心",
            location="测试",
            latitude=30.5,
            longitude=114.3,
            node_type="storage_center",
        )
        db_session.add(node_sc)
        db_session.flush()
        sc = StorageCenter(node_id=node_sc.id, capacity=1000.0, inventory=0)
        db_session.add(sc)
        
        node_so = Node(
            node_code="SO001",
            name="分拣中心",
            location="测试",
            latitude=30.6,
            longitude=114.4,
            node_type="sorting_center",
        )
        db_session.add(node_so)
        db_session.flush()
        so = SortingCenter(node_id=node_so.id, level=1)
        db_session.add(so)
        db_session.commit()
        
        # 创建测试包裹（状态为in_transit）
        package = Package(
            package_code="PKG001",
            from_node_id=node_sc.id,
            to_node_id=node_so.id,
            weight=10.0,
            volume=0.5,
            status="in_transit",
            goods_items=json.dumps([{"goods_code": "G001", "order_code": "O001"}]),
        )
        db_session.add(package)
        
        # 创建测试车辆
        vehicle = Vehicle(
            vehicle_code="VEH001",
            model="测试车型",
            capacity=100.0,
            energy_type="fuel",
            node_id=node_sc.id,
            last_arrived_node_id=node_sc.id,
            status="delivering",
        )
        db_session.add(vehicle)
        db_session.commit()
        
        # 更新包裹的vehicle_id
        package.vehicle_id = vehicle.id
        db_session.commit()
        
        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]
        
        # 模拟送达（不传参数）
        response = client.post(
            "/api/simulation/deliver",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert "data" in body

    @pytest.mark.api
    def test_deliver_package_not_found(self, client, db_session):
        """测试包裹不存在"""
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
        
        # 模拟送达（包裹不存在）
        response = client.post(
            "/api/simulation/deliver",
            json={"package_code": "PKGNONEXIST"},
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # 验证响应（业务错误）
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
        assert "包裹" in body["message"] or "不存在" in body["message"]
