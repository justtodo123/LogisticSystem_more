"""
服务单元测试：ExceptionService + ReplanService（异常与重规划）

测试目标：
- ExceptionService CRUD 操作（创建、查询、解决）
- ReplanService 重规划逻辑（redispatch / reroute）
- 版本链管理验证

阶段7单元测试（方案A：不修改现有服务层）。
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from fastapi import HTTPException

from models.exception_event import ExceptionEvent
from models.global_schedule import GlobalSchedule
from models.route import Route
from models.node_dispatch import NodeDispatch
from models.dispatch_batch import DispatchBatch
from models.vehicle import Vehicle
from models.driver import Driver
from models.node import Node
from services.exception_service import ExceptionService
from services.replan_service import ReplanService
from schemas.exception_event import CreateExceptionEventRequest
from utils.response import success_response, error_response


class TestExceptionServiceCRUD:
    """异常事件 CRUD 测试"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_exception_event_success(self, db_session, test_nodes):
        """创建异常事件成功"""
        # 使用 test_nodes fixture 中真实存在的节点编码
        node_code = list(test_nodes.keys())[0]
        data = CreateExceptionEventRequest(
            exception_type="node",
            exception_subtype="capacity_limit",
            target_type="node",
            target_code=node_code,
            recommended_action="redispatch",
            description="存储中心容量不足",
        )

        result = await ExceptionService.create_exception_event(
            db=db_session,
            data=data,
        )

        assert result["code"] == 0
        assert result["message"] == "success"
        assert result["data"]["event_code"].startswith("EX")
        assert result["data"]["exception_type"] == "node"
        assert result["data"]["exception_subtype"] == "capacity_limit"
        assert result["data"]["recommended_action"] == "redispatch"
        assert result["data"]["status"] == "open"
        assert result["data"]["description"] == "存储中心容量不足"

        # 验证数据库写入
        event = db_session.query(ExceptionEvent).filter(
            ExceptionEvent.event_code == result["data"]["event_code"]
        ).first()
        assert event is not None
        assert event.status == "open"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_exception_event_invalid_schedule(self, db_session):
        """创建异常事件失败：无效的 related_schedule_code"""
        data = CreateExceptionEventRequest(
            exception_type="node",
            recommended_action="redispatch",
            description="测试",
            related_schedule_code="GS_NONEXISTENT",
        )

        result = await ExceptionService.create_exception_event(
            db=db_session,
            data=data,
        )

        assert result["code"] == 40401
        assert "不存在" in result["message"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_exception_event_with_schedule(self, db_session, test_nodes):
        """创建关联调度方案的异常事件成功（需 mock 调度方案）"""
        # 先创建一个 GlobalSchedule
        from models.global_schedule import GlobalSchedule
        gs = GlobalSchedule(
            schedule_code="GS_TEST_001",
            order_codes=["O001"],
            goods_schedules=[],
            total_distance=100.0,
            total_time=5.0,
            total_goods=2,
            score=0.5,
            version=1,
            is_replan=False,
        )
        db_session.add(gs)
        db_session.commit()

        # 使用 test_nodes 中真实存在的节点编码
        node_code = list(test_nodes.keys())[0]
        data = CreateExceptionEventRequest(
            exception_type="road",
            exception_subtype="congestion",
            recommended_action="redispatch",
            target_type="node",
            target_code=node_code,
            description="道路拥堵",
            related_schedule_code="GS_TEST_001",
        )

        result = await ExceptionService.create_exception_event(
            db=db_session,
            data=data,
        )

        assert result["code"] == 0
        assert result["data"]["related_schedule_code"] == "GS_TEST_001"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_exception_events_list(self, db_session):
        """查询异常事件列表（分页、筛选）"""
        # 创建多个异常事件
        for i in range(3):
            event = ExceptionEvent(
                event_code=f"EX_TEST_{i}",
                exception_type="road" if i < 2 else "package",
                exception_subtype="congestion",
                recommended_action="reroute",
                description=f"测试异常 {i}",
                status="open" if i < 2 else "resolved",
            )
            db_session.add(event)
        db_session.commit()

        # 查询全部
        result = await ExceptionService.get_exception_events(
            db=db_session,
            page=1,
            page_size=10,
        )
        assert result["code"] == 0
        assert result["data"]["total"] == 3
        assert len(result["data"]["items"]) == 3

        # 按 status 筛选
        result = await ExceptionService.get_exception_events(
            db=db_session,
            status="open",
        )
        assert result["data"]["total"] == 2

        # 按 exception_type 筛选
        result = await ExceptionService.get_exception_events(
            db=db_session,
            exception_type="package",
        )
        assert result["data"]["total"] == 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_exception_event_detail(self, db_session):
        """查询异常事件详情"""
        event = ExceptionEvent(
            event_code="EX_DETAIL_001",
            exception_type="node",
            exception_subtype="capacity_limit",
            recommended_action="redispatch",
            description="节点异常",
            status="open",
        )
        db_session.add(event)
        db_session.commit()

        result = await ExceptionService.get_exception_event_by_code(
            db=db_session,
            event_code="EX_DETAIL_001",
        )
        assert result["code"] == 0
        assert result["data"]["event_code"] == "EX_DETAIL_001"
        assert result["data"]["description"] == "节点异常"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_exception_event_not_found(self, db_session):
        """查询不存在的异常事件"""
        result = await ExceptionService.get_exception_event_by_code(
            db=db_session,
            event_code="EX_NONEXISTENT",
        )
        assert result["code"] == 40401

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_resolve_exception_success(self, db_session):
        """标记异常已解决成功"""
        event = ExceptionEvent(
            event_code="EX_RESOLVE_001",
            exception_type="node",
            exception_subtype="capacity_limit",
            recommended_action="redispatch",
            description="待解决异常",
            status="open",
        )
        db_session.add(event)
        db_session.commit()

        result = await ExceptionService.resolve_exception(
            db=db_session,
            event_code="EX_RESOLVE_001",
        )
        assert result["code"] == 0
        assert result["data"]["status"] == "resolved"
        assert result["data"]["resolved_at"] is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_resolve_exception_already_resolved(self, db_session):
        """标记已解决的异常应失败"""
        event = ExceptionEvent(
            event_code="EX_RESOLVED_001",
            exception_type="node",
            exception_subtype="capacity_limit",
            recommended_action="redispatch",
            description="已解决异常",
            status="resolved",
        )
        db_session.add(event)
        db_session.commit()

        result = await ExceptionService.resolve_exception(
            db=db_session,
            event_code="EX_RESOLVED_001",
        )
        assert result["code"] == 40001
        assert "已解决" in result["message"]


class TestReplanService:
    """重规划服务测试（方案A）"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_redispatch_original_schedule_not_found(self, db_session):
        """重调度失败：原调度方案不存在"""
        result = await ReplanService.redispatch(
            db=db_session,
            original_schedule_code="GS_NONEXISTENT",
            replan_reason="测试重调度",
        )
        assert result["code"] == 40401
        assert "不存在" in result["message"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_redispatch_success(self, db_session, test_nodes, test_orders, test_goods, test_vehicles, test_drivers):
        """重调度成功：验证版本链更新"""
        # 1. 创建原调度方案
        original = GlobalSchedule(
            schedule_code="GS_ORIG_001",
            order_codes=list(test_orders.keys())[:3],
            goods_schedules=[],
            total_distance=300.0,
            total_time=15.0,
            total_goods=6,
            score=0.5,
            algorithm_type="traditional",
            version=1,
            is_replan=False,
        )
        db_session.add(original)
        # AI-replan 分支（无 event）：将订单/货物设为 AI 重规划可识别的状态
        # 留 goods 为 pending_pack，避免 synchronize_session=False 导致的会话缓存问题
        for order_code in original.order_codes:
            order = test_orders.get(order_code)
            if order:
                order.status = "in_transit"
        db_session.commit()

        # 2. 调用 redispatch（将触发 ScheduleService + DispatchService）
        result = await ReplanService.redispatch(
            db=db_session,
            original_schedule_code="GS_ORIG_001",
            replan_reason="节点容量异常触发重调度",
        )

        assert result["code"] == 0
        assert result["data"]["is_replan"] is True
        assert result["data"]["replan_reason"] == "节点容量异常触发重调度"
        assert result["data"]["original_schedule_code"] == "GS_ORIG_001"

        new_schedule_code = result["data"]["schedule_code"]
        assert new_schedule_code != "GS_ORIG_001"
        assert new_schedule_code.startswith("GS")

        # 3. 验证版本链
        new_schedule = db_session.query(GlobalSchedule).filter(
            GlobalSchedule.schedule_code == new_schedule_code
        ).first()
        assert new_schedule is not None
        assert new_schedule.version == 2  # original.version + 1
        assert new_schedule.parent_id == original.id
        assert new_schedule.is_replan is True
        assert new_schedule.replan_reason == "节点容量异常触发重调度"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reroute_original_route_not_found(self, db_session):
        """重路径规划失败：原路径不存在"""
        result = await ReplanService.reroute(
            db=db_session,
            original_route_code="RT_NONEXISTENT",
            replan_reason="测试重路径规划",
        )
        assert result["code"] == 40401
        assert "不存在" in result["message"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reroute_success(self, db_session, test_nodes):
        """重路径规划成功：验证版本链更新"""
        # 需要完整的 Route → NodeDispatch → DispatchBatch 链条
        # 创建必要的测试数据
        import json

        # 创建 vehicle 和 driver
        node_0 = list(test_nodes.values())[0]
        vehicle = Vehicle(
            vehicle_code="V_TEST_001",
            model="测试货车",
            vehicle_type="normal",
            energy_type="fuel",
            status="idle",
            capacity=5000.0,
            node_id=node_0.id,
            last_arrived_node_id=node_0.id,
        )
        driver = Driver(
            driver_code="D_TEST_001",
            name="测试司机",
            phone="13800001111",
            license_type="B2",
            shift="早班",
            status="idle",
            node_id=node_0.id,
        )
        db_session.add_all([vehicle, driver])

        # 创建 GlobalSchedule（不涉及版本链的前置条件）
        gs = GlobalSchedule(
            schedule_code="GS_REROUTE_001",
            order_codes=["O001"],
            goods_schedules=[],
            total_distance=100.0,
            total_time=5.0,
            total_goods=2,
            score=0.5,
            version=1,
            is_replan=False,
        )
        db_session.add(gs)
        db_session.flush()

        # 创建 DispatchBatch
        batch = DispatchBatch(
            batch_code="DB_REROUTE_001",
            global_schedule_id=gs.id,
            status="completed",
            l0_l1_dispatch_count=1,
            l1_l2_dispatch_count=0,
        )
        db_session.add(batch)
        db_session.flush()

        # 创建 NodeDispatch
        nd = NodeDispatch(
            dispatch_code="ND_REROUTE_001",
            dispatch_batch_id=batch.id,
            vehicle_id=vehicle.id,
            driver_id=driver.id,
            level_phase=0,
            tasks=json.dumps([]),
            total_distance=50.0,
            total_time=2.0,
        )
        db_session.add(nd)
        db_session.flush()

        # 创建原 Route（version=1）
        original_route = Route(
            route_code="RT_ORIG_001",
            dispatch_id=nd.id,
            vehicle_id=vehicle.id,
            route_segments=json.dumps([
                {"road_name": "虚拟大道", "start_lng": 114.30, "start_lat": 30.52,
                 "end_lng": 114.31, "end_lat": 30.53}
            ]),
            total_distance=50.0,
            total_time=2.0,
            total_emission=10.0,
            algorithm_type="traditional",
            version=1,
            is_replan=False,
        )
        db_session.add(original_route)
        db_session.commit()

        # Mock RouteService.create_route_planning（避免复杂的算法调用）
        # 注意：RouteService 在 replan_service.py 中通过局部导入，需 mock 原始模块
        with patch(
            "services.route_service.RouteService.create_route_planning",
            new_callable=AsyncMock,
        ) as mock_rp:
            mock_rp.return_value = success_response(data={
                "batch_code": "DB_REROUTE_001",
                "status": "completed",
                "routes": [{
                    "route_code": "RT_REPLAN_001",
                    "dispatch_code": "ND_REROUTE_001",
                    "vehicle_code": "V_TEST_001",
                    "route_segments": [],
                    "total_distance": 55.0,
                    "total_time": 2.2,
                    "total_emission": 11.0,
                    "algorithm_type": "traditional",
                }]
            })

            # 需要在 mock 返回前预先创建 route 对象到数据库
            # mock 调用后不会真正创建 Route 记录，所以模拟版本链更新
            result = await ReplanService.reroute(
                db=db_session,
                original_route_code="RT_ORIG_001",
                replan_reason="道路拥堵触发重路径规划",
            )

        assert result["code"] == 0
        assert result["data"]["is_replan"] is True
        assert result["data"]["replan_reason"] == "道路拥堵触发重路径规划"
        assert result["data"]["original_route_code"] == "RT_ORIG_001"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reroute_no_dispatches(self, db_session, test_nodes):
        """重路径规划失败：Route 关联的 dispatch 不存在"""
        # 创建没有有效 dispatch 的 Route
        import json
        node_0 = list(test_nodes.values())[0]
        vehicle = Vehicle(
            vehicle_code="V_NO_DISP_001",
            model="测试货车",
            vehicle_type="normal",
            energy_type="fuel",
            status="idle",
            capacity=5000.0,
            node_id=node_0.id if node_0 else 1,
            last_arrived_node_id=node_0.id if node_0 else 1,
        )
        db_session.add(vehicle)
        db_session.commit()

        route = Route(
            route_code="RT_NO_DISP_001",
            dispatch_id=99999,  # 不存在的 dispatch_id
            vehicle_id=vehicle.id,
            route_segments=json.dumps([]),
            total_distance=10.0,
            total_time=1.0,
            total_emission=2.0,
            version=1,
            is_replan=False,
        )
        db_session.add(route)
        db_session.commit()

        result = await ReplanService.reroute(
            db=db_session,
            original_route_code="RT_NO_DISP_001",
            replan_reason="测试",
        )
        assert result["code"] == 40001
        assert "调度明细不存在" in result["message"]


class TestExceptionTriggerReplan:
    """ExceptionService.trigger_replan 集成测试"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_trigger_replan_event_not_found(self, db_session):
        """触发重规划失败：异常事件不存在"""
        result = await ExceptionService.trigger_replan(
            db=db_session,
            event_code="EX_NONEXISTENT",
            action="reroute",
            replan_reason="测试",
        )
        assert result["code"] == 40401

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_trigger_replan_already_resolved(self, db_session):
        """触发重规划失败：异常事件已解决"""
        event = ExceptionEvent(
            event_code="EX_RESOLVED_001",
            exception_type="node",
            exception_subtype="capacity_limit",
            recommended_action="redispatch",
            description="已解决",
            status="resolved",
        )
        db_session.add(event)
        db_session.commit()

        result = await ExceptionService.trigger_replan(
            db=db_session,
            event_code="EX_RESOLVED_001",
            action="redispatch",
            replan_reason="测试",
        )
        assert result["code"] == 40001
        assert "已解决" in result["message"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_trigger_replan_redispatch_no_schedule(self, db_session):
        """触发重规划失败：redispatch 但无 related_schedule_code"""
        event = ExceptionEvent(
            event_code="EX_NO_SCH_001",
            exception_type="node",
            exception_subtype="capacity_limit",
            recommended_action="redispatch",
            description="无关联调度方案",
            status="open",
        )
        db_session.add(event)
        db_session.commit()

        result = await ExceptionService.trigger_replan(
            db=db_session,
            event_code="EX_NO_SCH_001",
            action="redispatch",
            replan_reason="测试",
        )
        assert result["code"] == 40001
        assert "关联调度方案" in result["message"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_trigger_replan_unsupported_action(self, db_session):
        """触发重规划失败：不支持的重规划类型（action 参数校验）"""
        event = ExceptionEvent(
            event_code="EX_UNSUPPORTED_001",
            exception_type="node",
            exception_subtype="capacity_limit",
            recommended_action="redispatch",
            description="测试非法action参数",
            status="open",
        )
        db_session.add(event)
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            await ExceptionService.trigger_replan(
                db=db_session,
                event_code="EX_UNSUPPORTED_001",
                action="unknown_action",
                replan_reason="测试",
            )
        assert exc_info.value.status_code == 400
        assert "unknown_action" in exc_info.value.detail

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_trigger_replan_redispatch_success(
        self, db_session, test_nodes, test_orders, test_goods, test_vehicles, test_drivers
    ):
        """触发 redispatch 成功"""
        # 创建原调度方案
        original = GlobalSchedule(
            schedule_code="GS_TRIGGER_001",
            order_codes=list(test_orders.keys())[:3],
            goods_schedules=[],
            total_distance=300.0,
            total_time=15.0,
            total_goods=6,
            score=0.5,
            algorithm_type="traditional",
            version=1,
            is_replan=False,
        )
        db_session.add(original)
        # 重规划需要订单状态为 exception（模拟异常事件后状态已流转）
        for order_code in original.order_codes:
            order = test_orders.get(order_code)
            if order:
                order.status = "exception"
                for goods in order.goods:
                    if goods.status in ["pending_pack"]:
                        goods.status = "exception"
        db_session.commit()

        # 创建异常事件
        event = ExceptionEvent(
            event_code="EX_TRIGGER_001",
            exception_type="node",
            exception_subtype="capacity_limit",
            recommended_action="redispatch",
            related_schedule_code="GS_TRIGGER_001",
            description="触发重调度测试",
            status="open",
        )
        db_session.add(event)
        db_session.commit()

        result = await ExceptionService.trigger_replan(
            db=db_session,
            event_code="EX_TRIGGER_001",
            action="redispatch",
            replan_reason="节点容量异常触发重调度",
        )

        assert result["code"] == 0
        assert result["data"]["is_replan"] is True
        assert result["data"]["original_schedule_code"] == "GS_TRIGGER_001"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_trigger_replan_reroute_success(
        self, db_session, test_nodes
    ):
        """触发 reroute 成功"""
        import json

        # 创建依赖数据
        node_reroute = list(test_nodes.values())[0]
        vehicle = Vehicle(
            vehicle_code="V_REROUTE_T_001",
            model="测试货车",
            vehicle_type="normal",
            energy_type="fuel",
            status="idle",
            capacity=5000.0,
            node_id=node_reroute.id,
            last_arrived_node_id=node_reroute.id,
        )
        driver = Driver(
            driver_code="D_REROUTE_T_001",
            name="测试司机2",
            phone="13800002222",
            license_type="B2",
            shift="早班",
            status="idle",
            node_id=node_reroute.id,
        )
        db_session.add_all([vehicle, driver])

        gs = GlobalSchedule(
            schedule_code="GS_REROUTE_T_001",
            order_codes=["O001"],
            goods_schedules=[],
            total_distance=100.0,
            total_time=5.0,
            total_goods=2,
            score=0.5,
            version=1,
            is_replan=False,
        )
        db_session.add(gs)
        db_session.flush()

        batch = DispatchBatch(
            batch_code="DB_REROUTE_T_001",
            global_schedule_id=gs.id,
            status="completed",
            l0_l1_dispatch_count=1,
            l1_l2_dispatch_count=0,
        )
        db_session.add(batch)
        db_session.flush()

        nd = NodeDispatch(
            dispatch_code="ND_REROUTE_T_001",
            dispatch_batch_id=batch.id,
            vehicle_id=vehicle.id,
            driver_id=driver.id,
            level_phase=0,
            tasks=json.dumps([]),
            total_distance=50.0,
            total_time=2.0,
        )
        db_session.add(nd)
        db_session.flush()

        route = Route(
            route_code="RT_REROUTE_T_001",
            dispatch_id=nd.id,
            vehicle_id=vehicle.id,
            route_segments=json.dumps([]),
            total_distance=50.0,
            total_time=2.0,
            total_emission=10.0,
            version=1,
            is_replan=False,
        )
        db_session.add(route)
        db_session.flush()

        # 创建异常事件（reroute 类型，通过 target_type+target_code 关联路线）
        event = ExceptionEvent(
            event_code="EX_REROUTE_T_001",
            exception_type="road",
            exception_subtype="congestion",
            target_type="route",
            target_code=route.route_code,
            recommended_action="reroute",
            related_schedule_code="GS_REROUTE_T_001",
            description="道路拥堵",
            status="open",
        )
        db_session.add(event)
        db_session.commit()

        # Mock RouteService（路径指向原始模块）
        with patch(
            "services.route_service.RouteService.create_route_planning",
            new_callable=AsyncMock,
        ) as mock_rp:
            mock_rp.return_value = success_response(data={
                "batch_code": "DB_REROUTE_T_001",
                "status": "completed",
                "routes": [{
                    "route_code": "RT_REPLAN_T_001",
                    "dispatch_code": "ND_REROUTE_T_001",
                    "vehicle_code": "V_REROUTE_T_001",
                    "route_segments": [],
                    "total_distance": 55.0,
                    "total_time": 2.2,
                    "total_emission": 11.0,
                    "algorithm_type": "traditional",
                }]
            })

            result = await ExceptionService.trigger_replan(
                db=db_session,
                event_code="EX_REROUTE_T_001",
                action="reroute",
                replan_reason="道路拥堵触发重路径规划",
            )

        assert result["code"] == 0
        assert result["data"]["is_replan"] is True


class TestReplanStrategy:
    """T3-1 重规划策略测试（partial / full / hybrid）"""

    @pytest.mark.unit
    def test_decide_strategy_partial(self):
        """partial 策略透传"""
        assert (
            ReplanService._decide_strategy("partial", ["O001"], ["O001", "O002", "O003"])
            == "partial"
        )

    @pytest.mark.unit
    def test_decide_strategy_full(self):
        """full 策略透传"""
        assert (
            ReplanService._decide_strategy("full", ["O001"], ["O001", "O002", "O003"])
            == "full"
        )

    @pytest.mark.unit
    def test_decide_strategy_hybrid_partial(self):
        """hybrid：受影响订单数 ≤ 一半 → partial"""
        assert (
            ReplanService._decide_strategy(
                "hybrid", ["O001"], ["O001", "O002", "O003", "O004"]
            )
            == "partial"
        )

    @pytest.mark.unit
    def test_decide_strategy_hybrid_full(self):
        """hybrid：受影响订单数 > 一半 → full"""
        assert (
            ReplanService._decide_strategy(
                "hybrid", ["O001", "O002", "O003"], ["O001", "O002", "O003", "O004"]
            )
            == "full"
        )

    @pytest.mark.unit
    def test_decide_strategy_hybrid_no_affected(self):
        """hybrid：无受影响订单 → full"""
        assert (
            ReplanService._decide_strategy("hybrid", [], ["O001", "O002", "O003"])
            == "full"
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_resolve_affected_order_codes_package(self, db_session, test_nodes):
        """T3-1 package 异常 → 解析受影响订单"""
        from models.package import Package

        node_list = list(test_nodes.values())
        pkg = Package(
            package_code="PKG_T31_RES_001",
            weight=10.0,
            volume=0.5,
            status="exception",
            from_node_id=node_list[0].id,
            to_node_id=node_list[1].id,
            goods_items=[{"goods_code": "G001", "order_code": "O001"}],
        )
        db_session.add(pkg)
        db_session.commit()

        event = ExceptionEvent(
            event_code="EX_T31_RES_001",
            exception_type="package",
            exception_subtype="damage",
            target_type="package",
            target_code="PKG_T31_RES_001",
            recommended_action="redispatch",
            status="open",
        )
        affected = ReplanService._resolve_affected_order_codes(db_session, event)
        assert affected == ["O001"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_redispatch_partial_captures_affected_orders(
        self, db_session, test_nodes, test_orders, test_goods, test_vehicles, test_drivers
    ):
        """T3-1 partial 策略：仅将受影响订单传入重规划"""
        from models.package import Package
        from services.schedule_service import ScheduleService

        node_list = list(test_nodes.values())
        original = GlobalSchedule(
            schedule_code="GS_T31_PARTIAL_001",
            order_codes=list(test_orders.keys())[:3],
            goods_schedules=[],
            total_distance=300.0,
            total_time=15.0,
            total_goods=6,
            score=0.5,
            algorithm_type="traditional",
            version=1,
            is_replan=False,
        )
        db_session.add(original)
        db_session.flush()

        # 异常驱动重规划：订单/货物置为 exception
        for order_code in original.order_codes:
            order = test_orders.get(order_code)
            if order:
                order.status = "exception"
                for g in order.goods:
                    if g.status == "pending_pack":
                        g.status = "exception"
        db_session.commit()

        # 受影响包裹（target=package → 解析出订单）
        target_order = original.order_codes[0]
        pkg = Package(
            package_code="PKG_T31_P_001",
            weight=10.0,
            volume=0.5,
            status="exception",
            from_node_id=node_list[0].id,
            to_node_id=node_list[1].id,
            goods_items=[{"goods_code": "G001", "order_code": target_order}],
        )
        db_session.add(pkg)
        db_session.commit()

        event = ExceptionEvent(
            event_code="EX_T31_P_001",
            exception_type="package",
            exception_subtype="damage",
            target_type="package",
            target_code="PKG_T31_P_001",
            recommended_action="redispatch",
            description="包裹损坏",
            status="open",
        )
        db_session.add(event)
        db_session.commit()

        # 拦截 create_global_schedule，捕获传入的 order_codes（其余链路走真实实现）
        real_create = ScheduleService.create_global_schedule
        captured = {}

        async def wrapper(order_codes, *args, **kwargs):
            captured["order_codes"] = order_codes
            return await real_create(order_codes, *args, **kwargs)

        with patch.object(
            ScheduleService, "create_global_schedule", new=wrapper
        ):
            result = await ReplanService.redispatch(
                db=db_session,
                original_schedule_code="GS_T31_PARTIAL_001",
                replan_reason="包裹损坏部分重排",
                event=event,
                strategy="partial",
            )

        assert result["code"] == 0, result
        assert result["data"]["strategy"] == "partial"
        assert captured["order_codes"] == [target_order]  # 仅受影响订单

        # diff_summary 存在且包含验收字段
        assert "diff_summary" in result["data"]
        ds = result["data"]["diff_summary"]
        assert "affected_count" in ds
        assert "new_eta_delta" in ds
        assert "cost_delta" in ds

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_redispatch_full_returns_diff_summary(
        self, db_session, test_nodes, test_orders, test_goods, test_vehicles, test_drivers
    ):
        """T3-1 full 策略：全部重排 + 返回 diff_summary"""
        original = GlobalSchedule(
            schedule_code="GS_T31_FULL_001",
            order_codes=list(test_orders.keys())[:3],
            goods_schedules=[],
            total_distance=300.0,
            total_time=15.0,
            total_goods=6,
            score=0.5,
            algorithm_type="traditional",
            version=1,
            is_replan=False,
        )
        db_session.add(original)
        for order_code in original.order_codes:
            order = test_orders.get(order_code)
            if order:
                order.status = "in_transit"
        db_session.commit()

        result = await ReplanService.redispatch(
            db=db_session,
            original_schedule_code="GS_T31_FULL_001",
            replan_reason="节点容量异常全量重排",
            strategy="full",
        )

        assert result["code"] == 0, result
        assert result["data"]["strategy"] == "full"
        assert "diff_summary" in result["data"]
        ds = result["data"]["diff_summary"]
        assert ds["strategy"] == "full"
        assert ds["affected_count"] >= 0
        assert "new_eta_delta" in ds
        assert "cost_delta" in ds


class TestReplanBatch:
    """T3-1 批量异常重规划测试"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_redispatch_batch_no_events(self, db_session):
        """批量重规划失败：未提供异常事件编码"""
        result = await ReplanService.redispatch_batch(
            db=db_session,
            event_codes=[],
            replan_reason="测试",
        )
        assert result["code"] == 40001
        assert "未提供" in result["message"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_redispatch_batch_events_not_found(self, db_session):
        """批量重规划失败：异常事件不存在"""
        result = await ReplanService.redispatch_batch(
            db=db_session,
            event_codes=["EX_NONE_001"],
            replan_reason="测试",
        )
        assert result["code"] == 40401
        assert "未找到" in result["message"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_redispatch_batch_dedup_same_schedule(self, db_session, test_nodes):
        """同一调度方案关联多个异常 → 只触发一次重规划（验收标准）"""
        node_code = list(test_nodes.keys())[0]
        gs = GlobalSchedule(
            schedule_code="GS_BATCH_001",
            order_codes=["O001"],
            goods_schedules=[],
            total_distance=100.0,
            total_time=5.0,
            total_goods=1,
            score=0.5,
            version=1,
            is_replan=False,
        )
        db_session.add(gs)
        db_session.commit()

        ev1 = ExceptionEvent(
            event_code="EX_BATCH_1",
            exception_type="node",
            exception_subtype="capacity_limit",
            target_type="node",
            target_code=node_code,
            recommended_action="redispatch",
            related_schedule_code="GS_BATCH_001",
            description="批量事件1",
            status="open",
        )
        ev2 = ExceptionEvent(
            event_code="EX_BATCH_2",
            exception_type="node",
            exception_subtype="capacity_limit",
            target_type="node",
            target_code=node_code,
            recommended_action="redispatch",
            related_schedule_code="GS_BATCH_001",
            description="批量事件2",
            status="open",
        )
        db_session.add_all([ev1, ev2])
        db_session.commit()

        with patch.object(
            ReplanService,
            "redispatch",
            new=AsyncMock(return_value=success_response(data={
                "schedule_code": "GS_BATCH_NEW_001",
                "strategy": "full",
            })),
        ) as mock_rd:
            result = await ReplanService.redispatch_batch(
                db=db_session,
                event_codes=["EX_BATCH_1", "EX_BATCH_2"],
                replan_reason="批量重规划",
            )

        assert result["code"] == 0, result
        assert mock_rd.call_count == 1  # 同一方案只重规划一次
        data = result["data"]
        assert len(data["replanned_schedules"]) == 1
        assert data["replanned_schedules"][0]["schedule_code"] == "GS_BATCH_001"
        assert data["replanned_schedules"][0]["event_codes"] == ["EX_BATCH_1", "EX_BATCH_2"]
        assert data["replanned_schedules"][0]["new_schedule_code"] == "GS_BATCH_NEW_001"
        assert data["skipped"] == []

        # 两个事件都回写 replan_batch_code
        db_session.expire_all()
        ev1b = db_session.query(ExceptionEvent).filter(
            ExceptionEvent.event_code == "EX_BATCH_1"
        ).first()
        ev2b = db_session.query(ExceptionEvent).filter(
            ExceptionEvent.event_code == "EX_BATCH_2"
        ).first()
        assert ev1b.replan_batch_code == "GS_BATCH_NEW_001"
        assert ev2b.replan_batch_code == "GS_BATCH_NEW_001"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_redispatch_batch_skips_resolved(self, db_session, test_nodes):
        """已解决的异常事件跳过重规划，不触发下游"""
        node_code = list(test_nodes.keys())[0]
        gs = GlobalSchedule(
            schedule_code="GS_BATCH_002",
            order_codes=["O001"],
            goods_schedules=[],
            total_distance=100.0,
            total_time=5.0,
            total_goods=1,
            score=0.5,
            version=1,
            is_replan=False,
        )
        db_session.add(gs)
        db_session.commit()

        ev_open = ExceptionEvent(
            event_code="EX_BATCH_OPEN",
            exception_type="node",
            target_type="node",
            target_code=node_code,
            recommended_action="redispatch",
            related_schedule_code="GS_BATCH_002",
            description="未解决",
            status="open",
        )
        ev_resolved = ExceptionEvent(
            event_code="EX_BATCH_RESOLVED",
            exception_type="node",
            target_type="node",
            target_code=node_code,
            recommended_action="redispatch",
            related_schedule_code="GS_BATCH_002",
            description="已解决",
            status="resolved",
        )
        db_session.add_all([ev_open, ev_resolved])
        db_session.commit()

        with patch.object(
            ReplanService,
            "redispatch",
            new=AsyncMock(return_value=success_response(data={
                "schedule_code": "GS_BATCH_NEW_002",
                "strategy": "full",
            })),
        ) as mock_rd:
            result = await ReplanService.redispatch_batch(
                db=db_session,
                event_codes=["EX_BATCH_OPEN", "EX_BATCH_RESOLVED"],
                replan_reason="批量重规划",
            )

        assert result["code"] == 0, result
        assert mock_rd.call_count == 1  # 仅 open 事件触发
        data = result["data"]
        assert data["replanned_schedules"][0]["event_codes"] == ["EX_BATCH_OPEN"]
        assert "EX_BATCH_RESOLVED" in data["skipped"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_trigger_batch_replan_service(self, db_session, test_nodes):
        """ExceptionService.trigger_batch_replan 透传 ReplanService"""
        node_code = list(test_nodes.keys())[0]
        gs = GlobalSchedule(
            schedule_code="GS_BATCH_003",
            order_codes=["O001"],
            goods_schedules=[],
            total_distance=100.0,
            total_time=5.0,
            total_goods=1,
            score=0.5,
            version=1,
            is_replan=False,
        )
        db_session.add(gs)
        db_session.commit()
        ev = ExceptionEvent(
            event_code="EX_BATCH_SVC",
            exception_type="node",
            target_type="node",
            target_code=node_code,
            recommended_action="redispatch",
            related_schedule_code="GS_BATCH_003",
            description="服务透传",
            status="open",
        )
        db_session.add(ev)
        db_session.commit()

        with patch.object(
            ReplanService,
            "redispatch",
            new=AsyncMock(return_value=success_response(data={
                "schedule_code": "GS_BATCH_NEW_003",
                "strategy": "partial",
            })),
        ) as mock_rd:
            result = await ExceptionService.trigger_batch_replan(
                db=db_session,
                event_codes=["EX_BATCH_SVC"],
                replan_reason="服务透传测试",
                strategy="partial",
            )

        assert result["code"] == 0, result
        assert mock_rd.call_count == 1
