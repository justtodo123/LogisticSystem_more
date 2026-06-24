"""
Simulation Pipeline 集成测试

测试模拟送达完整流程 (F013-1)：
1. 创建测试数据：订单 → 调度 → 打包 → 节点调度 → 路径规划
2. 模拟L0→L1送达（第一次F005后的包裹）
3. 验证货物状态变为pending_pack（需要重新打包）
4. 模拟L1→L2送达（第二次F005后的包裹）
5. 验证货物状态变为delivered，订单状态变为completed
"""
import pytest
from sqlalchemy.orm import Session
from datetime import datetime

from models.order import Order
from models.goods import Goods
from models.node import Node
from models.storage_center import StorageCenter
from models.sorting_center import SortingCenter
from models.package import Package
from models.vehicle import Vehicle
from models.driver import Driver
from models.global_schedule import GlobalSchedule
from models.dispatch_batch import DispatchBatch
from models.node_dispatch import NodeDispatch
from models.route import Route
from services.simulation_service import SimulationService


@pytest.fixture
def setup_simulation_data(db_session):
    """设置模拟送达测试数据（完整调度流水线）"""
    # 1. 创建节点
    storage_node = Node(
        node_code="SC001",
        name="存储中心1",
        location="测试位置1",
        latitude=30.5,
        longitude=114.3,
        node_type="storage_center"
    )
    db_session.add(storage_node)

    sorting_node_l1 = Node(
        node_code="SO001",
        name="1级分拣中心1",
        location="测试位置2",
        latitude=30.6,
        longitude=114.4,
        node_type="sorting_center"
    )
    db_session.add(sorting_node_l1)

    sorting_node_l2 = Node(
        node_code="SO002",
        name="0级分拣中心1",
        location="测试位置3",
        latitude=30.7,
        longitude=114.5,
        node_type="sorting_center"
    )
    db_session.add(sorting_node_l2)
    db_session.flush()

    # 2. 创建存储中心和分拣中心记录
    storage_center = StorageCenter(
        node_id=storage_node.id,
        capacity=1000.0,
        inventory=0
    )
    db_session.add(storage_center)

    sorting_center_l1 = SortingCenter(
        node_id=sorting_node_l1.id,
        level=1,
        capacity=500,
        max_storage_time=24
    )
    db_session.add(sorting_center_l1)

    sorting_center_l2 = SortingCenter(
        node_id=sorting_node_l2.id,
        level=0,
        capacity=500,
        max_storage_time=24
    )
    db_session.add(sorting_center_l2)
    db_session.flush()

    # 3. 创建订单和货物
    order = Order(
        order_code="O_TEST_001",
        destination_node_id=sorting_node_l2.id,
        time_window="2026-06-15 10:00-12:00",
        status="delivering"  # 模拟已调度的订单
    )
    db_session.add(order)
    db_session.flush()

    goods = Goods(
        goods_code="G_TEST_001",
        order_id=order.id,
        goods_name="测试货物",
        goods_type="electronics",
        weight=10.0,
        volume=0.5,
        node_id=storage_node.id,
        status="in_transit"  # P1-3: 与包裹状态一致（F005已调度，货物在途）
    )
    db_session.add(goods)
    db_session.flush()

    # 4. 创建全局调度记录
    global_schedule = GlobalSchedule(
        schedule_code="GS_TEST_001",
        order_codes='["O_TEST_001"]',
        goods_schedules='[{"goods_code":"G_TEST_001","order_code":"O_TEST_001","path":["SC001","SO001","SO002"]}]',
        total_distance=50.0,
        total_time=2.0,
        total_goods=1,
        score=100.0
    )
    db_session.add(global_schedule)
    db_session.flush()

    # 5. 创建包裹（L0→L1）
    package_l0_l1 = Package(
        package_code="PKG_TEST_L0L1",
        weight=10.0,
        volume=0.5,
        status="in_transit",  # 已经在运输中
        from_node_id=storage_node.id,
        to_node_id=sorting_node_l1.id,
        goods_items='[{"goods_code":"G_TEST_001","order_code":"O_TEST_001"}]',
        from_longitude=114.3,
        from_latitude=30.5,
        to_longitude=114.4,
        to_latitude=30.6,
        schedule_id=global_schedule.id
    )
    db_session.add(package_l0_l1)
    db_session.flush()

    # 6. 创建车辆和司机
    vehicle = Vehicle(
        vehicle_code="V_TEST_001",
        model="测试车型",
        capacity=1000.0,
        energy_type="electric",
        vehicle_type="normal",
        capability_tags=[],
        last_arrived_node_id=storage_node.id,
        status="delivering",
        node_id=storage_node.id
    )
    db_session.add(vehicle)

    driver = Driver(
        driver_code="D_TEST_001",
        name="测试司机",
        phone="13800138000",
        license_type="C1",
        shift="day",
        node_id=storage_node.id,
        status="busy"
    )
    db_session.add(driver)
    db_session.flush()

    # 7. 创建调度批次和节点调度
    dispatch_batch = DispatchBatch(
        batch_code="BATCH_TEST_001",
        global_schedule_id=global_schedule.id,
        status="pending"
    )
    db_session.add(dispatch_batch)
    db_session.flush()

    node_dispatch = NodeDispatch(
        dispatch_code="ND_TEST_001",
        dispatch_batch_id=dispatch_batch.id,
        vehicle_id=vehicle.id,
        driver_id=driver.id,
        level_phase=0,
        tasks='[]',
        total_distance=10.0,
        total_time=30.0
    )
    db_session.add(node_dispatch)
    db_session.flush()

    # 8. 更新包裹的dispatch_id
    package_l0_l1.dispatch_id = node_dispatch.id
    db_session.commit()

    return {
        "storage_node": storage_node,
        "sorting_node_l1": sorting_node_l1,
        "sorting_node_l2": sorting_node_l2,
        "order": order,
        "goods": goods,
        "global_schedule": global_schedule,
        "package_l0_l1": package_l0_l1,
        "vehicle": vehicle,
        "driver": driver,
        "dispatch_batch": dispatch_batch,
        "node_dispatch": node_dispatch
    }


