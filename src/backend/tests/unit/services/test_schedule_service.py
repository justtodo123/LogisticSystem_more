"""
服务单元测试：ScheduleService（调度编排服务）

测试目标：
- ScheduleService.create_global_schedule 方法的正常流程和异常流程
- 验证服务层业务逻辑、事务管理、错误处理
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from services.schedule_service import ScheduleService
from models.global_schedule import GlobalSchedule
from models.package import Package
from models.order import Order
from models.goods import Goods


class TestScheduleServiceNormalFlow:
    """正常流程：预览→确认（P1-2 两步流）"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_normal_flow_preview_then_confirm(self, db_session, test_nodes, test_orders, test_goods):
        """
        P1-2 正常两步流：
        1. 预览：F007 生成 draft 方案（不写 packages、不改状态）
        2. 确认：执行 F021 + 写入 packages + 状态更新
        验证：
        - 预览后：code=0, status=draft, package_count=0, 订单/货物状态不变
        - 确认后：status=active, packages 有记录, orders→delivering, goods→packed
        """
        # ── 步骤1：预览 ──
        preview_result = await ScheduleService.create_global_schedule(
            order_codes=None,
            algorithm="traditional",
            db=db_session,
            preview=True,
        )

        # 验证预览响应
        assert preview_result["code"] == 0
        assert preview_result["data"]["status"] == "draft"
        assert preview_result["data"]["package_count"] == 0
        assert preview_result["data"]["schedule_code"].startswith("GS")
        assert preview_result["data"]["total_goods"] == 18  # 9订单 × 2货物/订单
        assert preview_result["data"]["version"] == 1
        assert preview_result["data"]["is_replan"] is False

        # 验证预览后 global_schedules 写入（draft）
        gs_list = db_session.query(GlobalSchedule).all()
        assert len(gs_list) == 1
        gs = gs_list[0]
        assert gs.status == "draft"
        assert gs.total_goods == 18

        # 验证预览后 packages 表为空
        pkg_count = db_session.query(Package).count()
        assert pkg_count == 0, "预览不应生成包裹"

        # 验证预览后 orders/goods 状态不变
        for order in test_orders.values():
            db_session.refresh(order)
            assert order.status == "pending"
        for goods in test_goods.values():
            db_session.refresh(goods)
            assert goods.status == "pending_pack"

        schedule_code = preview_result["data"]["schedule_code"]

        # ── 步骤2：确认 ──
        confirm_result = await ScheduleService.confirm_schedule(
            schedule_code=schedule_code,
            db=db_session,
        )

        # 验证确认响应
        assert confirm_result["code"] == 0
        assert confirm_result["data"]["status"] == "active"
        assert confirm_result["data"]["package_count"] > 0

        # 验证 global_schedules status → active
        db_session.refresh(gs)
        assert gs.status == "active"

        # 验证 packages 写入
        packages = db_session.query(Package).filter(
            Package.schedule_id == gs.id
        ).all()
        assert len(packages) == confirm_result["data"]["package_count"]
        packed_count = sum(1 for p in packages if p.status == "packed")
        pending_count = sum(1 for p in packages if p.status == "pending_pack")
        assert packed_count > 0, "应至少有一个 L0→L1 包裹状态为 packed"
        assert pending_count > 0, "应至少有一个 L1→L2 包裹状态为 pending_pack"

        # 验证 orders 状态：pending → delivering
        for order in test_orders.values():
            db_session.refresh(order)
            assert order.status == "delivering"

        # 验证 goods 状态：pending_pack → packed
        for goods in test_goods.values():
            db_session.refresh(goods)
            assert goods.status == "packed"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_no_preview_param_returns_error(self, db_session):
        """
        不传 preview 参数 → 返回 40000（P1-2 强制预览模式）
        """
        result = await ScheduleService.create_global_schedule(
            order_codes=None,
            algorithm="traditional",
            db=db_session,
            preview=False,
        )
        assert result["code"] == 40000
        assert "已移除直接落库" in result["message"]


