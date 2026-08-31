"""
测试固件（Fixtures）- 全局共享

提供：
- 内存 SQLite 数据库会话
- 测试基础数据工厂（节点、订单、货物、车辆、司机）
- 认证辅助函数
- 全局缓存清理（T4-3，防止跨测试缓存污染）
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base
from models.node import Node
from models.storage_center import StorageCenter
from models.sorting_center import SortingCenter
from models.order import Order
from models.goods import Goods
from models.user import User
from models.vehicle import Vehicle
from models.driver import Driver


@pytest.fixture(autouse=True)
def _clear_global_memory_cache():
    """每个测试前后清空全局内存缓存，避免跨测试污染（T4-3）"""
    from utils.cache import memory_cache
    memory_cache.clear()
    yield
    memory_cache.clear()


# ── 数据库固件 ─────────────────────────────────────────────

@pytest.fixture(scope="function")
def test_db():
    """创建测试数据库引擎和会话工厂，供所有fixture共享"""
    from sqlalchemy.pool import StaticPool
    
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # 使用StaticPool确保所有连接共享同一个数据库连接
    )
    
    # 导入所有模型以确保它们被注册到Base.metadata
    from models import (  # noqa: F401
        User, LogEvent, Node, StorageCenter, SortingCenter,
        Order, Goods, Package, Vehicle, Driver, GlobalSchedule,
        DispatchBatch, NodeDispatch, Route, ExceptionEvent,
        NotificationConfig
    )
    
    Base.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield engine, TestingSessionLocal
    
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_db):
    """创建独立的内存 SQLite 数据库会话，每个测试函数结束后销毁"""
    engine, TestingSessionLocal = test_db
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()


# ── 基础数据固件 ──────────────────────────────────────────────

@pytest.fixture(scope="function")
def test_nodes(db_session):
    """
    创建测试节点数据：
    - SC001: 存储中心 (L0)
    - SC002: 存储中心 (L0)
    - SO001: 1级分拣中心 (L1)，容量=100，最大存储时长=24h
    - SO002: 1级分拣中心 (L1)，容量=100，最大存储时长=24h
    - SO010: 0级分拣中心 (L2)
    - SO011: 0级分拣中心 (L2)
    - SO012: 0级分拣中心 (L2)
    """
    nodes_data = [
        {
            "node_code": "SC001", "name": "武汉存储中心",
            "location": "武汉市", "latitude": 30.580000, "longitude": 114.300000,
            "node_type": "storage_center",
            "sc_extra": {"capacity": 1000.0},
        },
        {
            "node_code": "SC002", "name": "长沙存储中心",
            "location": "长沙市", "latitude": 28.220000, "longitude": 112.930000,
            "node_type": "storage_center",
            "sc_extra": {"capacity": 800.0},
        },
        {
            "node_code": "SO001", "name": "武汉1级分拣中心",
            "location": "武汉市", "latitude": 30.590000, "longitude": 114.310000,
            "node_type": "sorting_center",
            "sc_extra": {"level": 1, "capacity": 100, "max_storage_time": 24},
        },
        {
            "node_code": "SO002", "name": "长沙1级分拣中心",
            "location": "长沙市", "latitude": 28.230000, "longitude": 112.940000,
            "node_type": "sorting_center",
            "sc_extra": {"level": 1, "capacity": 100, "max_storage_time": 24},
        },
        {
            "node_code": "SO010", "name": "武昌0级分拣中心",
            "location": "武汉市武昌区", "latitude": 30.540000, "longitude": 114.315000,
            "node_type": "sorting_center",
            "sc_extra": {"level": 0},
        },
        {
            "node_code": "SO011", "name": "汉口0级分拣中心",
            "location": "武汉市汉口区", "latitude": 30.610000, "longitude": 114.280000,
            "node_type": "sorting_center",
            "sc_extra": {"level": 0},
        },
        {
            "node_code": "SO012", "name": "长沙0级分拣中心",
            "location": "长沙市", "latitude": 28.210000, "longitude": 112.920000,
            "node_type": "sorting_center",
            "sc_extra": {"level": 0},
        },
    ]

    node_objects = {}
    for nd in nodes_data:
        node = Node(
            node_code=nd["node_code"],
            name=nd["name"],
            location=nd["location"],
            latitude=nd["latitude"],
            longitude=nd["longitude"],
            node_type=nd["node_type"],
        )
        db_session.add(node)
        db_session.flush()

        if nd["node_type"] == "storage_center":
            sc = StorageCenter(
                node_id=node.id,
                capacity=nd["sc_extra"]["capacity"],
                inventory=0,
            )
        else:
            sc = SortingCenter(
                node_id=node.id,
                level=nd["sc_extra"].get("level", 0),
                capacity=nd["sc_extra"].get("capacity"),
                max_storage_time=nd["sc_extra"].get("max_storage_time"),
            )
        db_session.add(sc)
        node_objects[nd["node_code"]] = node

    db_session.commit()
    return node_objects


@pytest.fixture(scope="function")
def test_orders(db_session, test_nodes):
    """
    创建测试订单数据：
    - O001: 目的地 SO010（武昌），来自 SC001
    - O002: 目的地 SO011（汉口），来自 SC001
    - O003: 目的地 SO012（长沙），来自 SC002
    - O004: 目的地 SO010（武昌），来自 SC001
    - O005: 目的地 SO011（汉口），来自 SC001
    - O006: 目的地 SO012（长沙），来自 SC002
    - O007: 目的地 SO010（武昌），来自 SC001
    - O008: 目的地 SO011（汉口），来自 SC001
    - O009: 目的地 SO012（长沙），来自 SC002
    """
    orders_data = [
        {
            "order_code": "O001",
            "destination_node_code": "SO010",
            "time_window": "2026-06-15 全天",
        },
        {
            "order_code": "O002",
            "destination_node_code": "SO011",
            "time_window": "2026-06-15 全天",
        },
        {
            "order_code": "O003",
            "destination_node_code": "SO012",
            "time_window": "2026-06-15 全天",
        },
        {
            "order_code": "O004",
            "destination_node_code": "SO010",
            "time_window": "2026-06-15 全天",
        },
        {
            "order_code": "O005",
            "destination_node_code": "SO011",
            "time_window": "2026-06-15 全天",
        },
        {
            "order_code": "O006",
            "destination_node_code": "SO012",
            "time_window": "2026-06-15 全天",
        },
        {
            "order_code": "O007",
            "destination_node_code": "SO010",
            "time_window": "2026-06-15 全天",
        },
        {
            "order_code": "O008",
            "destination_node_code": "SO011",
            "time_window": "2026-06-15 全天",
        },
        {
            "order_code": "O009",
            "destination_node_code": "SO012",
            "time_window": "2026-06-15 全天",
        },
    ]
    
    order_objects = {}
    for od in orders_data:
        order = Order(
            order_code=od["order_code"],
            destination_node_id=test_nodes[od["destination_node_code"]].id,
            time_window=od["time_window"],
            status="unassigned",
        )
        db_session.add(order)
        order_objects[od["order_code"]] = order
    
    db_session.commit()
    return order_objects


@pytest.fixture(scope="function")
def test_goods(db_session, test_orders, test_nodes):
    """
    创建测试货物数据：
    - 每个订单有2-3个货物
    - 总计约20个货物，用于测试复杂场景（L1节点包裹数量众多）
    """
    goods_data = [
        # O001的货物（2个）
        {
            "goods_code": "G001",
            "goods_name": "测试货物A1",
            "goods_type": "普通",
            "weight": 10.0,
            "volume": 0.5,
            "order_code": "O001",
            "node_code": "SC001",
        },
        {
            "goods_code": "G002",
            "goods_name": "测试货物A2",
            "goods_type": "普通",
            "weight": 15.0,
            "volume": 0.8,
            "order_code": "O001",
            "node_code": "SC001",
        },
        # O002的货物（2个）
        {
            "goods_code": "G003",
            "goods_name": "测试货物B1",
            "goods_type": "普通",
            "weight": 5.0,
            "volume": 0.3,
            "order_code": "O002",
            "node_code": "SC001",
        },
        {
            "goods_code": "G004",
            "goods_name": "测试货物B2",
            "goods_type": "普通",
            "weight": 8.0,
            "volume": 0.4,
            "order_code": "O002",
            "node_code": "SC001",
        },
        # O003的货物（2个）
        {
            "goods_code": "G005",
            "goods_name": "测试货物C1",
            "goods_type": "普通",
            "weight": 12.0,
            "volume": 0.6,
            "order_code": "O003",
            "node_code": "SC002",
        },
        {
            "goods_code": "G006",
            "goods_name": "测试货物C2",
            "goods_type": "普通",
            "weight": 9.0,
            "volume": 0.5,
            "order_code": "O003",
            "node_code": "SC002",
        },
        # O004的货物（2个）
        {
            "goods_code": "G007",
            "goods_name": "测试货物D1",
            "goods_type": "普通",
            "weight": 11.0,
            "volume": 0.7,
            "order_code": "O004",
            "node_code": "SC001",
        },
        {
            "goods_code": "G008",
            "goods_name": "测试货物D2",
            "goods_type": "普通",
            "weight": 7.0,
            "volume": 0.4,
            "order_code": "O004",
            "node_code": "SC001",
        },
        # O005的货物（2个）
        {
            "goods_code": "G009",
            "goods_name": "测试货物E1",
            "goods_type": "普通",
            "weight": 6.0,
            "volume": 0.3,
            "order_code": "O005",
            "node_code": "SC001",
        },
        {
            "goods_code": "G010",
            "goods_name": "测试货物E2",
            "goods_type": "普通",
            "weight": 9.0,
            "volume": 0.5,
            "order_code": "O005",
            "node_code": "SC001",
        },
        # O006的货物（2个）
        {
            "goods_code": "G011",
            "goods_name": "测试货物F1",
            "goods_type": "普通",
            "weight": 13.0,
            "volume": 0.8,
            "order_code": "O006",
            "node_code": "SC002",
        },
        {
            "goods_code": "G012",
            "goods_name": "测试货物F2",
            "goods_type": "普通",
            "weight": 8.0,
            "volume": 0.4,
            "order_code": "O006",
            "node_code": "SC002",
        },
        # O007的货物（2个）
        {
            "goods_code": "G013",
            "goods_name": "测试货物G1",
            "goods_type": "普通",
            "weight": 10.0,
            "volume": 0.6,
            "order_code": "O007",
            "node_code": "SC001",
        },
        {
            "goods_code": "G014",
            "goods_name": "测试货物G2",
            "goods_type": "普通",
            "weight": 12.0,
            "volume": 0.7,
            "order_code": "O007",
            "node_code": "SC001",
        },
        # O008的货物（2个）
        {
            "goods_code": "G015",
            "goods_name": "测试货物H1",
            "goods_type": "普通",
            "weight": 7.0,
            "volume": 0.4,
            "order_code": "O008",
            "node_code": "SC001",
        },
        {
            "goods_code": "G016",
            "goods_name": "测试货物H2",
            "goods_type": "普通",
            "weight": 9.0,
            "volume": 0.5,
            "order_code": "O008",
            "node_code": "SC001",
        },
        # O009的货物（2个）
        {
            "goods_code": "G017",
            "goods_name": "测试货物I1",
            "goods_type": "普通",
            "weight": 11.0,
            "volume": 0.6,
            "order_code": "O009",
            "node_code": "SC002",
        },
        {
            "goods_code": "G018",
            "goods_name": "测试货物I2",
            "goods_type": "普通",
            "weight": 8.0,
            "volume": 0.4,
            "order_code": "O009",
            "node_code": "SC002",
        },
    ]
    
    goods_objects = {}
    for gd in goods_data:
        goods = Goods(
            goods_code=gd["goods_code"],
            goods_name=gd["goods_name"],
            goods_type=gd["goods_type"],
            weight=gd["weight"],
            volume=gd["volume"],
            node_id=test_nodes[gd["node_code"]].id,
            order_id=test_orders[gd["order_code"]].id,
            status="pending_pack",
        )
        db_session.add(goods)
        goods_objects[gd["goods_code"]] = goods
    
    db_session.commit()
    # 刷新 orders 以便访问 .goods 关系
    for order in test_orders.values():
        db_session.refresh(order)
    return goods_objects


@pytest.fixture(scope="function")
def test_vehicles(db_session, test_nodes):
    """
    创建测试车辆数据：
    - VEH001: 归属于SC001，status='idle'
    - VEH002: 归属于SC001，status='idle'
    - VEH003: 归属于SO001，status='idle'
    - VEH004: 归属于SC002，status='idle' (新增，修复SC002没有车辆的问题)
    """
    vehicles_data = [
        {
            "vehicle_code": "VEH001",
            "model": "测试车型A",
            "capacity": 100.0,
            "energy_type": "fuel",
            "node_code": "SC001",
            "last_arrived_node_code": "SC001",
        },
        {
            "vehicle_code": "VEH002",
            "model": "测试车型B",
            "capacity": 200.0,
            "energy_type": "electric",
            "node_code": "SC001",
            "last_arrived_node_code": "SC001",
        },
        {
            "vehicle_code": "VEH003",
            "model": "测试车型C",
            "capacity": 150.0,
            "energy_type": "fuel",
            "node_code": "SO001",
            "last_arrived_node_code": "SO001",
        },
        {
            "vehicle_code": "VEH004",
            "model": "测试车型D",
            "capacity": 120.0,
            "energy_type": "fuel",
            "node_code": "SC002",
            "last_arrived_node_code": "SC002",
        },
        {
            "vehicle_code": "VEH005",
            "model": "测试车型E",
            "capacity": 130.0,
            "energy_type": "electric",
            "node_code": "SO002",
            "last_arrived_node_code": "SO002",
        },
    ]

    vehicle_objects = {}
    for vd in vehicles_data:
        vehicle = Vehicle(
            vehicle_code=vd["vehicle_code"],
            model=vd["model"],
            capacity=vd["capacity"],
            energy_type=vd["energy_type"],
            node_id=test_nodes[vd["node_code"]].id,
            last_arrived_node_id=test_nodes[vd["last_arrived_node_code"]].id,
            status="idle",
        )
        db_session.add(vehicle)
        vehicle_objects[vd["vehicle_code"]] = vehicle

    db_session.commit()
    return vehicle_objects


@pytest.fixture(scope="function")
def test_drivers(db_session, test_nodes):
    """
    创建测试司机数据：
    - DRV001: 归属于SC001，status='idle'
    - DRV002: 归属于SC001，status='idle'
    - DRV003: 归属于SO001，status='idle'
    """
    drivers_data = [
        {
            "driver_code": "DRV001",
            "name": "测试司机A",
            "phone": "13800000001",
            "license_type": "C1",
            "shift": "day",
            "node_code": "SC001",
        },
        {
            "driver_code": "DRV002",
            "name": "测试司机B",
            "phone": "13800000002",
            "license_type": "C1",
            "shift": "night",
            "node_code": "SC001",
        },
        {
            "driver_code": "DRV003",
            "name": "测试司机C",
            "phone": "13800000003",
            "license_type": "C1",
            "shift": "day",
            "node_code": "SO001",
        },
    ]

    driver_objects = {}
    for dd in drivers_data:
        driver = Driver(
            driver_code=dd["driver_code"],
            name=dd["name"],
            phone=dd["phone"],
            license_type=dd["license_type"],
            shift=dd["shift"],
            node_id=test_nodes[dd["node_code"]].id,
            status="idle",
        )
        db_session.add(driver)
        driver_objects[dd["driver_code"]] = driver

    db_session.commit()
    return driver_objects


@pytest.fixture(scope="function")
def test_users(db_session):
    """
    创建测试用户数据：
    - dispatcher: 调度员角色
    - manager: 管理者角色
    """
    from config.database import settings
    from services.auth_service import get_password_hash
    
    users_data = [
        {
            "username": "dispatcher",
            "password": "123456",
            "role": "dispatcher",
            "display_name": "调度员",
        },
        {
            "username": "manager",
            "password": "123456",
            "role": "manager",
            "display_name": "管理者",
        },
    ]
    
    user_objects = {}
    for ud in users_data:
        user = User(
            username=ud["username"],
            password_hash=get_password_hash(ud["password"]),
            role=ud["role"],
            display_name=ud["display_name"],
            is_active=True,
        )
        db_session.add(user)
        user_objects[ud["username"]] = user
    
    db_session.commit()
    return user_objects


# ── 认证辅助函数 ──────────────────────────────────────────────

def create_jwt_token(username, role):
    """生成 JWT Token"""
    from config.database import settings
    import jwt
    from datetime import datetime, timedelta, timezone
    
    return jwt.encode(
        {
            "sub": username,
            "role": role,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
        settings.JWT_SECRET,
        algorithm="HS256",
    )


@pytest.fixture(scope="function")
def dispatcher_token():
    """生成 dispatcher 角色的 JWT Token"""
    return create_jwt_token("dispatcher", "dispatcher")


@pytest.fixture(scope="function")
def manager_token():
    """生成 manager 角色的 JWT Token"""
    return create_jwt_token("manager", "manager")


@pytest.fixture(autouse=True)
def reset_login_rate_limiter_between_tests():
    from core.login_rate_limit import reset_login_rate_limiter

    reset_login_rate_limiter()
    yield
    reset_login_rate_limiter()
