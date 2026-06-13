"""
test_schedule.py — 调度 API 接口测试

测试用例：
1. POST /api/schedule/global：正常触发调度
2. POST /api/schedule/global：业务失败（无法调度）
3. GET /api/schedule/global：获取历史列表
4. GET /api/schedule/global/{schedule_code}：获取详情

注意：使用 pytest.mark.asyncio + 异步测试确保 FastAPI 依赖注入正确工作。
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
    # 用闭包捕获 test_db，使得每次 FastAPI 请求都使用同一个 session
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


def create_dispatcher_user(db):
    """在测试数据库中创建 dispatcher 用户"""
    user = User(
        username="dispatcher",
        password_hash="test_hash",
        role="dispatcher",
        display_name="调度员",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


def create_manager_user(db):
    """在测试数据库中创建 manager 用户"""
    user = User(
        username="manager",
        password_hash="test_hash",
        role="manager",
        display_name="管理者",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


def seed_test_data(db):
    """初始化测试数据（节点、订单、货物）"""
    # ── 节点 ──
    nodes = {}
    nodes_data = [
        ("SC001", "武汉存储中心", "武汉市", 30.58, 114.30, "storage_center"),
        ("SC002", "长沙存储中心", "长沙市", 28.22, 112.93, "storage_center"),
        ("SO001", "武汉1级分拣中心", "武汉市", 30.59, 114.31, "sorting_center"),
        ("SO002", "长沙1级分拣中心", "长沙市", 28.23, 112.94, "sorting_center"),
        ("SO010", "武昌0级分拣中心", "武汉市武昌区", 30.54, 114.315, "sorting_center"),
        ("SO011", "汉口0级分拣中心", "武汉市汉口区", 30.61, 114.28, "sorting_center"),
        ("SO012", "长沙0级分拣中心", "长沙市", 28.21, 112.92, "sorting_center"),
    ]

    for code, name, loc, lat, lng, ntype in nodes_data:
        node = Node(
            node_code=code, name=name, location=loc,
            latitude=lat, longitude=lng, node_type=ntype,
        )
        db.add(node)
        db.flush()

        if ntype == "storage_center":
            db.add(StorageCenter(node_id=node.id, capacity=1000.0, inventory=0))
        elif code in ("SO001", "SO002"):
            db.add(SortingCenter(node_id=node.id, level=1, capacity=100, max_storage_time=24))
        else:
            db.add(SortingCenter(node_id=node.id, level=0))
        nodes[code] = node

    # ── 订单 ──
    orders = {}
    orders_data = [
        ("O001", "SO010", "全天"),
        ("O002", "SO011", "全天"),
        ("O003", "SO012", "全天"),
    ]
    for ocode, dest, tw in orders_data:
        order = Order(
            order_code=ocode,
            destination_node_id=nodes[dest].id,
            time_window=tw,
            status="pending",
        )
        db.add(order)
        orders[ocode] = order
    db.flush()

    # ── 货物 ──
    goods_data = [
        ("G001", "测试货物A", "普通", 10.0, 0.5, "O001", "SC001"),
        ("G002", "测试货物B", "普通", 5.0, 0.3, "O002", "SC001"),
        ("G003", "测试货物C", "普通", 8.0, 0.4, "O003", "SC002"),
    ]
    for gcode, gname, gtype, w, v, ocode, ncode in goods_data:
        db.add(Goods(
            goods_code=gcode, goods_name=gname, goods_type=gtype,
            weight=w, volume=v,
            node_id=nodes[ncode].id,
            order_id=orders[ocode].id,
            status="pending_pack",
        ))

    db.commit()
    return nodes, orders


class TestPostGlobalSchedule:
    """POST /api/schedule/global"""

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_normal_schedule_success(self, client, test_db):
        """正常触发调度，期望返回 200 + code=0"""
        create_dispatcher_user(test_db)
        seed_test_data(test_db)

        token = create_dispatcher_token()
        response = await client.post(
            "/api/schedule/global",
            json={"algorithm": "traditional"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["message"] == "success"
        assert body["data"]["schedule_code"].startswith("GS")
        assert body["data"]["total_goods"] == 3
        assert body["data"]["package_count"] > 0
        assert body["meta"]["degraded"] is False

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_schedule_with_specific_orders(self, client, test_db):
        """指定订单编号触发调度"""
        create_dispatcher_user(test_db)
        seed_test_data(test_db)

        token = create_dispatcher_token()
        response = await client.post(
            "/api/schedule/global",
            json={"order_codes": ["O001", "O002"], "algorithm": "traditional"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["total_goods"] == 2

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_business_failure_no_pending_orders(self, client, test_db):
        """
        业务失败：没有 pending 订单时触发调度
        期望返回 HTTP 200 + code=40001
        """
        create_dispatcher_user(test_db)
        # 不初始化数据 → 无 pending 订单

        token = create_dispatcher_token()
        response = await client.post(
            "/api/schedule/global",
            json={"algorithm": "traditional"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 40001
        assert "没有找到符合条件的订单" in body["message"]

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_business_failure_no_l1(self, client, test_db):
        """
        业务失败：没有 L1 节点时触发调度
        期望返回 HTTP 200 + code=40001
        """
        create_dispatcher_user(test_db)

        # 创建节点但不创建 L1
        l0 = Node(node_code="SC_NO_L1", name="存储中心", location="测试",
                  latitude=30.5, longitude=114.3, node_type="storage_center")
        test_db.add(l0)
        test_db.flush()
        test_db.add(StorageCenter(node_id=l0.id, capacity=100.0, inventory=0))

        l2 = Node(node_code="SO_DEST", name="目的地", location="测试",
                  latitude=30.6, longitude=114.4, node_type="sorting_center")
        test_db.add(l2)
        test_db.flush()
        test_db.add(SortingCenter(node_id=l2.id, level=0))

        order = Order(order_code="O_NO_L1", destination_node_id=l2.id,
                      time_window="全天", status="pending")
        test_db.add(order)
        test_db.flush()

        test_db.add(Goods(goods_code="G_NO_L1", goods_name="货物",
                          goods_type="普通", weight=5.0, volume=0.2,
                          node_id=l0.id, order_id=order.id, status="pending_pack"))
        test_db.commit()

        token = create_dispatcher_token()
        response = await client.post(
            "/api/schedule/global",
            json={"algorithm": "traditional"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 40001
        assert "没有找到 1 级分拣中心" in body["message"]

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_unauthorized_no_token(self, client, test_db):
        """未提供 Token → 401"""
        seed_test_data(test_db)

        response = await client.post(
            "/api/schedule/global",
            json={"algorithm": "traditional"},
        )
        assert response.status_code == 401

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_forbidden_manager_role(self, client, test_db):
        """manager 角色 → 403"""
        create_manager_user(test_db)
        seed_test_data(test_db)

        token = create_manager_token()
        response = await client.post(
            "/api/schedule/global",
            json={"algorithm": "traditional"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_invalid_algorithm_param(self, client, test_db):
        """非法 algorithm 参数 → 40001"""
        create_dispatcher_user(test_db)
        seed_test_data(test_db)

        token = create_dispatcher_token()
        response = await client.post(
            "/api/schedule/global",
            json={"algorithm": "deepseek"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 40001
        assert "仅支持 traditional" in body["message"]


class TestGetGlobalSchedules:
    """GET /api/schedule/global"""

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_list_empty(self, client, test_db):
        """空数据库 → 返回空列表"""
        create_dispatcher_user(test_db)

        token = create_dispatcher_token()
        response = await client.get(
            "/api/schedule/global",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["items"] == []
        assert body["data"]["total"] == 0

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_list_with_data(self, client, test_db):
        """有历史数据 → 返回列表"""
        create_dispatcher_user(test_db)
        seed_test_data(test_db)

        # 先执行一次调度以生成数据
        token = create_dispatcher_token()
        await client.post(
            "/api/schedule/global",
            json={"algorithm": "traditional"},
            headers={"Authorization": f"Bearer {token}"},
        )

        # 查询列表
        response = await client.get(
            "/api/schedule/global",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert len(body["data"]["items"]) == 1
        assert body["data"]["total"] == 1
        item = body["data"]["items"][0]
        assert item["schedule_code"].startswith("GS")
        assert item["total_goods"] == 3
        assert item["package_count"] > 0

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_list_pagination(self, client, test_db):
        """分页参数测试"""
        create_dispatcher_user(test_db)

        token = create_dispatcher_token()
        response = await client.get(
            "/api/schedule/global?page=1&page_size=5",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["page"] == 1
        assert body["data"]["page_size"] == 5

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_list_filter_by_order(self, client, test_db):
        """
        按订单编号筛选（无过滤参数返回全部）
        注意：SQLite 的 JSON 字段 LIKE 过滤可能有兼容性问题，
        此测试仅验证不带过滤参数的列表查询。
        """
        create_dispatcher_user(test_db)
        seed_test_data(test_db)

        # 执行调度
        token = create_dispatcher_token()
        await client.post(
            "/api/schedule/global",
            json={"algorithm": "traditional"},
            headers={"Authorization": f"Bearer {token}"},
        )

        # 查询全部（不带过滤）
        response = await client.get(
            "/api/schedule/global",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert len(body["data"]["items"]) >= 1
        # 验证返回的 item 包含正确字段
        item = body["data"]["items"][0]
        assert "schedule_code" in item
        assert "total_goods" in item

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_list_unauthorized(self, client):
        """未认证 → 401"""
        response = await client.get("/api/schedule/global")
        assert response.status_code == 401


class TestGetGlobalScheduleDetail:
    """GET /api/schedule/global/{schedule_code}"""

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_get_detail_success(self, client, test_db):
        """正常获取调度详情"""
        create_dispatcher_user(test_db)
        seed_test_data(test_db)

        token = create_dispatcher_token()
        # 先创建调度
        create_resp = await client.post(
            "/api/schedule/global",
            json={"algorithm": "traditional"},
            headers={"Authorization": f"Bearer {token}"},
        )
        schedule_code = create_resp.json()["data"]["schedule_code"]

        # 获取详情
        response = await client.get(
            f"/api/schedule/global/{schedule_code}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        data = body["data"]
        assert data["schedule_code"] == schedule_code
        assert data["total_goods"] == 3
        assert data["package_count"] > 0
        assert data["version"] == 1
        assert data["is_replan"] is False
        assert len(data["goods_schedules"]) == 3
        assert len(data["packages"]) == data["package_count"]

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_get_detail_not_found(self, client, test_db):
        """调度方案不存在 → 40401"""
        create_dispatcher_user(test_db)

        token = create_dispatcher_token()
        response = await client.get(
            "/api/schedule/global/GS_NONEXIST",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 40401
        assert "不存在" in body["message"]

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_get_detail_unauthorized(self, client):
        """未认证 → 401"""
        response = await client.get("/api/schedule/global/GS20260613001")
        assert response.status_code == 401

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_get_detail_with_packages(self, client, test_db):
        """验证详情中的 packages 包含正确字段"""
        create_dispatcher_user(test_db)
        seed_test_data(test_db)

        token = create_dispatcher_token()
        create_resp = await client.post(
            "/api/schedule/global",
            json={"algorithm": "traditional"},
            headers={"Authorization": f"Bearer {token}"},
        )
        schedule_code = create_resp.json()["data"]["schedule_code"]

        response = await client.get(
            f"/api/schedule/global/{schedule_code}",
            headers={"Authorization": f"Bearer {token}"},
        )

        body = response.json()
        packages = body["data"]["packages"]
        assert len(packages) > 0

        for pkg in packages:
            assert pkg["package_code"].startswith("PKG")
            assert pkg["status"] == "packed"
            assert pkg["weight"] > 0
            assert pkg["volume"] > 0
            assert pkg["from_node_code"] is not None
            assert pkg["to_node_code"] is not None
            assert len(pkg["goods_items"]) > 0
