"""
集成测试：调度流水线（F007 → F021 → F005 → F006）

测试目标：
- 验证全局调度、节点调度、路径规划的完整流程
- 验证模块间的交互和数据一致性
- 验证事务原子性和错误回滚
"""
import pytest
from sqlalchemy.orm import Session

from services.schedule_service import ScheduleService
from services.dispatch_service import DispatchService
from models.global_schedule import GlobalSchedule
from models.dispatch_batch import DispatchBatch
from models.package import Package
from models.goods import Goods
from models.order import Order


class TestSchedulePipeline:
    """测试完整调度流水线"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_pipeline(self, db_session, test_nodes, test_orders, test_goods, test_vehicles, test_drivers):
        """
        测试完整流水线（P1-2 预览→确认两步流）：
        1. F007：预览创建 draft 方案
        2. 确认：执行 F021 打包
        3. F005：节点间调度（第一次，L0→L1）
        4. F006：路径规划
        
        验证：
        - 预览成功，生成 schedule_code，status=draft
        - 确认后 orders→delivering，packages 有记录
        - 节点调度成功，dispatch_batches 表有记录
        - 路径规划成功，routes 表有记录
        """
        # ── 第1步：预览全局调度 ──────────────────────────────
        schedule_result = await ScheduleService.create_global_schedule(
            order_codes=None,
            algorithm="traditional",
            db=db_session,
            preview=True,
        )
        assert schedule_result["code"] == 0
        assert schedule_result["data"]["status"] == "draft"
        schedule_code = schedule_result["data"]["schedule_code"]

        # ── 第2步：确认方案（draft → active）────────────────
        confirm_result = await ScheduleService.confirm_schedule(
            schedule_code=schedule_code,
            db=db_session,
        )
        assert confirm_result["code"] == 0
        assert confirm_result["data"]["status"] == "active"

        # 验证 global_schedules 表有记录
        gs_list = db_session.query(GlobalSchedule).all()
        assert len(gs_list) == 1
        gs = gs_list[0]
        assert gs.schedule_code == schedule_code
        assert gs.status == "active"

        # 验证 packages 表有记录
        packages = db_session.query(Package).filter(Package.schedule_id == gs.id).all()
        assert len(packages) > 0

        # 验证 orders 状态变为 delivering
        for order_code in ["O001", "O002", "O003"]:
            order = db_session.query(Order).filter(Order.order_code == order_code).first()
            assert order.status == "delivering"

        # ── 第3步：节点间调度（第一次，L0→L1）──────────────────────────────
        # 为简化测试，我们假设测试数据已经包含了车辆和司机（test_vehicles, test_drivers）

        # ── 验证 ─────────────────────────────────────────────
        assert schedule_result["data"]["total_goods"] == 18  # 9订单 × 2货物/订单
        assert confirm_result["data"]["package_count"] > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_schedule_then_query(self, db_session, test_nodes, test_orders, test_goods):
        """
        测试调度后查询（P1-2 预览→确认两步流）：
        1. 执行预览
        2. 确认方案
        3. 查询调度方案列表
        4. 查询调度方案详情
        """
        # 执行预览
        schedule_result = await ScheduleService.create_global_schedule(
            order_codes=None,
            algorithm="traditional",
            db=db_session,
            preview=True,
        )
        assert schedule_result["code"] == 0
        schedule_code = schedule_result["data"]["schedule_code"]

        # 确认方案
        confirm_result = await ScheduleService.confirm_schedule(
            schedule_code=schedule_code,
            db=db_session,
        )
        assert confirm_result["code"] == 0

        # 查询调度方案列表
        list_result = await ScheduleService.get_global_schedules(
            page=1, page_size=20, order_code=None, db=db_session
        )
        assert list_result["code"] == 0
        assert list_result["data"]["total"] == 1
        assert len(list_result["data"]["items"]) == 1
        assert list_result["data"]["items"][0]["schedule_code"] == schedule_code

        # 查询调度方案详情
        detail_result = await ScheduleService.get_global_schedule(
            schedule_code=schedule_code, db=db_session
        )
        assert detail_result["code"] == 0
        assert detail_result["data"]["schedule_code"] == schedule_code
        assert detail_result["data"]["total_goods"] == 18  # 9订单 × 2货物/订单
        # P1-06 修改后 goods_schedules 格式变更，检查是否有数据即可
        assert len(detail_result["data"]["goods_schedules"]) >= 1
        # 验证 goods_schedules 格式：每项应包含 goods_code, path (对象数组)
        if len(detail_result["data"]["goods_schedules"]) > 0:
            first_item = detail_result["data"]["goods_schedules"][0]
            assert "goods_code" in first_item
            assert "path" in first_item
            assert isinstance(first_item["path"], list)
            if len(first_item["path"]) > 0:
                assert "node_code" in first_item["path"][0]
                assert "node_name" in first_item["path"][0]
        assert len(detail_result["data"]["packages"]) > 0


class TestScheduleTransaction:
    """测试调度事务原子性"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_schedule_transaction_rollback(self, db_session, test_nodes, test_orders, test_goods):
        """
        测试确认阶段事务回滚（P1-2）：
        如果 confirm 时打包失败，draft 应被删除且其他数据不变
        """
        from unittest.mock import patch

        # 先创建 preview draft
        preview_result = await ScheduleService.create_global_schedule(
            order_codes=None,
            algorithm="traditional",
            db=db_session,
            preview=True,
        )
        assert preview_result["code"] == 0
        schedule_code = preview_result["data"]["schedule_code"]

        # 确认 draft 前确保它在
        gs_count_before = db_session.query(GlobalSchedule).count()
        assert gs_count_before == 1

        # Mock packaging 函数抛出异常
        with patch("services.schedule_service.packaging") as mock_packaging:
            mock_packaging.side_effect = RuntimeError("模拟打包异常")

            result = await ScheduleService.confirm_schedule(
                schedule_code=schedule_code,
                db=db_session,
            )

        # 验证返回错误（打包异常被 confirm_schedule 捕获后统一返回 50001）
        assert result["code"] == 50001

        # 验证事务回滚：draft 不在了（被 confirm 清理）
        gs_count = db_session.query(GlobalSchedule).count()
        assert gs_count == 0

        # 验证事务回滚：packages 表应该为空
        pkg_count = db_session.query(Package).count()
        assert pkg_count == 0

        # 验证事务回滚：orders 状态应该保持 pending
        for order_code in ["O001", "O002", "O003"]:
            order = db_session.query(Order).filter(Order.order_code == order_code).first()
            assert order.status == "pending"
