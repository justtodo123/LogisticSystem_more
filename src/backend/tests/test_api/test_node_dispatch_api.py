"""
test_node_dispatch_api.py — 阶段4 API接口测试

测试用例：
1. POST /api/schedule/node-dispatch：正常触发调度
2. POST /api/schedule/node-dispatch：调度失败（无可用车辆）
3. POST /api/schedule/node-dispatch：调度方案不存在
4. POST /api/schedule/node-dispatch：权限验证（manager不能调用）
5. GET /api/schedule/batches：获取批次列表
6. GET /api/schedule/batches：按状态筛选
7. GET /api/schedule/batches/{batch_code}：获取批次详情
8. GET /api/schedule/batches/{batch_code}：返回 unallocated_packages
9. GET /api/schedule/batches/{batch_code}：批次不存在
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
import jwt
from datetime import datetime, timedelta, timezone

from config.database import get_db, settings, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.user import User
from models.node import Node
from models.storage_center import StorageCenter
from models.sorting_center import SortingCenter
from models.order import Order
from models.goods import Goods
from models.vehicle import Vehicle
from models.driver import Driver
from models.dispatch_batch import DispatchBatch
from models.node_dispatch import NodeDispatch
from models.package import Package

from main import app


# ── 测试数据库与客户端 ──

@pytest.fixture(scope="function")
def test_db():
    """创建独立的内存 SQLite 数据库"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def client(test_db):
    """创建 AsyncClient，使用内存数据库覆盖依赖"""
    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async_client = AsyncClient(transport=transport, base_url="http://test")

    yield async_client

    app.dependency_overrides.clear()


# ── 辅助函数 ──

