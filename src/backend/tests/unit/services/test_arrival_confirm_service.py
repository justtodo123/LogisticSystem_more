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
        # Bug3 回归：goods 在 SC001（非目的地 SO010）→ 触发 repacking → goods_status = "packed"
        assert result["goods_status"] == "packed", \
            f"Bug3 回归: repacking 场景应返回 'packed'，实际返回 '{result['goods_status']}'"
        assert result["triggered_repacking"] is True

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
    async def test_confirm_arrival_normal_at_destination(self, db_session, test_nodes, test_orders, test_goods):
        """
        测试正常到货确认（货物已到最终目的地，不触发 repacking）—— Bug3 分支覆盖

        场景：货物 G001 当前在 SO010（恰好是 O001 目的地），
              confirm-arrival 正常确认 → goods.status = delivered
        验证：goods_status 响应字段为 "delivered"（非颠倒的 "pending_pack"）
        """
        # 1. 准备：货物 G001 已到达目的地 SO010（O001 的 destination_node）
        goods = test_goods["G001"]
        goods.status = "in_transit"
        goods.node_id = test_nodes["SO010"].id  # SO010 是 O001 的目的地

        # 1.2 创建 GlobalSchedule
        global_schedule = GlobalSchedule(
            schedule_code="GS_TEST_DEST",
            order_codes=json.dumps([]),
            total_distance=0.0,
            total_time=0.0,
            total_goods=0,
            score=0.0,
            algorithm_type="traditional",
            version=1,
            is_replan=False,
            goods_schedules=json.dumps([
                {"goods_code": "G001", "order_code": "O001",
                 "path": ["SC001", "SO001", "SO010"]}
            ]),
        )
        db_session.add(global_schedule)
        db_session.commit()

        # 1.3 创建包裹（L1→L2，到达 SO010）
        package = Package(
            package_code="PKG_TEST_DEST_001",
            from_node_id=test_nodes["SO001"].id,
            to_node_id=test_nodes["SO010"].id,
            weight=10.0,
            volume=0.5,
            status="in_transit",
            schedule_id=global_schedule.id,
            goods_items=[{"goods_code": "G001", "order_code": "O001"}],
        )
        db_session.add(package)
        db_session.commit()

        # 2. 调用 confirm_arrival
        result = ArrivalConfirmService.confirm_arrival(
            db=db_session,
            schedule_code="GS_TEST_DEST",
            package_code="PKG_TEST_DEST_001",
            is_normal=True,
        )

        # 3. 验证 goods_status = "delivered"（Bug3 回归）
        assert result["goods_status"] == "delivered", \
            f"Bug3 回归: 到目的地应返回 'delivered'，实际返回 '{result['goods_status']}'"
        assert result["triggered_repacking"] is False

        # 4. 验证数据库状态
        db_session.flush()
        db_session.refresh(package)
        assert package.status == "delivered"
        db_session.refresh(goods)
        assert goods.status == "delivered"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_confirm_arrival_exception_on_delivered_package(self, db_session, test_nodes, test_orders, test_goods):
        """
        测试异常到货确认（包裹状态为 delivered）—— Bug1 回归

        场景：包裹已 delivered，但后续发现货物异常需要标记 exception。
              confirm-arrival 异常确认 → delivered → exception
        验证：delivered → exception 转换不抛 ValueError（Bug1 修复后）
        """
        # 1. 准备：货物 G003（属于 O002）
        goods = test_goods["G003"]
        goods.status = "in_transit"
        goods.node_id = test_nodes["SC001"].id

        # 1.2 创建 GlobalSchedule
        global_schedule = GlobalSchedule(
            schedule_code="GS_TEST_DEL_EX",
            order_codes=json.dumps([]),
            total_distance=0.0,
            total_time=0.0,
            total_goods=0,
            score=0.0,
            algorithm_type="traditional",
            version=1,
            is_replan=False,
            goods_schedules=json.dumps([
                {"goods_code": "G003", "order_code": "O002",
                 "path": ["SC001", "SO001", "SO010"]}
            ]),
        )
        db_session.add(global_schedule)
        db_session.commit()

        # 1.3 创建包裹（状态为 delivered，模拟已送达但后续需标记异常）
        package = Package(
            package_code="PKG_TEST_DEL_EX",
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO001"].id,
            weight=10.0,
            volume=0.5,
            status="delivered",  # Bug1 场景：已 delivered 的包裹需要标记异常
            schedule_id=global_schedule.id,
            goods_items=[{"goods_code": "G003", "order_code": "O002"}],
        )
        db_session.add(package)
        db_session.commit()

        # 2. 调用 confirm_arrival（异常确认 on delivered 包裹）
        result = ArrivalConfirmService.confirm_arrival(
            db=db_session,
            schedule_code="GS_TEST_DEL_EX",
            package_code="PKG_TEST_DEL_EX",
            is_normal=False,
            exception_subtype="damaged",
        )

        # 3. 验证：不抛 ValueError（Bug1 回归）
        assert result["status"] == "exception"
        assert result["goods_status"] == "exception"

        # 4. 验证数据库状态
        db_session.flush()
        db_session.refresh(package)
        assert package.status == "exception", \
            f"Bug1 回归: delivered → exception 应成功，实际 {package.status}"

        db_session.refresh(goods)
        assert goods.status == "exception"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_confirm_arrival_exception_when_goods_already_delivered(self, db_session, test_nodes, test_orders, test_goods):
        """
        测试异常确认时货物已 delivered —— force=True 强制回退

        场景：L2 终点确认后，货物 goods=delivered + 订单 order=completed。
              后补标记包裹异常 → 货物和订单均需 force=True 回退为 exception。
        验证：不抛 ValueError，goods → exception（force=True），
              order → exception（force=True），exception_event 正常创建。
        """
        # 1. 准备：货物 G005（属于 O003），状态已是 delivered（模拟已到终点）
        goods = test_goods["G005"]
        goods.status = "delivered"
        goods.node_id = test_nodes["SO010"].id  # L2 终点

        # 1.1 关联订单设为 completed（模拟已完成送达）
        order = test_orders["O003"]
        order.status = "completed"

        # 1.2 创建 GlobalSchedule
        global_schedule = GlobalSchedule(
            schedule_code="GS_TEST_GD_DEL",
            order_codes=json.dumps([]),
            total_distance=0.0,
            total_time=0.0,
            total_goods=0,
            score=0.0,
            algorithm_type="traditional",
            version=1,
            is_replan=False,
            goods_schedules=json.dumps([
                {"goods_code": "G005", "order_code": "O003",
                 "path": ["SC001", "SO001", "SO010"]}
            ]),
        )
        db_session.add(global_schedule)
        db_session.commit()

        # 1.3 创建包裹（状态为 in_transit，goods 已 delivered）
        package = Package(
            package_code="PKG_TEST_GD_DEL",
            from_node_id=test_nodes["SO001"].id,
            to_node_id=test_nodes["SO010"].id,
            weight=10.0,
            volume=0.5,
            status="in_transit",
            schedule_id=global_schedule.id,
            goods_items=[{"goods_code": "G005", "order_code": "O003"}],
        )
        db_session.add(package)
        db_session.commit()

        # 2. 调用 confirm_arrival（异常确认，goods 已是 delivered，order 已是 completed）
        result = ArrivalConfirmService.confirm_arrival(
            db=db_session,
            schedule_code="GS_TEST_GD_DEL",
            package_code="PKG_TEST_GD_DEL",
            is_normal=False,
            exception_subtype="damaged",
            remark="L2 异常，货物已提前送达，需 force 回退",
        )

        # 3. 核心断言：不抛 ValueError，正常返回
        assert result["status"] == "exception", \
            f"包裹应标记为 exception，实际: {result['status']}"
        assert result["goods_status"] == "exception", \
            f"goods_status 应为 exception，实际: {result['goods_status']}"
        assert result["order_status"] == "exception", \
            f"order_status 应为 exception，实际: {result['order_status']}"

        # 4. 验证：goods → exception（force=True 强制回退）
        db_session.flush()
        db_session.refresh(goods)
        assert goods.status == "exception", \
            f"delivered goods 应 force 回退为 exception，实际: {goods.status}"

        # 5. 验证：order → exception（force=True 强制回退）
        db_session.refresh(order)
        assert order.status == "exception", \
            f"completed order 应 force 回退为 exception，实际: {order.status}"

        # 6. 验证：包裹 → exception
        db_session.refresh(package)
        assert package.status == "exception", \
            f"包裹应标记为 exception，实际: {package.status}"

        # 7. 验证：异常事件已创建
        db_session.flush()
        event = db_session.query(ExceptionEvent).filter(
            ExceptionEvent.target_code == "PKG_TEST_GD_DEL"
        ).first()
        assert event is not None, "应创建异常事件记录"
        assert event.exception_type == "package"

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
        1. 使用 fixture 货物 G007/G008（属于 O004）和 G005（属于 O003），更新为 in_transit
        2. 创建 3 个测试包裹（状态为 in_transit），各自使用不同 goods
        3. 调用 confirm_arrival_batch
        4. 验证所有包裹状态变为 delivered
        """
        # 1. 准备测试数据
        # 1.1 更新多个 fixture 货物为 in_transit
        goods_list = {
            "G005": test_goods["G005"],   # O003
            "G007": test_goods["G007"],   # O004
            "G008": test_goods["G008"],   # O004
        }
        for code, g in goods_list.items():
            g.status = "in_transit"
            g.node_id = test_nodes["SC001"].id
        db_session.commit()

        # 1.2 创建 GlobalSchedule（含所有三条 goods_schedules）
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
                {"goods_code": "G005", "order_code": "O003", "path": ["SC002", "SO001", "SO010"]},
                {"goods_code": "G007", "order_code": "O004", "path": ["SC001", "SO001", "SO010"]},
                {"goods_code": "G008", "order_code": "O004", "path": ["SC001", "SO001", "SO010"]},
            ])
        )
        db_session.add(global_schedule)
        db_session.commit()

        # 1.3 创建 3 个测试包裹（各自使用不同 goods）
        packages = []
        package_goods_map = [
            {"goods_code": "G005", "order_code": "O003"},
            {"goods_code": "G007", "order_code": "O004"},
            {"goods_code": "G008", "order_code": "O004"},
        ]
        for i, goods_item in enumerate(package_goods_map):
            package = Package(
                package_code=f"PKG_TEST_BATCH_{i}",
                from_node_id=test_nodes["SC001"].id,
                to_node_id=test_nodes["SO001"].id,
                weight=10.0,
                volume=0.5,
                status="in_transit",
                schedule_id=global_schedule.id,
                goods_items=[goods_item]
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

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_trigger_repacking_with_existing_package(self, db_session, test_nodes, test_orders, test_goods):
        """
        测试触发 F021 重新打包（复用同一订单已创建的 L1→L2 包裹）—— P1-3 分支覆盖

        场景：batch confirm 时同一订单的两个货物分别在不同包裹中到达 L1。
             第一个 _trigger_repacking 调用创建 L1→L2 包裹，
             第二个调用复用现有包裹并将新 goods 合并进去。
        验证：同订单货物最终在一个 L1→L2 包裹中，goods 均为 packed。
        """
        # 1. 准备货物 G003（属于 O002）和 G004（也属于 O002），均在 SO001 待重新打包
        goods_g003 = test_goods["G003"]  # O002
        goods_g003.status = "pending_pack"
        goods_g003.node_id = test_nodes["SO001"].id

        goods_g004 = test_goods["G004"]  # O002
        goods_g004.status = "pending_pack"
        goods_g004.node_id = test_nodes["SO001"].id

        # 1.1 创建 GlobalSchedule
        global_schedule = GlobalSchedule(
            schedule_code="GS_TEST_REPACK_MERGE",
            order_codes=json.dumps([]),
            total_distance=0.0,
            total_time=0.0,
            total_goods=0,
            score=0.0,
            algorithm_type="traditional",
            version=1,
            is_replan=False,
            goods_schedules=json.dumps([
                {"goods_code": "G003", "order_code": "O002",
                 "path": ["SC001", "SO001", "SO011"]},
                {"goods_code": "G004", "order_code": "O002",
                 "path": ["SC001", "SO001", "SO011"]},
            ]),
        )
        db_session.add(global_schedule)
        db_session.commit()

        # 2. 第一次调用 _trigger_repacking（模拟第一个包裹 confirm-arrival）
        result1 = ArrivalConfirmService._trigger_repacking(
            db=db_session,
            schedule_code="GS_TEST_REPACK_MERGE"
        )
        assert result1 is not None, "第一次调用应创建新 L1→L2 包裹"

        # 验证：包裹已创建，G003+G004 均在同一个包裹中（一次调用处理所有 pending_pack goods）
        db_session.flush()
        db_session.refresh(goods_g003)
        assert goods_g003.status == "packed"
        db_session.refresh(goods_g004)
        assert goods_g004.status == "packed"

        # 验证：仅创建了 1 个包裹（同订单合并）
        new_packages = db_session.query(Package).filter(
            Package.schedule_id == global_schedule.id,
            Package.status == "packed"
        ).all()
        assert len(new_packages) == 1, \
            f"同订单 O002 应仅生成 1 个 L1→L2 包裹，实际 {len(new_packages)} 个"
        assert new_packages[0].from_node_id == test_nodes["SO001"].id
        assert new_packages[0].to_node_id == test_nodes["SO011"].id

        # 验证 goods_items 包含两个货物
        pkg = new_packages[0]
        gi = pkg.goods_items if isinstance(pkg.goods_items, list) else json.loads(pkg.goods_items)
        goods_codes_in_pkg = {item["goods_code"] for item in gi}
        assert "G003" in goods_codes_in_pkg
        assert "G004" in goods_codes_in_pkg

        # 3. 模拟第二个包裹到站后新 goods 加入（同一订单 O002 的第三个货物）
        #    将 G003 回退为 pending_pack 模拟"第二批到达"场景
        goods_g003.status = "pending_pack"
        db_session.commit()

        result2 = ArrivalConfirmService._trigger_repacking(
            db=db_session,
            schedule_code="GS_TEST_REPACK_MERGE"
        )

        # 4. 验证：复用已有包裹（不创建新包裹）
        assert result2 is not None, "第二次调用应复用已有包裹"
        assert result2 == pkg.package_code, \
            f"应返回已有包裹 code {pkg.package_code}，实际 {result2}"

        # 验证包裹总数仍为 1（未创建新包裹）
        db_session.flush()
        all_packages = db_session.query(Package).filter(
            Package.schedule_id == global_schedule.id,
            Package.status == "packed"
        ).all()
        assert len(all_packages) == 1, "不应创建重复包裹"

        # 验证 G003 重新变为 packed
        db_session.refresh(goods_g003)
        assert goods_g003.status == "packed"


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