class TestScheduleServiceExceptionRollback:
    """异常流程：事务回滚验证（适配 P1-2 两步流）"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_preview_f007_exception_triggers_rollback(self, db_session, test_nodes, test_orders, test_goods):
        """
        F007 抛出异常 → preview 返回错误 → 无任何写入
        """
        with patch("services.schedule_service.global_schedule") as mock_gs:
            mock_gs.side_effect = ValueError("模拟 F007 算法失败")

            result = await ScheduleService.create_global_schedule(
                order_codes=None,
                algorithm="traditional",
                db=db_session,
                preview=True,
            )

        assert result["code"] == 40001
        assert "模拟 F007 算法失败" in result["message"]

        # 无数据写入
        assert db_session.query(GlobalSchedule).count() == 0
        assert db_session.query(Package).count() == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_confirm_packaging_exception_deletes_draft(self, db_session, test_nodes, test_orders, test_goods):
        """
        confirm 时 F021 打包异常 → 返回错误 → draft 被删除
        """
        # 1. 预览
        preview_result = await ScheduleService.create_global_schedule(
            order_codes=None,
            algorithm="traditional",
            db=db_session,
            preview=True,
        )
        schedule_code = preview_result["data"]["schedule_code"]

        # 2. Mock packaging 抛异常
        with patch("services.schedule_service.packaging") as mock_packaging:
            mock_packaging.side_effect = RuntimeError("模拟打包异常")

            confirm_result = await ScheduleService.confirm_schedule(
                schedule_code=schedule_code,
                db=db_session,
            )

        # 验证响应为错误
        assert confirm_result["code"] == 50001
        assert "确认失败，draft 已丢弃" in confirm_result["message"]

        # 验证 draft 已被删除
        gs = db_session.query(GlobalSchedule).filter(
            GlobalSchedule.schedule_code == schedule_code
        ).first()
        assert gs is None, "confirm 失败后 draft 应被删除"

        # 验证 packages 未写入
        assert db_session.query(Package).count() == 0


class TestScheduleServiceQuery:
    """查询服务测试"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_global_schedules_empty(self, db_session):
        """空数据库获取历史列表"""
        result = await ScheduleService.get_global_schedules(
            page=1, page_size=20, order_code=None, db=db_session
        )
        assert result["code"] == 0
        assert result["data"]["items"] == []
        assert result["data"]["total"] == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_global_schedule_not_found(self, db_session):
        """获取不存在的调度方案"""
        result = await ScheduleService.get_global_schedule(
            schedule_code="GS_NONEXIST", db=db_session
        )
        assert result["code"] == 40401
        assert "不存在" in result["message"]