def create_dispatcher_token():
    """生成 dispatcher 角色的 JWT Token"""
    return jwt.encode(
        {
            "sub": "dispatcher",
            "role": "dispatcher",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
        settings.JWT_SECRET,
        algorithm="HS256",
    )


def create_manager_token():
    """生成 manager 角色的 JWT Token"""
    return jwt.encode(
        {
            "sub": "manager",
            "role": "manager",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
        settings.JWT_SECRET,
        algorithm="HS256",
    )


def seed_test_data(db):
    """初始化测试数据（用户、节点、车辆、司机、订单、货物、包裹）"""
    # ── 用户 ──
    import bcrypt
    pwd = bcrypt.hashpw("123456".encode(), bcrypt.gensalt()).decode()
    for role in ["dispatcher", "manager"]:
        if not db.query(User).filter(User.username == role).first():
            db.add(User(username=role, password_hash=pwd, role=role))
    
    # ── 节点 ──
    nodes = {}
    nodes_data = [
        ("SC001", "存储中心", "武汉市", 30.58, 114.30, "storage_center", 1000.0),
        ("SO001", "一级分拣中心", "武汉市", 30.59, 114.31, "sorting_center", 100),
        ("SO010", "0级分拣中心", "武汉市武昌区", 30.54, 114.315, "sorting_center", 50),
    ]

    for code, name, loc, lat, lng, ntype, capacity in nodes_data:
        node = Node(
            node_code=code, name=name, location=loc,
            latitude=lat, longitude=lng, node_type=ntype,
        )
        db.add(node)
        db.flush()

        if ntype == "storage_center":
            db.add(StorageCenter(node_id=node.id, capacity=capacity, inventory=0))
        elif ntype == "sorting_center":
            level = 1 if "SO001" in code else 0
            db.add(SortingCenter(node_id=node.id, level=level, capacity=capacity, max_storage_time=24))
        nodes[code] = node

    # ── 车辆 ──
    vehicles = {}
    for i, (node_code, vid) in enumerate([("SC001", 1), ("SC001", 2)]):
        vehicle = Vehicle(
            vehicle_code=f"VEH{node_code}{vid:02d}",
            model="货车",
            capacity=100.0 + i * 50,
            energy_type="fuel",
            status="idle",
            node_id=nodes[node_code].id,
            last_arrived_node_id=nodes[node_code].id,
        )
        db.add(vehicle)
        db.flush()
        vehicles[f"{node_code}_{vid}"] = vehicle

    # ── 司机 ──
    for i, (node_code, did) in enumerate([("SC001", 1), ("SC001", 2)]):
        driver = Driver(
            driver_code=f"DRV{node_code}{did:02d}",
            name=f"司机{i+1}",
            phone="13800138000",
            license_type="C1",  # 添加必填字段
            shift="day",  # 添加必填字段
            status="idle",
            node_id=nodes[node_code].id,
        )
        db.add(driver)

    # ── 订单 ──
    orders = {}
    order = Order(
        order_code="O001",
        destination_node_id=nodes["SO010"].id,
        time_window="全天",
        status="pending",
    )
    db.add(order)
    db.flush()
    orders["O001"] = order

    # ── 货物 ──
    goods = Goods(
        goods_code="G001",
        goods_name="测试货物",
        goods_type="普通",
        weight=10.0,
        volume=0.5,
        node_id=nodes["SC001"].id,
        order_id=order.id,
        status="pending_pack",
    )
    db.add(goods)

    db.commit()
    return nodes, vehicles, orders


def seed_schedule_data(db, nodes):
    """创建全局调度方案和包裹"""
    from models.global_schedule import GlobalSchedule

    # 创建全局调度方案
    schedule = GlobalSchedule(
        schedule_code="GS_TEST001",
        order_codes=["O001"],
        goods_schedules=[
            {"goods_code": "G001", "order_code": "O001", "path": ["SC001", "SO001", "SO010"]}
        ],
        total_distance=0,
        total_time=0,
        total_goods=1,
        score=0,
    )
    db.add(schedule)
    db.flush()

    # 创建包裹
    pkg = Package(
        package_code="PKG_TEST001",
        weight=10.0,
        volume=0.5,
        status="packed",
        from_node_id=nodes["SC001"].id,
        to_node_id=nodes["SO001"].id,
        goods_items=[{"goods_code": "G001", "order_code": "O001"}],
        schedule_id=schedule.id,
    )
    db.add(pkg)
    db.commit()

    return schedule


class TestPostNodeDispatch:
    """POST /api/schedule/node-dispatch"""

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_create_success(self, client, test_db):
        """正常触发调度"""
        # 创建测试数据
        nodes, vehicles, orders = seed_test_data(test_db)
        schedule = seed_schedule_data(test_db, nodes)

        # 调用API
        token = create_dispatcher_token()
        response = await client.post(
            "/api/schedule/node-dispatch",
            json={"schedule_code": "GS_TEST001", "demo_mode": True},
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["message"] == "success"
        assert "batch_code" in body["data"]
        assert body["data"]["status"] == "completed"
        assert "unallocated_packages" in body["data"]

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_create_no_vehicle(self, client, test_db):
        """调度失败：无可用车辆"""
        # 初始化测试数据（用户、节点、车辆等）
        seed_test_data(test_db)
        
        # 删除所有车辆，模拟无可用车辆的场景
        from models.vehicle import Vehicle
        test_db.query(Vehicle).delete()
        test_db.commit()
        
        # 获取已创建的节点
        from models.node import Node
        from_node = test_db.query(Node).filter(Node.node_code == "SC001").first()
        to_node = test_db.query(Node).filter(Node.node_code == "SO001").first()
        
        # 创建调度方案和包裹
        from models.global_schedule import GlobalSchedule
        from models.package import Package
        schedule = GlobalSchedule(
            schedule_code="GS_TEST002",
            order_codes=["O001"],
            goods_schedules=[{"goods_code": "G001", "order_code": "O001", "path": ["SC001", "SO001", "SO010"]}],
            total_distance=0,
            total_time=0,
            total_goods=0,
            score=0,
        )
        test_db.add(schedule)
        test_db.flush()

        pkg = Package(
            package_code="PKG_TEST002",
            weight=10.0,
            volume=0.5,
            status="packed",
            from_node_id=from_node.id,
            to_node_id=to_node.id,
            goods_items=[{"goods_code": "G001", "order_code": "O001"}],
            schedule_id=schedule.id,
        )
        test_db.add(pkg)
        test_db.commit()

        # 调用API（应失败）
        token = create_dispatcher_token()
        response = await client.post(
            "/api/schedule/node-dispatch",
            json={"schedule_code": "GS_TEST002", "demo_mode": True},
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证错误响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 40001
        assert "调度失败" in body["message"]

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_create_schedule_not_found(self, client, test_db):
        """调度方案不存在"""
        # 初始化测试数据（用户）
        seed_test_data(test_db)
        
        token = create_dispatcher_token()
        response = await client.post(
            "/api/schedule/node-dispatch",
            json={"schedule_code": "GS_NONEXIST", "demo_mode": True},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 40401
        assert "不存在" in body["message"]

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_create_forbidden_manager(self, client, test_db):
        """manager 角色 → 403"""
        # 初始化测试数据（用户）
        seed_test_data(test_db)
        
        token = create_manager_token()
        response = await client.post(
            "/api/schedule/node-dispatch",
            json={"schedule_code": "GS_TEST001", "demo_mode": True},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_create_unauthorized(self, client):
        """未认证 → 401"""
        response = await client.post(
            "/api/schedule/node-dispatch",
            json={"schedule_code": "GS_TEST001", "demo_mode": True},
        )

        assert response.status_code == 401


class TestGetDispatchBatches:
    """GET /api/schedule/batches"""

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_get_empty(self, client, test_db):
        """空数据库 → 返回空列表"""
        # 初始化测试数据（用户）
        seed_test_data(test_db)
        
        token = create_dispatcher_token()
        response = await client.get(
            "/api/schedule/batches",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["total"] == 0
        assert body["data"]["items"] == []

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_get_with_data(self, client, test_db):
        """有数据 → 返回批次列表"""
        # 创建测试数据
        nodes, vehicles, orders = seed_test_data(test_db)
        schedule = seed_schedule_data(test_db, nodes)

        # 先执行一次调度
        token = create_dispatcher_token()
        await client.post(
            "/api/schedule/node-dispatch",
            json={"schedule_code": "GS_TEST001", "demo_mode": True},
            headers={"Authorization": f"Bearer {token}"},
        )

        # 查询列表
        response = await client.get(
            "/api/schedule/batches",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["total"] >= 1
        assert len(body["data"]["items"]) >= 1

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_get_filter_by_status(self, client, test_db):
        """按状态筛选"""
        # 创建测试数据并执行调度
        nodes, vehicles, orders = seed_test_data(test_db)
        schedule = seed_schedule_data(test_db, nodes)

        token = create_dispatcher_token()
        await client.post(
            "/api/schedule/node-dispatch",
            json={"schedule_code": "GS_TEST001", "demo_mode": True},
            headers={"Authorization": f"Bearer {token}"},
        )

        # 按 status='completed' 筛选
        response = await client.get(
            "/api/schedule/batches?status=completed",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        # 所有返回的批次状态都应为 'completed'
        for item in body["data"]["items"]:
            assert item["status"] == "completed"

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_get_unauthorized(self, client):
        """未认证 → 401"""
        response = await client.get("/api/schedule/batches")
        assert response.status_code == 401


class TestGetDispatchBatchDetail:
    """GET /api/schedule/batches/{batch_code}"""

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_get_detail_success(self, client, test_db):
        """正常获取批次详情"""
        # 创建测试数据并执行调度
        nodes, vehicles, orders = seed_test_data(test_db)
        schedule = seed_schedule_data(test_db, nodes)

        token = create_dispatcher_token()
        create_resp = await client.post(
            "/api/schedule/node-dispatch",
            json={"schedule_code": "GS_TEST001", "demo_mode": True},
            headers={"Authorization": f"Bearer {token}"},
        )
        batch_code = create_resp.json()["data"]["batch_code"]

        # 获取详情
        response = await client.get(
            f"/api/schedule/batches/{batch_code}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        data = body["data"]
        assert data["batch_code"] == batch_code
        assert "unallocated_packages" in data
        assert "dispatches" in data

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_get_detail_with_unallocated(self, client, test_db):
        """批次详情包含 unallocated_packages"""
        # 创建测试数据
        nodes, vehicles, orders = seed_test_data(test_db)
        schedule = seed_schedule_data(test_db, nodes)

        # 创建批次（手动创建，包含未分配包裹）
        from models.global_schedule import GlobalSchedule
        batch = DispatchBatch(
            batch_code="BATCH_TEST001",
            global_schedule_id=schedule.id,
            status="completed",
            demo_mode=True,
            l0_l1_dispatch_count=1,
            l1_l2_dispatch_count=1,
            unallocated_packages='["PKG001", "PKG002"]',
        )
        test_db.add(batch)
        test_db.commit()

        # 获取详情
        token = create_dispatcher_token()
        response = await client.get(
            f"/api/schedule/batches/BATCH_TEST001",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        data = body["data"]
        assert "unallocated_packages" in data
        assert len(data["unallocated_packages"]) == 2

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_get_detail_not_found(self, client, test_db):
        """批次不存在 → 404"""
        # 初始化测试数据（用户）
        seed_test_data(test_db)
        
        token = create_dispatcher_token()
        response = await client.get(
            "/api/schedule/batches/BATCH_NONEXIST",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 40402
        assert "不存在" in body["message"]

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_get_detail_unauthorized(self, client):
        """未认证 → 401"""
        response = await client.get("/api/schedule/batches/BATCH_TEST001")
        assert response.status_code == 401
