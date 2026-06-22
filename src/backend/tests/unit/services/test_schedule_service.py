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
    """正常流程：F007→F021→单事务写入"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_normal_flow_writes_all_data(self, db_session, test_nodes, test_orders, test_goods):
        """
        正常调度流程：
        1. F007 成功生成 goods_schedules
        2. F021 成功生成 packages
        3. 单事务写入：global_schedules + packages + orders/goods 状态更新
        验证：
        - 响应 code=0
        - global_schedules 表有 1 条记录
        - packages 表有记录
        - orders 状态从 pending → delivering
        - goods 状态从 pending_pack → packed
        """
        result = await ScheduleService.create_global_schedule(
            order_codes=None,
            algorithm="traditional",
            db=db_session,
        )

        # ── 验证响应格式 ──
        assert result["code"] == 0
        assert result["message"] == "success"
        assert result["data"]["schedule_code"].startswith("GS")
        assert result["data"]["total_goods"] == 18  # 9订单 × 2货物/订单
        assert result["data"]["package_count"] > 0
        assert result["data"]["version"] == 1
        assert result["data"]["is_replan"] is False

        # ── 验证 global_schedules 写入 ──
        gs_list = db_session.query(GlobalSchedule).all()
        assert len(gs_list) == 1
        gs = gs_list[0]
        assert gs.schedule_code == result["data"]["schedule_code"]
        assert gs.total_goods == 18  # 9订单 × 2货物/订单
        assert gs.algorithm_type == "traditional"
        assert gs.version == 1
        assert gs.is_replan is False

        # ── 验证 packages 写入 ──
        packages = db_session.query(Package).filter(
            Package.schedule_id == gs.id
        ).all()
        assert len(packages) == result["data"]["package_count"]
        for pkg in packages:
            assert pkg.status == "packed"
            assert pkg.schedule_id == gs.id

        # ── 验证 orders 状态更新 ──
        for order in test_orders.values():
            db_session.refresh(order)
            assert order.status == "delivering", (
                f"订单 {order.order_code} 状态应为 delivering，实际 {order.status}"
            )

        # ── 验证 goods 状态更新 ──
        for goods in test_goods.values():
            db_session.refresh(goods)
            assert goods.status == "packed", (
                f"货物 {goods.goods_code} 状态应为 packed，实际 {goods.status}"
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_specific_orders_schedule(self, db_session, test_nodes, test_orders, test_goods):
        """
        指定订单编号进行调度
        仅调度 O001 和 O002，O003 保持不变
        """
        result = await ScheduleService.create_global_schedule(
            order_codes=["O001", "O002"],
            algorithm="traditional",
            db=db_session,
        )

        assert result["code"] == 0
        assert result["data"]["total_goods"] == 4  # O001有2个货物 + O002有2个货物

        # O001、O002 应变为 delivering
        db_session.refresh(test_orders["O001"])
        db_session.refresh(test_orders["O002"])
        db_session.refresh(test_orders["O003"])
        assert test_orders["O001"].status == "delivering"
        assert test_orders["O002"].status == "delivering"
        assert test_orders["O003"].status == "pending", "O003 未参与调度，应保持 pending"


class TestScheduleServiceExceptionRollback:
    """异常流程：事务回滚验证"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_f021_exception_triggers_rollback(self, db_session, test_nodes, test_orders, test_goods):
        """
        F021 抛出异常 → 事务回滚 → global_schedules 不写入
        通过 mock packaging 函数抛异常模拟
        """
        with patch("services.schedule_service.packaging") as mock_packaging:
            mock_packaging.side_effect = RuntimeError("模拟打包异常")

            result = await ScheduleService.create_global_schedule(
                order_codes=None,
                algorithm="traditional",
                db=db_session,
            )

        # ── 验证响应为错误 ──
        assert result["code"] == 40001
        assert "全局调度异常" in result["message"]
        assert "模拟打包异常" in result["message"]

        # ── 验证 global_schedules 未写入 ──
        gs_count = db_session.query(GlobalSchedule).count()
        assert gs_count == 0, f"事务应回滚，global_schedules 应为 0 条，实际 {gs_count} 条"

        # ── 验证 packages 未写入 ──
        pkg_count = db_session.query(Package).count()
        assert pkg_count == 0, f"事务应回滚，packages 应为 0 条，实际 {pkg_count} 条"

        # ── 验证 orders 状态未变化 ──
        for order in test_orders.values():
            db_session.refresh(order)
            assert order.status == "pending", (
                f"事务回滚后订单 {order.order_code} 应保持 pending，实际 {order.status}"
            )

        # ── 验证 goods 状态未变化 ──
        for goods in test_goods.values():
            db_session.refresh(goods)
            assert goods.status == "pending_pack", (
                f"事务回滚后货物 {goods.goods_code} 应保持 pending_pack，实际 {goods.status}"
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_f007_exception_triggers_rollback(self, db_session, test_nodes, test_orders, test_goods):
        """
        F007 抛出异常 → 事务回滚 → 无任何写入
        """
        with patch("services.schedule_service.global_schedule") as mock_gs:
            mock_gs.side_effect = ValueError("模拟 F007 算法失败")

            result = await ScheduleService.create_global_schedule(
                order_codes=None,
                algorithm="traditional",
                db=db_session,
            )

        assert result["code"] == 40001
        assert "模拟 F007 算法失败" in result["message"]

        # 无数据写入
        assert db_session.query(GlobalSchedule).count() == 0
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
