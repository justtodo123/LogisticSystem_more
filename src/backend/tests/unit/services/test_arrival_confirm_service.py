"""
服务单元测试：ArrivalConfirmService（到货确认服务）

测试目标：
- ArrivalConfirmService.confirm_arrival 方法的正常流程和异常流程
- ArrivalConfirmService.confirm_arrival_batch 方法的批量确认逻辑
- ArrivalConfirmService._trigger_repacking 方法的重新打包逻辑
- ArrivalConfirmService._cascade_exception_packages 方法的级联异常逻辑
- ArrivalConfirmService.get_arrival_packages 方法的查询逻辑

测试范围：
- 正常到货确认（is_normal=True）
- 异常到货确认（is_normal=False）
- 批量到货确认（成功和失败）
- 触发 F021 重新打包
- 级联异常包裹
- 查询到站包裹
- 边界情况（包裹不存在、状态不正确、事务回滚等）
"""

import pytest
from sqlalchemy.orm import Session
import json

from services.arrival_confirm_service import ArrivalConfirmService
from models.package import Package
from models.goods import Goods
from models.order import Order
from models.global_schedule import GlobalSchedule
from models.node import Node
from models.exception_event import ExceptionEvent


class TestConfirmArrival:
    """测试单个到货确认"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_confirm_arrival_normal(self, db_session, test_nodes, test_orders, test_goods):
        """
        测试正常到货确认：
        1. 使用 fixture 货物 G001（属于 O001），更新状态为 in_transit
        2. 创建测试包裹（状态为 in_transit）
        3. 调用 confirm_arrival(is_normal=True)
        4. 验证包裹状态变为 delivered
        5. 验证货物状态更新
        """
        # 1. 准备测试数据
        # 1.1 更新 fixture 货物 G001 的状态和位置
        goods = test_goods["G001"]  # fixture 已有 G001，属于 O001
        goods.status = "in_transit"
        goods.node_id = test_nodes["SC001"].id

        # 1.2 创建 GlobalSchedule（goods_schedules 匹配 fixture 货物）
        global_schedule = GlobalSchedule(
            schedule_code="GS_TEST_001",
            order_codes=json.dumps([]),
            total_distance=0.0,
            total_time=0.0,
            total_goods=0,
            score=0.0,
            algorithm_type="traditional",
            version=1,
            is_replan=False,
            goods_schedules=json.dumps([
                {
                    "goods_code": "G001",
                    "order_code": "O001",
                    "path": ["SC001", "SO001", "SO010"]
                }
            ])
        )
        db_session.add(global_schedule)
        db_session.commit()

        # 1.3 创建测试包裹
        package = Package(
            package_code="PKG_TEST_001",
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO001"].id,
            weight=10.0,
            volume=0.5,
            status="in_transit",
            schedule_id=global_schedule.id,
            goods_items=[{"goods_code": "G001", "order_code": "O001"}]
        )
        db_session.add(package)
        db_session.commit()

        # 2. 调用 confirm_arrival
        result = ArrivalConfirmService.confirm_arrival(
            db=db_session,
            schedule_code="GS_TEST_001",
            package_code="PKG_TEST_001",
            is_normal=True
        )

        # 3. 验证结果
        assert result["package_code"] == "PKG_TEST_001"
        assert result["status"] == "delivered"
        assert "goods_status" in result

        # 4. 显式 flush 确保状态持久化，再 refresh 验证
        db_session.flush()
        db_session.refresh(package)
        assert package.status == "delivered"

        db_session.refresh(goods)
        # _trigger_repacking 已将 goods 状态更新为 packed
        assert goods.status == "packed"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_confirm_arrival_exception(self, db_session, test_nodes, test_orders, test_goods):
        """
        测试异常到货确认：
        1. 使用 fixture 货物 G003（属于 O002），更新状态为 in_transit
        2. 创建测试包裹（状态为 in_transit）
        3. 调用 confirm_arrival(is_normal=False)
        4. 验证包裹状态变为 exception
        5. 验证货物状态变为 exception
        6. 验证订单状态变为 exception
        7. 验证写入 exception_events
        """
        # 1. 准备测试数据
        # 1.1 更新 fixture 货物 G003（属于 O002）的状态和位置
        goods = test_goods["G003"]  # fixture: G003 -> O002
        goods.status = "in_transit"
        goods.node_id = test_nodes["SC001"].id

        # 1.2 创建 GlobalSchedule
        global_schedule = GlobalSchedule(
            schedule_code="GS_TEST_002",
            order_codes=json.dumps([]),
            total_distance=0.0,
            total_time=0.0,
            total_goods=0,
            score=0.0,
            algorithm_type="traditional",
            version=1,
            is_replan=False,
            goods_schedules=json.dumps([
                {
                    "goods_code": "G003",
                    "order_code": "O002",
                    "path": ["SC001", "SO001", "SO010"]
                }
            ])
        )
        db_session.add(global_schedule)
        db_session.commit()

        # 1.3 创建测试包裹
        package = Package(
            package_code="PKG_TEST_002",
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO001"].id,
            weight=10.0,
            volume=0.5,
            status="in_transit",
            schedule_id=global_schedule.id,
            goods_items=[{"goods_code": "G003", "order_code": "O002"}]
        )
        db_session.add(package)
        db_session.commit()

        # 2. 调用 confirm_arrival（异常确认）
        result = ArrivalConfirmService.confirm_arrival(
            db=db_session,
            schedule_code="GS_TEST_002",
            package_code="PKG_TEST_002",
            is_normal=False,
            exception_subtype="damaged",
            remark="测试异常到货"
        )

        # 3. 验证结果
        assert result["package_code"] == "PKG_TEST_002"
        assert result["status"] == "exception"
        assert result["goods_status"] == "exception"
        assert result["order_status"] == "exception"

        # 4. 显式 flush + refresh 验证数据库状态
        db_session.flush()
        db_session.refresh(package)
        assert package.status == "exception"

        db_session.refresh(goods)
        assert goods.status == "exception"

        # 5. 验证订单状态
        db_session.refresh(test_orders["O002"])
        assert test_orders["O002"].status == "exception"

        # 6. 验证 exception_events（写入审计日志）
        exception_event = db_session.query(ExceptionEvent).filter(
            ExceptionEvent.target_code == "PKG_TEST_002"
        ).first()
        assert exception_event is not None
        assert exception_event.exception_type == "package"
        assert exception_event.exception_subtype == "damaged"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_confirm_arrival_package_not_found(self, db_session):
        """
        测试包裹不存在（边界情况）
        """
        with pytest.raises(Exception) as exc_info:
            ArrivalConfirmService.confirm_arrival(
                db=db_session,
                schedule_code="GS_TEST_001",
                package_code="PKG_NOT_EXIST",
                is_normal=True
            )

        assert "包裹 PKG_NOT_EXIST 不存在" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_confirm_arrival_invalid_status(self, db_session, test_nodes):
        """
        测试包裹状态不正确（边界情况）：
        - confirm_arrival_batch 预校验时拒绝非 in_transit/delivered 状态的包裹
        """
        # 1. 创建 GlobalSchedule
        global_schedule = GlobalSchedule(
            schedule_code="GS_TEST_INVALID",
            order_codes=json.dumps([]),
            total_distance=0.0,
            total_time=0.0,
            total_goods=0,
            score=0.0,
            algorithm_type="traditional",
            version=1,
            is_replan=False,
            goods_schedules=json.dumps([])
        )
        db_session.add(global_schedule)
        db_session.commit()

        # 2. 创建包裹（状态为 "packed"，不在允许列表中）
        package = Package(
            package_code="PKG_TEST_INVALID_STATUS",
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO001"].id,
            weight=10.0,
            volume=0.5,
            status="packed",  # 状态不正确（允许的是 in_transit 或 delivered）
            schedule_id=global_schedule.id,
            goods_items=[]
        )
        db_session.add(package)
        db_session.commit()

        # 3. 通过 confirm_arrival_batch 触发状态校验（confirm_arrival 不做状态校验）
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            ArrivalConfirmService.confirm_arrival_batch(
                db=db_session,
                schedule_code="GS_TEST_INVALID",
                confirmations=[
                    {"package_code": "PKG_TEST_INVALID_STATUS", "is_normal": True}
                ]
            )

        assert exc_info.value.status_code == 400
        assert "状态不正确" in exc_info.value.detail


class TestConfirmArrivalBatch:
    """测试批量到货确认"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_confirm_arrival_batch_success(self, db_session, test_nodes, test_orders, test_goods):
        """
        测试批量确认成功：
        1. 使用 fixture 货物 G007（属于 O004），更新为 in_transit
        2. 创建多个测试包裹（状态为 in_transit）
        3. 调用 confirm_arrival_batch
        4. 验证所有包裹状态变为 delivered
        """
        # 1. 准备测试数据
        # 1.1 更新 fixture 货物
        goods = test_goods["G007"]  # G007 -> O004
        goods.status = "in_transit"
        goods.node_id = test_nodes["SC001"].id
        db_session.commit()

        # 1.2 创建 GlobalSchedule
        global_schedule = GlobalSchedule(
            schedule_code="GS_TEST_BATCH_OK",
            order_codes=json.dumps([]),
            total_distance=0.0,
            total_time=0.0,
            total_goods=0,
            score=0.0,
            algorithm_type="traditional",
            version=1,
            is_replan=False,
            goods_schedules=json.dumps([
                {"goods_code": "G007", "order_code": "O004", "path": ["SC001", "SO001", "SO010"]}
            ])
        )
        db_session.add(global_schedule)
        db_session.commit()

        # 1.3 创建多个测试包裹
        packages = []
        for i in range(3):
            package = Package(
                package_code=f"PKG_TEST_BATCH_{i}",
                from_node_id=test_nodes["SC001"].id,
                to_node_id=test_nodes["SO001"].id,
                weight=10.0,
                volume=0.5,
                status="in_transit",
                schedule_id=global_schedule.id,
                goods_items=[{"goods_code": "G007", "order_code": "O004"}]
            )
            db_session.add(package)
            packages.append(package)
        db_session.commit()

        # 2. 调用 confirm_arrival_batch
        confirmations = [
            {"package_code": "PKG_TEST_BATCH_0", "is_normal": True},
            {"package_code": "PKG_TEST_BATCH_1", "is_normal": True},
            {"package_code": "PKG_TEST_BATCH_2", "is_normal": True}
        ]

        result = ArrivalConfirmService.confirm_arrival_batch(
            db=db_session,
            schedule_code="GS_TEST_BATCH_OK",
            confirmations=confirmations
        )

        # 3. 验证结果
        assert result["total"] == 3
        assert result["success_count"] == 3
        assert result["failed_count"] == 0

        # 4. 显式 flush + refresh 确保状态已持久化
        db_session.flush()
        for pkg in packages:
            db_session.refresh(pkg)
            assert pkg.status == "delivered", f"Expected delivered, got {pkg.status}"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_confirm_arrival_batch_failure(self, db_session, test_nodes):
        """
        测试批量确认失败（预校验拦截）：
        - 创建包裹（状态为 "packed"，不在允许的 in_transit/delivered 列表中）
        - 预校验阶段抛出 HTTPException(400)
        """
        # 1. 创建 GlobalSchedule
        global_schedule = GlobalSchedule(
            schedule_code="GS_TEST_BATCH_FAIL",
            order_codes=json.dumps([]),
            total_distance=0.0,
            total_time=0.0,
            total_goods=0,
            score=0.0,
            algorithm_type="traditional",
            version=1,
            is_replan=False,
            goods_schedules=json.dumps([])
        )
        db_session.add(global_schedule)
        db_session.commit()

        # 2. 创建包裹（状态为 "packed"，预校验会拒绝）
        package1 = Package(
            package_code="PKG_TEST_BATCH_FAIL_OK",
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO001"].id,
            weight=10.0,
            volume=0.5,
            status="in_transit",
            schedule_id=global_schedule.id,
            goods_items=[]
        )
        db_session.add(package1)

        package2 = Package(
            package_code="PKG_TEST_BATCH_FAIL_BAD",
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO001"].id,
            weight=10.0,
            volume=0.5,
            status="packed",  # 不允许的状态 → 预校验失败
            schedule_id=global_schedule.id,
            goods_items=[]
        )
        db_session.add(package2)
        db_session.commit()

        # 3. 调用 confirm_arrival_batch，预校验应抛出 HTTPException
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            ArrivalConfirmService.confirm_arrival_batch(
                db=db_session,
                schedule_code="GS_TEST_BATCH_FAIL",
                confirmations=[
                    {"package_code": "PKG_TEST_BATCH_FAIL_OK", "is_normal": True},
                    {"package_code": "PKG_TEST_BATCH_FAIL_BAD", "is_normal": True}
                ]
            )

        assert exc_info.value.status_code == 400
        assert "状态不正确" in exc_info.value.detail