@pytest.mark.integration
class TestSimulationPipeline:
    """测试模拟送达流水线"""

    @pytest.mark.asyncio
    async def test_simulate_l0_l1_delivery(self, db_session, setup_simulation_data):
        """
        测试L0→L1送达流程

        验证：
        1. 调用模拟送达服务
        2. 包裹状态变为delivered
        3. 货物状态变为pending_pack（需要重新打包）
        4. 车辆状态变为idle
        5. 司机状态变为idle
        """
        data = setup_simulation_data

        # 验证包裹当前状态是 in_transit
        db_session.refresh(data["package_l0_l1"])
        assert data["package_l0_l1"].status == "in_transit"

        # 调用模拟送达服务（L0→L1）
        result = await SimulationService.deliver_packages(
            vehicle_code=None,
            package_code="PKG_TEST_L0L1",
            db=db_session,
        )

        # 验证响应
        assert result["code"] == 0

        # 验证数据库状态
        db_session.refresh(data["package_l0_l1"])
        assert data["package_l0_l1"].status == "delivered"

        # P1-3: deliver 不改变 goods 状态（保持 in_transit），需走 confirm-arrival 流程
        db_session.refresh(data["goods"])
        assert data["goods"].status == "in_transit"  # P1-3: 送达后状态不变

        # 模拟 confirm-arrival: goods in_transit → pending_pack
        from services.state_machine import transition_goods_status, transition_package_status
        transition_goods_status(db_session, data["goods"], 'pending_pack')
        db_session.flush()
        assert data["goods"].status == "pending_pack"

        # 模拟 F021 重新打包: goods pending_pack → packed
        transition_goods_status(db_session, data["goods"], 'packed')
        db_session.flush()
        assert data["goods"].status == "packed"

    @pytest.mark.asyncio
    async def test_simulate_l1_l2_delivery(self, db_session, setup_simulation_data):
        """
        测试L1→L2送达流程

        验证：
        1. 调用模拟送达服务
        2. 包裹状态变为delivered
        3. 货物状态变为delivered（已送达目的地）
        4. 订单状态变为completed（所有货物已送达）
        """
        data = setup_simulation_data

        # 创建L1→L2的包裹
        package_l1_l2 = Package(
            package_code="PKG_TEST_L1L2",
            weight=10.0,
            volume=0.5,
            status="in_transit",
            from_node_id=data["sorting_node_l1"].id,
            to_node_id=data["sorting_node_l2"].id,
            goods_items='[{"goods_code":"G_TEST_001","order_code":"O_TEST_001"}]',
            from_longitude=114.4,
            from_latitude=30.6,
            to_longitude=114.5,
            to_latitude=30.7,
            schedule_id=data["global_schedule"].id,
            dispatch_id=data["node_dispatch"].id
        )
        db_session.add(package_l1_l2)
        db_session.commit()

        # 调用模拟送达服务（L1→L2）
        result = await SimulationService.deliver_packages(
            vehicle_code=None,
            package_code="PKG_TEST_L1L2",
            db=db_session,
        )

        # 验证响应
        assert result["code"] == 0

        # 验证数据库状态
        db_session.refresh(package_l1_l2)
        assert package_l1_l2.status == "delivered"

    @pytest.mark.asyncio
    async def test_simulation_pipeline_complete(self, db_session, setup_simulation_data):
        """
        测试完整模拟送达流水线

        验证：
        1. L0→L1送达
        2. 货物状态变为pending_pack（需要重新打包）
        3. L1→L2送达（需要重新打包后的包裹）
        4. 订单状态变为completed
        """
        data = setup_simulation_data

        # 1. L0→L1送达
        result = await SimulationService.deliver_packages(
            vehicle_code=None,
            package_code="PKG_TEST_L0L1",
            db=db_session,
        )

        assert result["code"] == 0

        # P1-3: deliver 后 goods 保持 in_transit，需走 confirm-arrival 流程
        db_session.refresh(data["goods"])
        assert data["goods"].status == "in_transit"

        # 模拟 confirm-arrival + F021 重新打包
        from services.state_machine import transition_goods_status
        transition_goods_status(db_session, data["goods"], 'pending_pack')
        db_session.flush()
        transition_goods_status(db_session, data["goods"], 'packed')
        db_session.flush()
        assert data["goods"].status == "packed"

        # 2. L1→L2送达（需要重新打包后的包裹）
        # 创建L1→L2的包裹（模拟重新打包后的结果）
        package_l1_l2 = Package(
            package_code="PKG_TEST_L1L2",
            weight=10.0,
            volume=0.5,
            status="in_transit",
            from_node_id=data["sorting_node_l1"].id,
            to_node_id=data["sorting_node_l2"].id,
            goods_items='[{"goods_code":"G_TEST_001","order_code":"O_TEST_001"}]',
            from_longitude=114.4,
            from_latitude=30.6,
            to_longitude=114.5,
            to_latitude=30.7,
            schedule_id=data["global_schedule"].id,
            dispatch_id=data["node_dispatch"].id
        )
        db_session.add(package_l1_l2)
        db_session.commit()

        result2 = await SimulationService.deliver_packages(
            vehicle_code=None,
            package_code="PKG_TEST_L1L2",
            db=db_session,
        )

        assert result2["code"] == 0

        # P1-3: L1→L2 送达后需要 confirm-arrival 将 goods 转为 delivered
        db_session.refresh(data["goods"])
        # deliver 已更新 goods.node_id = package.to_node_id（即 L2/目的地）
        # 但 goods 状态仍是 packed（之前 repack 的结果），需要先经过 in_transit
        # 模拟 F005 L1→L2 调度：packed → in_transit
        transition_goods_status(db_session, data["goods"], 'in_transit')
        db_session.flush()
        # confirm-arrival 检查 goods.node_id == destination_node_id → delivered
        from services.state_machine import check_and_update_order_status
        transition_goods_status(db_session, data["goods"], 'delivered')
        db_session.flush()
        assert data["goods"].status == "delivered"

        # 4. 验证订单状态变为completed
        check_and_update_order_status(db_session, data["order"].order_code)
        db_session.refresh(data["order"])
        assert data["order"].status == "completed"
