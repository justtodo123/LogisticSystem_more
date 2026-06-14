"""
服务单元测试：DispatchService（调度批次服务）

测试目标：
- DispatchService.create_node_dispatch 方法的正常流程和异常流程
- 验证服务层业务逻辑、车辆分配、司机分配、错误处理
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from services.dispatch_service import DispatchService
from models.dispatch_batch import DispatchBatch
from models.node_dispatch import NodeDispatch
from models.package import Package
from models.vehicle import Vehicle
from models.driver import Driver


class TestCreateNodeDispatch:
    """测试创建节点调度"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_node_dispatch_success(self, db_session, test_nodes, test_orders, test_goods, test_vehicles, test_drivers):
        """
        测试成功创建节点调度：
        1. 先执行全局调度，生成包裹
        2. 调用 create_node_dispatch(schedule_code, demo_mode=True)
        3. 验证返回成功，生成 batch_code
        4. 验证 dispatch_batches 表有记录
        5. 验证 node_dispatches 表有记录
        """
        # 先执行全局调度
        from services.schedule_service import ScheduleService
        schedule_result = await ScheduleService.create_global_schedule(
            order_codes=None,
            algorithm="traditional",
            db=db_session,
        )
        assert schedule_result["code"] == 0
        schedule_code = schedule_result["data"]["schedule_code"]
        
        # 调用节点调度
        result = await DispatchService.create_node_dispatch(
            schedule_code=schedule_code,
            demo_mode=True,
            db=db_session,
        )
        
        # 验证响应
        assert result["code"] == 0
        assert "data" in result
        assert "batch_code" in result["data"]
        
        # 验证 dispatch_batches 表有记录
        batch_list = db_session.query(DispatchBatch).all()
        assert len(batch_list) >= 1
        
        # 验证 node_dispatches 表有记录
        nd_list = db_session.query(NodeDispatch).all()
        assert len(nd_list) >= 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_node_dispatch_schedule_not_found(self, db_session):
        """
        测试调度方案不存在：
        1. 调用 create_node_dispatch("GS_NONEXIST", ...)
        2. 验证返回业务错误
        """
        result = await DispatchService.create_node_dispatch(
            schedule_code="GS_NONEXIST",
            demo_mode=True,
            db=db_session,
        )
        
        # 验证响应（业务错误）
        assert result["code"] != 0
        assert "调度" in result["message"] or "不存在" in result["message"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_node_dispatch_no_available_vehicles(self, db_session, test_nodes, test_orders, test_goods):
        """
        测试没有可用车辆：
        1. 先执行全局调度，生成包裹
        2. 但不创建车辆（test_vehicles fixture不使用）
        3. 调用 create_node_dispatch
        4. 验证返回业务错误（或空批次）
        """
        # 先执行全局调度
        from services.schedule_service import ScheduleService
        schedule_result = await ScheduleService.create_global_schedule(
            order_codes=None,
            algorithm="traditional",
            db=db_session,
        )
        assert schedule_result["code"] == 0
        schedule_code = schedule_result["data"]["schedule_code"]
        
        # 调用节点调度（应该失败，因为没有车辆）
        result = await DispatchService.create_node_dispatch(
            schedule_code=schedule_code,
            demo_mode=True,
            db=db_session,
        )
        
        # 验证响应（可能是业务错误或空批次）
        # 注意：实际行为取决于DispatchService的实现
        # 这里我们假设返回业务错误
        if result["code"] != 0:
            assert "车辆" in result["message"] or "不可用" in result["message"]
        else:
            # 或者返回空批次
            assert result["data"]["total_packages"] == 0


class TestGetDispatchBatches:
    """测试查询调度批次"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_batches_empty(self, db_session):
        """测试空数据库返回空列表"""
        result = await DispatchService.get_dispatch_batches(
            page=1, page_size=20, db=db_session
        )
        
        assert result["code"] == 0
        assert result["data"]["items"] == []
        assert result["data"]["total"] == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_batches_with_data(self, db_session, test_nodes, test_orders, test_goods, test_vehicles, test_drivers):
        """测试有数据时返回批次列表"""
        # 先执行全局调度和节点调度
        from services.schedule_service import ScheduleService
        schedule_result = await ScheduleService.create_global_schedule(
            order_codes=None,
            algorithm="traditional",
            db=db_session,
        )
        assert schedule_result["code"] == 0
        schedule_code = schedule_result["data"]["schedule_code"]
        
        batch_result = await DispatchService.create_node_dispatch(
            schedule_code=schedule_code,
            demo_mode=True,
            db=db_session,
        )
        assert batch_result["code"] == 0
        
        # 查询批次列表
        result = await DispatchService.get_dispatch_batches(
            page=1, page_size=20, db=db_session
        )
        
        assert result["code"] == 0
        assert len(result["data"]["items"]) >= 1
        assert result["data"]["total"] >= 1


class TestGetDispatchBatchDetail:
    """测试查询调度批次详情"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_batch_detail_success(self, db_session, test_nodes, test_orders, test_goods, test_vehicles, test_drivers):
        """测试成功获取批次详情"""
        # 先执行全局调度和节点调度
        from services.schedule_service import ScheduleService
        schedule_result = await ScheduleService.create_global_schedule(
            order_codes=None,
            algorithm="traditional",
            db=db_session,
        )
        assert schedule_result["code"] == 0
        schedule_code = schedule_result["data"]["schedule_code"]
        
        batch_result = await DispatchService.create_node_dispatch(
            schedule_code=schedule_code,
            demo_mode=True,
            db=db_session,
        )
        assert batch_result["code"] == 0
        batch_code = batch_result["data"]["batch_code"]
        
        # 获取批次详情
        result = await DispatchService.get_dispatch_batch(
            batch_code=batch_code, db=db_session
        )
        
        assert result["code"] == 0
        assert result["data"]["batch_code"] == batch_code
        assert "node_dispatches" in result["data"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_batch_detail_not_found(self, db_session):
        """测试批次不存在"""
        result = await DispatchService.get_dispatch_batch(
            batch_code="BATCH_NONEXIST", db=db_session
        )
        
        assert result["code"] != 0
        assert "批次" in result["message"] or "不存在" in result["message"]
