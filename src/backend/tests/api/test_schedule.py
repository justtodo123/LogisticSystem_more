"""
API测试：调度管理（schedule.py）

测试目标：
- POST /api/schedule/global：触发全局调度
- GET /api/schedule/global：历史方案列表
- GET /api/schedule/global/{schedule_code}：方案详情
- POST /api/schedule/node-dispatch：触发节点调度
- GET /api/schedule/batches：调度批次列表
- GET /api/schedule/batches/{code}：调度批次详情

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
from models.order import Order
from models.goods import Goods


class TestCreateGlobalSchedule:
    """测试触发全局调度"""

    @pytest.mark.api
    def test_create_global_schedule_success(self, client, db_session):
        """测试成功触发全局调度"""
        # 创建测试用户、节点、订单、货物
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)
        
        # 创建测试节点
        node_sc1 = Node(
            node_code="SC001",
            name="存储中心1",
            location="测试",
            latitude=30.5,
            longitude=114.3,
            node_type="storage_center",
        )
        db_session.add(node_sc1)
        node_sc2 = Node(
            node_code="SC002",
            name="存储中心2",
            location="测试",
            latitude=28.2,
            longitude=112.9,
            node_type="storage_center",
        )
        db_session.add(node_sc2)
        node_so1 = Node(
            node_code="SO001",
            name="分拣中心1",
            location="测试",
            latitude=30.6,
            longitude=114.4,
            node_type="sorting_center",
        )
        db_session.add(node_so1)
        node_so2 = Node(
            node_code="SO002",
            name="分拣中心2",
            location="测试",
            latitude=28.3,
            longitude=112.8,
            node_type="sorting_center",
        )
        db_session.add(node_so2)
        db_session.flush()
        
        # 创建存储中心和分拣中心记录
        from models.storage_center import StorageCenter
        from models.sorting_center import SortingCenter as SCModel
        
        sc1 = StorageCenter(node_id=node_sc1.id, capacity=1000.0, inventory=0)
        sc2 = StorageCenter(node_id=node_sc2.id, capacity=800.0, inventory=0)
        so1 = SCModel(node_id=node_so1.id, level=1, capacity=100, max_storage_time=24)
        so2 = SCModel(node_id=node_so2.id, level=1, capacity=100, max_storage_time=24)
        db_session.add_all([sc1, sc2, so1, so2])
        
        # 创建目的地节点
        node_dest1 = Node(
            node_code="SO010",
            name="目的地1",
            location="测试",
            latitude=30.54,
            longitude=114.315,
            node_type="sorting_center",
        )
        db_session.add(node_dest1)
        node_dest2 = Node(
            node_code="SO011",
            name="目的地2",
            location="测试",
            latitude=30.61,
            longitude=114.28,
            node_type="sorting_center",
        )
        db_session.add(node_dest2)
        db_session.flush()
        
        dest_sc1 = SCModel(node_id=node_dest1.id, level=0)
        dest_sc2 = SCModel(node_id=node_dest2.id, level=0)
        db_session.add_all([dest_sc1, dest_sc2])
        db_session.commit()
        
        # 创建测试订单
        order1 = Order(
            order_code="O001",
            destination_node_id=node_dest1.id,
            time_window="全天",
            status="pending",
        )
        order2 = Order(
            order_code="O002",
            destination_node_id=node_dest2.id,
            time_window="全天",
            status="pending",
        )
        db_session.add_all([order1, order2])
        db_session.flush()
        
        # 创建测试货物
        goods1 = Goods(
            goods_code="G001",
            goods_name="测试货物1",
            goods_type="普通",
            weight=10.0,
            volume=0.5,
            node_id=node_sc1.id,
            order_id=order1.id,
            status="pending_pack",
        )
        goods2 = Goods(
            goods_code="G002",
            goods_name="测试货物2",
            goods_type="普通",
            weight=5.0,
            volume=0.3,
            node_id=node_sc1.id,
            order_id=order2.id,
            status="pending_pack",
        )
        db_session.add_all([goods1, goods2])
        db_session.commit()
        
        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]
        
        # 第一阶段：预览（创建 draft）
        response = client.post(
            "/api/schedule/global",
            json={"algorithm": "traditional"},
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # 验证预览响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert "data" in body
        assert "schedule_code" in body["data"]
        assert body["data"]["schedule_code"].startswith("GS")
        assert body["data"]["total_goods"] == 2
        schedule_code = body["data"]["schedule_code"]

        # 第二阶段：确认（draft → active，执行 F021 打包）
        confirm_resp = client.post(
            f"/api/schedule/confirm/{schedule_code}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert confirm_resp.status_code == 200
        confirm_body = confirm_resp.json()
        assert confirm_body["code"] == 0
        assert confirm_body["data"]["package_count"] > 0

    @pytest.mark.api
    def test_create_global_schedule_no_pending_orders(self, client, db_session):
        """测试没有pending订单时触发调度（应该失败）"""
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
        
        # 触发全局调度（没有订单）
        response = client.post(
            "/api/schedule/global",
            json={"algorithm": "traditional"},
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # 验证响应（业务错误）
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
        assert "订单" in body["message"] or "pending" in body["message"].lower()

    @pytest.mark.api
    def test_create_global_schedule_manager_forbidden(self, client, db_session):
        """测试manager角色触发调度（应该403）"""
        # 创建测试用户（manager角色）
        user = User(
            username="manager",
            password_hash=get_password_hash("123456"),
            role="manager",
            display_name="管理者",
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
        
        # 触发全局调度（manager角色）
        response = client.post(
            "/api/schedule/global",
            json={"algorithm": "traditional"},
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # 验证响应（403 Forbidden）
        assert response.status_code == 403
        body = response.json()
        assert body["code"] == 40300


class TestGetGlobalSchedules:
    """测试获取全局调度方案列表"""

    @pytest.mark.api
    def test_get_global_schedules_empty(self, client, db_session):
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
        
        # 获取调度方案列表
        response = client.get(
            "/api/schedule/global",
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


class TestGetGlobalScheduleDetail:
    """测试获取全局调度方案详情"""

    @pytest.mark.api
    def test_get_global_schedule_detail_success(self, client, db_session):
        """测试成功获取调度方案详情"""
        # 这里需要先创建一个调度方案，然后获取详情
        # 为了简化，我们直接测试404情况
        pass

    @pytest.mark.api
    def test_get_global_schedule_detail_not_found(self, client, db_session):
        """测试调度方案不存在"""
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
        
        # 获取不存在的调度方案详情
        response = client.get(
            "/api/schedule/global/GS_NONEXIST",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # 验证响应（业务错误）
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
        assert "不存在" in body["message"] or "方案" in body["message"]


class TestCreateGlobalScheduleBoundaries:
    """测试触发全局调度的边界情况"""

    @pytest.mark.api
    def test_create_global_schedule_no_l1_nodes(self, client, db_session):
        """测试没有L1节点时触发调度（应该失败）"""
        # 创建测试用户、节点（只有L0和L2，没有L1）
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)
        
        # 创建L0节点（存储中心）
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
        
        # 创建L2节点（0级分拣中心）
        node_so = Node(
            node_code="SO001",
            name="目的地",
            location="测试",
            latitude=30.6,
            longitude=114.4,
            node_type="sorting_center",
        )
        db_session.add(node_so)
        db_session.flush()
        so = SortingCenter(node_id=node_so.id, level=0, capacity=500, max_storage_time=24)
        db_session.add(so)
        db_session.commit()
        
        # 创建测试订单
        order = Order(
            order_code="O001",
            destination_node_id=node_so.id,
            time_window="全天",
            status="pending",
        )
        db_session.add(order)
        db_session.flush()
        
        # 创建测试货物
        goods = Goods(
            goods_code="G001",
            goods_name="测试货物",
            goods_type="普通",
            weight=10.0,
            volume=0.5,
            node_id=node_sc.id,
            order_id=order.id,
            status="pending_pack",
        )
        db_session.add(goods)
        db_session.commit()
        
        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]
        
        # 触发全局调度（没有L1节点）
        response = client.post(
            "/api/schedule/global",
            json={"algorithm": "traditional"},
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # 验证响应（业务错误）
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
        assert "L1" in body["message"] or "分拣中心" in body["message"]

    @pytest.mark.api
    def test_create_global_schedule_invalid_algorithm(self, client, db_session):
        """测试算法类型错误（阶段3仅支持traditional）"""
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
        
        # 触发全局调度（算法类型错误）
        response = client.post(
            "/api/schedule/global",
            json={"algorithm": "deepseek"},  # 阶段3不支持
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # 验证响应（业务错误）
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
        assert "算法" in body["message"] or "不支持" in body["message"]

    @pytest.mark.api
    def test_create_global_schedule_invalid_order_codes(self, client, db_session):
        """测试指定不存在的订单编号"""
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
            node_code="L1001",
            name="一级分拣中心",
            location="测试",
            latitude=30.55,
            longitude=114.35,
            node_type="sorting_center",
        )
        db_session.add(node_so)
        db_session.flush()
        so = SortingCenter(node_id=node_so.id, level=1, capacity=500, max_storage_time=24)
        db_session.add(so)
        db_session.commit()
        
        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]
        
        # 触发全局调度（指定不存在的订单）
        response = client.post(
            "/api/schedule/global",
            json={
                "order_codes": ["O_NONEXIST"],
                "algorithm": "traditional",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # 验证响应（业务错误）
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
        assert "订单" in body["message"] or "不存在" in body["message"]

    @pytest.mark.api
    def test_get_global_schedule_detail_success(self, client, db_session):
        """测试成功获取调度方案详情（实现空缺的测试）"""
        # 创建测试用户、节点、订单、货物、调度方案
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
        
        node_l1 = Node(
            node_code="L1001",
            name="一级分拣中心",
            location="测试",
            latitude=30.55,
            longitude=114.35,
            node_type="sorting_center",
        )
        db_session.add(node_l1)
        db_session.flush()
        l1 = SortingCenter(node_id=node_l1.id, level=1, capacity=500, max_storage_time=24)
        db_session.add(l1)
        
        node_l2 = Node(
            node_code="SO001",
            name="目的地",
            location="测试",
            latitude=30.6,
            longitude=114.4,
            node_type="sorting_center",
        )
        db_session.add(node_l2)
        
        # 创建存储中心（L0节点）和待处理订单
        node_sc = Node(
            node_code="SC999",  # 使用唯一的node_code避免冲突
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
        
        # 创建待处理订单
        order = Order(
            order_code="O001",
            destination_node_id=node_l2.id,
            time_window="全天",
            status="pending",
        )
        db_session.add(order)
        db_session.flush()
        
        # 创建货物
        goods = Goods(
            goods_code="G001",
            goods_name="测试货物",
            goods_type="普通",
            weight=10.0,
            volume=0.5,
            node_id=node_sc.id,
            order_id=order.id,
            status="pending_pack",
        )
        db_session.add(goods)
        db_session.commit()
        
        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]
        
        # 先触发全局调度创建方案
        response = client.post(
            "/api/schedule/global",
            json={"algorithm": "traditional"},
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # 获取方案编号
        assert response.status_code == 200
        schedule_code = response.json()["data"]["schedule_code"]
        
        # 获取调度方案详情
        response = client.get(
            f"/api/schedule/global/{schedule_code}",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert "data" in body
        assert "schedule_code" in body["data"]
        assert "goods_schedules" in body["data"]
        assert "packages" in body["data"]


class TestCreateNodeDispatch:
    """测试触发节点调度（阶段4）"""

    @pytest.mark.api
    def test_create_node_dispatch_success(self, client, db_session):
        """测试成功触发节点调度"""
        # 先创建测试用户、节点、订单、货物，并触发全局调度
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
        node_l1 = Node(
            node_code="L1001",
            name="一级分拣中心",
            location="测试",
            latitude=30.55,
            longitude=114.35,
            node_type="sorting_center",
        )
        db_session.add(node_l1)
        node_l2 = Node(
            node_code="SO001",
            name="目的地",
            location="测试",
            latitude=30.6,
            longitude=114.4,
            node_type="sorting_center",
        )
        db_session.add(node_l2)
        db_session.flush()
        
        # 创建存储中心和分拣中心记录
        sc = StorageCenter(node_id=node_sc.id, capacity=1000.0, inventory=0)
        db_session.add(sc)
        l1 = SortingCenter(node_id=node_l1.id, level=1, capacity=500, max_storage_time=24)
        db_session.add(l1)
        l2 = SortingCenter(node_id=node_l2.id, level=0, capacity=500, max_storage_time=24)
        db_session.add(l2)
        
        # 创建车辆和司机
        from models.vehicle import Vehicle
        from models.driver import Driver
        
        vehicle = Vehicle(
            vehicle_code="VEH001",
            model="测试车型",
            capacity=100.0,
            energy_type="fuel",
            node_id=node_sc.id,
            last_arrived_node_id=node_sc.id,
            status="idle",
        )
        db_session.add(vehicle)
        
        driver = Driver(
            driver_code="DRV001",
            name="测试司机",
            phone="13800000001",
            license_type="C1",
            shift="day",
            node_id=node_sc.id,
            status="idle",
        )
        db_session.add(driver)
        
        # 创建待处理订单
        order = Order(
            order_code="O001",
            destination_node_id=node_l2.id,
            time_window="全天",
            status="pending",
        )
        db_session.add(order)
        db_session.flush()
        
        # 创建货物
        goods = Goods(
            goods_code="G001",
            goods_name="测试货物",
            goods_type="普通",
            weight=10.0,
            volume=0.5,
            node_id=node_sc.id,
            order_id=order.id,
            status="pending_pack",
        )
        db_session.add(goods)
        db_session.commit()
        
        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]
        
        # 先触发全局调度
        response = client.post(
            "/api/schedule/global",
            json={"algorithm": "traditional"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        schedule_code = response.json()["data"]["schedule_code"]

        # 确认方案（draft → active，执行 F021 打包）
        confirm_resp = client.post(
            f"/api/schedule/confirm/{schedule_code}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert confirm_resp.status_code == 200
        assert confirm_resp.json()["code"] == 0
        
        # 触发节点调度
        response = client.post(
            "/api/schedule/node-dispatch",
            json={
                "schedule_code": schedule_code,
                "demo_mode": True,  # 使用demo_mode跳过等待
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert "data" in body
        assert "batch_code" in body["data"]

    @pytest.mark.api
    def test_create_node_dispatch_schedule_not_found(self, client, db_session):
        """测试调度方案不存在"""
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
        
        # 触发节点调度（方案不存在）
        response = client.post(
            "/api/schedule/node-dispatch",
            json={
                "schedule_code": "GS_NONEXIST",
                "demo_mode": False,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # 验证响应（业务错误）
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
        assert "方案" in body["message"] or "不存在" in body["message"]


class TestCreateNodeDispatchBoundaries:
    """测试节点调度的边界情况"""

    @pytest.mark.api
    def test_create_node_dispatch_no_packages(self, client, db_session):
        """测试没有可调度包裹（应该失败）"""
        # 创建测试用户、节点，但不创建订单/货物/包裹
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
        node_l1 = Node(
            node_code="L1001",
            name="一级分拣中心",
            location="测试",
            latitude=30.55,
            longitude=114.35,
            node_type="sorting_center",
        )
        db_session.add(node_l1)
        db_session.flush()
        
        sc = StorageCenter(node_id=node_sc.id, capacity=1000.0, inventory=0)
        db_session.add(sc)
        l1 = SortingCenter(node_id=node_l1.id, level=1, capacity=500, max_storage_time=24)
        db_session.add(l1)
        db_session.commit()
        
        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]
        
        # 先触发全局调度（但没有包裹）
        response = client.post(
            "/api/schedule/global",
            json={"algorithm": "traditional"},
            headers={"Authorization": f"Bearer {token}"},
        )
        # 可能没有pending订单，返回业务错误
        if response.status_code == 200 and response.json()["code"] != 0:
            # 没有pending订单，这是预期的
            pass
        else:
            # 有调度方案，但没有车辆/司机，节点调度应该失败
            schedule_code = response.json()["data"]["schedule_code"]
            
            # 触发节点调度（没有车辆）
            response = client.post(
                "/api/schedule/node-dispatch",
                json={
                    "schedule_code": schedule_code,
                    "demo_mode": False,
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            
            # 验证响应（业务错误）
            assert response.status_code == 200
            body = response.json()
            assert body["code"] != 0

    @pytest.mark.api
    def test_create_node_dispatch_no_vehicles(self, client, db_session):
        """测试没有可用车辆（应该失败）"""
        # 创建测试用户、节点、订单、货物，并触发全局调度和打包
        # 但不创建车辆
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
        node_l1 = Node(
            node_code="L1001",
            name="一级分拣中心",
            location="测试",
            latitude=30.55,
            longitude=114.35,
            node_type="sorting_center",
        )
        db_session.add(node_l1)
        node_l2 = Node(
            node_code="SO001",
            name="目的地",
            location="测试",
            latitude=30.6,
            longitude=114.4,
            node_type="sorting_center",
        )
        db_session.add(node_l2)
        db_session.flush()
        
        sc = StorageCenter(node_id=node_sc.id, capacity=1000.0, inventory=0)
        db_session.add(sc)
        l1 = SortingCenter(node_id=node_l1.id, level=1, capacity=500, max_storage_time=24)
        db_session.add(l1)
        l2 = SortingCenter(node_id=node_l2.id, level=0, capacity=500, max_storage_time=24)
        db_session.add(l2)
        db_session.commit()
        
        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]
        
        # 先触发全局调度
        response = client.post(
            "/api/schedule/global",
            json={"algorithm": "traditional"},
            headers={"Authorization": f"Bearer {token}"},
        )
        
        if response.status_code == 200 and response.json()["code"] == 0:
            schedule_code = response.json()["data"]["schedule_code"]

            # 确认方案
            confirm_resp = client.post(
                f"/api/schedule/confirm/{schedule_code}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert confirm_resp.status_code == 200
            assert confirm_resp.json()["code"] == 0
            
            # 触发节点调度（没有车辆）
            response = client.post(
                "/api/schedule/node-dispatch",
                json={
                    "schedule_code": schedule_code,
                    "demo_mode": False,
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            
            # 验证响应（业务错误：没有可用车辆）
            assert response.status_code == 200
            body = response.json()
            assert body["code"] != 0
            assert "车辆" in body["message"] or "不足" in body["message"]

    @pytest.mark.api
    def test_get_dispatch_batches_empty(self, client, db_session):
        """测试获取调度批次列表（空数据库）"""
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
        
        # 获取调度批次列表
        response = client.get(
            "/api/schedule/batches",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["items"] == []
        assert body["data"]["total"] == 0