class TestTriggerRepacking:
    """测试 F021 重新打包触发"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_trigger_repacking(self, db_session, test_nodes, test_orders, test_goods):
        """
        测试触发 F021 重新打包：
        1. 使用 fixture 货物 G003（属于 O002），更新为 pending_pack + 位置 SO001
        2. 创建 GlobalSchedule（goods_schedules 中 path=["SC001","SO001","SO011"]）
        3. 调用 _trigger_repacking → 生成新包裹 SO001→SO011
        """
        # 1. 更新 fixture 货物 G003 的状态和位置
        goods = test_goods["G003"]  # fixture: G003 -> O002, node=SC001
        goods.status = "pending_pack"
        goods.node_id = test_nodes["SO001"].id  # 当前在 SO001

        # 1.1 创建 GlobalSchedule
        global_schedule = GlobalSchedule(
            schedule_code="GS_TEST_REPACK",
            order_codes=json.dumps([]),
            total_distance=0.0,
            total_time=0.0,
            total_goods=0,
            score=0.0,
            algorithm_type="traditional",
            version=1,
            is_replan=False,
            goods_schedules=[
                {"goods_code": "G003", "order_code": "O002",
                 "path": ["SC001", "SO001", "SO011"]}
            ]
        )
        db_session.add(global_schedule)
        db_session.commit()

        # 2. 调用 _trigger_repacking
        new_package_code = ArrivalConfirmService._trigger_repacking(
            db=db_session,
            schedule_code="GS_TEST_REPACK"
        )
        assert new_package_code is not None, "_trigger_repacking should return a package code"

        # 3. flush 确保新包裹落库，然后查询验证
        db_session.flush()
        new_package = db_session.query(Package).filter(
            Package.package_code == new_package_code
        ).first()
        assert new_package is not None, "New package should be queryable after flush"
        assert new_package.status == "packed"
        assert new_package.from_node_id == test_nodes["SO001"].id
        assert new_package.to_node_id == test_nodes["SO011"].id

        # 4. 验证货物状态更新
        db_session.refresh(goods)
        assert goods.status == "packed"


class TestCascadeExceptionPackages:
    """测试级联异常包裹"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cascade_exception_packages(self, db_session, test_nodes, test_goods):
        """
        测试级联异常包裹：
        1. 使用 fixture 货物 G004（属于 O002）
        2. 创建异常包裹（SO001）+ 下游包裹（SO010, SO011）+ 无关包裹
        3. 调用 _cascade_exception_packages
        4. 验证下游包裹被标记为 exception，无关包裹保持 in_transit
        """
        # 1. 创建 GlobalSchedule
        global_schedule = GlobalSchedule(
            schedule_code="GS_TEST_CASCADE",
            order_codes=json.dumps([]),
            total_distance=0.0,
            total_time=0.0,
            total_goods=0,
            score=0.0,
            algorithm_type="traditional",
            version=1,
            is_replan=False,
            goods_schedules=json.dumps([
                {
                    "goods_code": "G004",
                    "order_code": "O002",
                    "path": ["SC001", "SO001", "SO010", "SO011"]  # 多节点路径
                }
            ])
        )
        db_session.add(global_schedule)
        db_session.commit()

        # 2. 创建异常包裹（在 SO001 异常）
        exception_package = Package(
            package_code="PKG_TEST_EXCEPTION",
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO001"].id,
            weight=10.0,
            volume=0.5,
            status="exception",
            schedule_id=global_schedule.id,
            goods_items=[{"goods_code": "G004", "order_code": "O002"}]
        )
        db_session.add(exception_package)

        # 3. 创建下游包裹（SO001 → SO010）
        downstream_package1 = Package(
            package_code="PKG_TEST_DOWNSTREAM_1",
            from_node_id=test_nodes["SO001"].id,
            to_node_id=test_nodes["SO010"].id,
            weight=10.0,
            volume=0.5,
            status="in_transit",
            schedule_id=global_schedule.id,
            goods_items=[{"goods_code": "G004", "order_code": "O002"}]
        )
        db_session.add(downstream_package1)

        # 4. 创建下游包裹（SO010 → SO011）
        downstream_package2 = Package(
            package_code="PKG_TEST_DOWNSTREAM_2",
            from_node_id=test_nodes["SO010"].id,
            to_node_id=test_nodes["SO011"].id,
            weight=10.0,
            volume=0.5,
            status="in_transit",
            schedule_id=global_schedule.id,
            goods_items=[{"goods_code": "G004", "order_code": "O002"}]
        )
        db_session.add(downstream_package2)

        # 5. 创建无关包裹（不同货物 G005 → 不应被级联）
        unrelated_package = Package(
            package_code="PKG_TEST_UNRELATED",
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO001"].id,
            weight=10.0,
            volume=0.5,
            status="in_transit",
            schedule_id=global_schedule.id,
            goods_items=[{"goods_code": "G005", "order_code": "O003"}]
        )
        db_session.add(unrelated_package)
        db_session.commit()

        # 6. 调用 _cascade_exception_packages
        ArrivalConfirmService._cascade_exception_packages(
            db=db_session,
            schedule_code="GS_TEST_CASCADE",
            package_code="PKG_TEST_EXCEPTION"
        )

        # 7. 显式 flush 确保状态持久化
        db_session.flush()

        # 8. 验证：下游包裹应被标记为 exception
        db_session.refresh(downstream_package1)
        assert downstream_package1.status == "exception", \
            f"Expected exception, got {downstream_package1.status}"

        db_session.refresh(downstream_package2)
        assert downstream_package2.status == "exception", \
            f"Expected exception, got {downstream_package2.status}"

        # 9. 验证：无关包裹保持 in_transit
        db_session.refresh(unrelated_package)
        assert unrelated_package.status == "in_transit"