class TestScheduleServiceP1PreviewConfirm:
    """P1-2 预览确认功能测试"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_preview_creates_draft(self, db_session, test_nodes, test_orders, test_goods):
        """
        预览模式：preview=True 后，global_schedules 中 status=draft，订单状态不变
        """
        result = await ScheduleService.create_global_schedule(
            order_codes=None,
            algorithm="traditional",
            db=db_session,
            preview=True,
        )

        # 验证响应
        assert result["code"] == 0
        assert result["data"]["status"] == "draft"
        assert result["data"]["package_count"] == 0  # 预览时不生成包裹

        # 验证数据库：global_schedules 有记录，status=draft
        gs_list = db_session.query(GlobalSchedule).all()
        assert len(gs_list) == 1
        gs = gs_list[0]
        assert gs.status == "draft"

        # 验证订单状态不变
        for order in test_orders.values():
            db_session.refresh(order)
            assert order.status == "pending", "预览模式不应改变订单状态"

        # 验证货物状态不变
        for goods in test_goods.values():
            db_session.refresh(goods)
            assert goods.status == "pending_pack", "预览模式不应改变货物状态"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_preview_returns_schedule_code(self, db_session, test_nodes, test_orders, test_goods):
        """
        预览成功：响应含 schedule_code 和 status: "draft"
        """
        result = await ScheduleService.create_global_schedule(
            order_codes=None,
            algorithm="traditional",
            db=db_session,
            preview=True,
        )

        assert result["code"] == 0
        assert "schedule_code" in result["data"]
        assert result["data"]["schedule_code"].startswith("GS")
        assert result["data"]["status"] == "draft"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_confirm_updates_status(self, db_session, test_nodes, test_orders, test_goods):
        """
        确认成功：confirm 后 status=active，订单 delivering，包裹 packed
        """
        # 1. 预览
        preview_result = await ScheduleService.create_global_schedule(
            order_codes=None,
            algorithm="traditional",
            db=db_session,
            preview=True,
        )
        schedule_code = preview_result["data"]["schedule_code"]

        # 2. 确认
        confirm_result = await ScheduleService.confirm_schedule(
            schedule_code=schedule_code,
            db=db_session,
        )

        # 验证响应
        assert confirm_result["code"] == 0
        assert confirm_result["data"]["status"] == "active"
        assert confirm_result["data"]["package_count"] > 0

        # 验证数据库：status=active
        gs = db_session.query(GlobalSchedule).filter(
            GlobalSchedule.schedule_code == schedule_code
        ).first()
        assert gs.status == "active"

        # 验证订单状态：pending → delivering
        for order in test_orders.values():
            db_session.refresh(order)
            assert order.status == "delivering"

        # 验证货物状态：pending_pack → packed
        for goods in test_goods.values():
            db_session.refresh(goods)
            assert goods.status == "packed"

        # 验证包裹状态：部分 packed，部分 pending_pack
        packages = db_session.query(Package).filter(
            Package.schedule_id == gs.id
        ).all()
        assert len(packages) == confirm_result["data"]["package_count"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_confirm_fails_if_order_status_changed(self, db_session, test_nodes, test_orders, test_goods):
        """
        确认失败：订单状态已变化，confirm 报错，draft 被删除
        """
        # 1. 预览（使用全部订单，已验证可行）
        preview_result = await ScheduleService.create_global_schedule(
            order_codes=None,
            algorithm="traditional",
            db=db_session,
            preview=True,
        )
        schedule_code = preview_result["data"]["schedule_code"]

        # 2. 修改订单状态（模拟状态变化，completed 是 Order 合法状态且不可再确认）
        test_orders["O001"].status = "completed"
        db_session.commit()

        # 3. 确认（应失败）
        confirm_result = await ScheduleService.confirm_schedule(
            schedule_code=schedule_code,
            db=db_session,
        )

        # 验证响应
        assert confirm_result["code"] == 40003
        assert "状态已变化" in confirm_result["message"]

        # 验证 draft 已被删除
        gs = db_session.query(GlobalSchedule).filter(
            GlobalSchedule.schedule_code == schedule_code
        ).first()
        assert gs is None, "confirm 失败后 draft 应被删除"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_discard_draft(self, db_session, test_nodes, test_orders, test_goods):
        """
        丢弃 draft：DELETE draft 后记录被删除
        """
        # 1. 预览
        preview_result = await ScheduleService.create_global_schedule(
            order_codes=None,
            algorithm="traditional",
            db=db_session,
            preview=True,
        )
        schedule_code = preview_result["data"]["schedule_code"]

        # 2. 丢弃
        discard_result = await ScheduleService.discard_draft(
            schedule_code=schedule_code,
            db=db_session,
        )

        # 验证响应
        assert discard_result["code"] == 0
        assert discard_result["data"]["status"] == "discarded"

        # 验证记录已被删除
        gs = db_session.query(GlobalSchedule).filter(
            GlobalSchedule.schedule_code == schedule_code
        ).first()
        assert gs is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_discard_non_draft_fails(self, db_session, test_nodes, test_orders, test_goods):
        """
        丢弃非 draft 失败：对 active 方案调用 discard 返回 40401
        """
        # 1. 预览 + 确认（生成 active 方案）
        preview_result = await ScheduleService.create_global_schedule(
            order_codes=None,
            algorithm="traditional",
            db=db_session,
            preview=True,
        )
        schedule_code = preview_result["data"]["schedule_code"]
        await ScheduleService.confirm_schedule(
            schedule_code=schedule_code,
            db=db_session,
        )

        # 2. 尝试丢弃 active 方案（应失败）
        discard_result = await ScheduleService.discard_draft(
            schedule_code=schedule_code,
            db=db_session,
        )

        # 验证响应
        assert discard_result["code"] == 40401
        assert "不存在或已确认" in discard_result["message"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_default_filters_draft(self, db_session, test_nodes, test_orders, test_goods):
        """
        列表默认过滤 draft：GET /global 默认不返回 status=draft 的方案
        """
        # 1. 预览（生成 draft）
        await ScheduleService.create_global_schedule(
            order_codes=None,
            algorithm="traditional",
            db=db_session,
            preview=True,
        )

        # 2. 查询列表（默认过滤 draft）
        result = await ScheduleService.get_global_schedules(
            page=1, page_size=20, order_code=None, db=db_session
        )

        # 验证：列表为空（因为只有一个 draft）
        assert result["code"] == 0
        assert result["data"]["total"] == 0
        assert len(result["data"]["items"]) == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_with_status_param(self, db_session, test_nodes, test_orders, test_goods):
        """
        列表按状态筛选：GET /global?status=draft 可查 draft 方案
        """
        # 1. 预览（生成 draft）
        preview_result = await ScheduleService.create_global_schedule(
            order_codes=None,
            algorithm="traditional",
            db=db_session,
            preview=True,
        )
        schedule_code = preview_result["data"]["schedule_code"]

        # 2. 查询列表（按 status=draft 筛选）
        result = await ScheduleService.get_global_schedules(
            page=1, page_size=20, order_code=None, status="draft", db=db_session
        )

        # 验证：列表包含 draft 方案
        assert result["code"] == 0
        assert result["data"]["total"] == 1
        assert len(result["data"]["items"]) == 1
        assert result["data"]["items"][0]["schedule_code"] == schedule_code
        assert result["data"]["items"][0]["status"] == "draft"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_duplicate_preview_fails(self, db_session, test_nodes, test_orders, test_goods):
        """
        重复预览失败：对已 confirm 的订单重复 preview 返回 40002
        """
        # 1. 预览 + 确认（生成 active 方案）
        preview_result = await ScheduleService.create_global_schedule(
            order_codes=None,
            algorithm="traditional",
            db=db_session,
            preview=True,
        )
        schedule_code = preview_result["data"]["schedule_code"]
        await ScheduleService.confirm_schedule(
            schedule_code=schedule_code,
            db=db_session,
        )

        # 2. 验证 active 记录存在，取出其 order_codes
        active_gs = db_session.query(GlobalSchedule).filter(
            GlobalSchedule.status == "active"
        ).first()
        assert active_gs is not None
        assert active_gs.order_codes is not None
        assert len(active_gs.order_codes) > 0

        # 3. 用 active 记录中的第一个 order_code 再次预览（应触发重复检查）
        test_order_code = active_gs.order_codes[0]
        result = await ScheduleService.create_global_schedule(
            order_codes=[test_order_code],
            algorithm="traditional",
            db=db_session,
            preview=True,
        )

        # 验证被重复检查拦截（F007不应被调用）
        assert result["code"] == 40002
        assert "已有活跃" in result["message"]