class TestGetArrivalPackages:
    """测试查询到站包裹"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_arrival_packages(self, db_session, test_nodes):
        """
        测试查询到站包裹：
        1. 创建测试包裹（状态为 in_transit 和 delivered）
        2. 调用 get_arrival_packages
        3. 验证返回正确的包裹列表
        """
        # 1. 创建测试数据
        # 1.1 创建 GlobalSchedule
        global_schedule = GlobalSchedule(
            schedule_code="GS_TEST_007",
            order_codes=json.dumps([]),
            total_distance=0.0,
            total_time=0.0,
            total_goods=0,
            score=0.0,
            algorithm_type="traditional",
            version=1,
            is_replan=False,
            goods_schedules=json.dumps([])
        )
        db_session.add(global_schedule)
        db_session.commit()

        # 1.2 创建测试包裹（状态为 in_transit）
        package1 = Package(
            package_code="PKG_TEST_ARRIVAL_1",
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO001"].id,
            weight=10.0,
            volume=0.5,
            status="in_transit",
            schedule_id=global_schedule.id,
            goods_items=[]
        )
        db_session.add(package1)

        # 1.3 创建测试包裹（状态为 delivered）
        package2 = Package(
            package_code="PKG_TEST_ARRIVAL_2",
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO001"].id,
            weight=10.0,
            volume=0.5,
            status="delivered",
            schedule_id=global_schedule.id,
            goods_items=[]
        )
        db_session.add(package2)

        # 1.4 创建测试包裹（状态为 packed，不应该被查询到）
        package3 = Package(
            package_code="PKG_TEST_ARRIVAL_3",
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO001"].id,
            weight=10.0,
            volume=0.5,
            status="packed",
            schedule_id=global_schedule.id,
            goods_items=[]
        )
        db_session.add(package3)
        db_session.commit()

        # 2. 调用 get_arrival_packages
        result = ArrivalConfirmService.get_arrival_packages(
            db=db_session,
            schedule_code="GS_TEST_007"
        )

        # 3. 验证结果
        assert len(result) == 2  # 只应该返回 in_transit 和 delivered 的包裹

        package_codes = [pkg["package_code"] for pkg in result]
        assert "PKG_TEST_ARRIVAL_1" in package_codes
        assert "PKG_TEST_ARRIVAL_2" in package_codes
        assert "PKG_TEST_ARRIVAL_3" not in package_codes
