"""
<<<<<<< HEAD:src/backend/tests/unit/services/test_dispatch_service.py
服务单元测试：DispatchService（调度批次服务）

测试目标：
- DispatchService.create_node_dispatch 方法的正常流程和异常流程
- 验证服务层业务逻辑、车辆分配、司机分配、错误处理
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from services.dispatch_service import DispatchService
=======
test_dispatch_service.py — 节点调度服务层测试

测试用例：
1. create_node_dispatch：正常创建调度批次
2. create_node_dispatch：调度失败（无可用车辆）
3. get_dispatch_batches：获取批次列表
4. get_dispatch_batches：按状态筛选
5. get_dispatch_batch_detail：获取批次详情
6. get_dispatch_batch_detail：返回 unallocated_packages
7. get_dispatch_batch_detail：批次不存在
"""
import pytest
import json
import asyncio
>>>>>>> backend/phase-5:src/backend/tests/test_services/test_dispatch_service.py
from models.dispatch_batch import DispatchBatch
from models.node_dispatch import NodeDispatch
from models.package import Package
from models.vehicle import Vehicle
from models.driver import Driver
<<<<<<< HEAD:src/backend/tests/unit/services/test_dispatch_service.py


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
            schedule_code=None, status=None, db=db_session
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
            schedule_code=None, status=None, db=db_session
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
        result = await DispatchService.get_dispatch_batch_detail(
            batch_code=batch_code, db=db_session
        )
        
        assert result["code"] == 0
        assert result["data"]["batch_code"] == batch_code
        assert "dispatches" in result["data"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_batch_detail_not_found(self, db_session):
        """测试批次不存在"""
        result = await DispatchService.get_dispatch_batch_detail(
            batch_code="BATCH_NONEXIST", db=db_session
        )
        
        assert result["code"] != 0
        assert "批次" in result["message"] or "不存在" in result["message"]
=======
from services.dispatch_service import DispatchService


class TestCreateNodeDispatch:
    """测试 create_node_dispatch 服务"""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_success(self, db_session, test_nodes, test_vehicles, test_drivers):
        """
        正常创建调度批次
        """
        # 1. 创建全局调度方案
        from models.global_schedule import GlobalSchedule
        schedule = GlobalSchedule(
            schedule_code="GS_TEST001",
            order_codes=["O001"],
            goods_schedules=[
                {"goods_code": "G001", "order_code": "O001", "path": ["SC001", "SO001", "SO010"]}
            ],
            total_distance=0,
            total_time=0,
            total_goods=1,
            score=0,
        )
        db_session.add(schedule)
        db_session.flush()

        # 2. 创建包裹（status='packed'）
        pkg = Package(
            package_code="PKG_TEST001",
            weight=10.0,
            volume=0.5,
            status="packed",
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO001"].id,
            goods_items=[{"goods_code": "G001", "order_code": "O001"}],
            schedule_id=schedule.id,
        )
        db_session.add(pkg)
        db_session.commit()

        # 3. 调用服务
        result = await DispatchService.create_node_dispatch(
            schedule_code="GS_TEST001",
            demo_mode=True,
            db=db_session,
        )

        # 4. 验证响应
        assert result["code"] == 0
        assert result["message"] == "success"
        assert "batch_code" in result["data"]
        assert result["data"]["status"] == "completed"
        assert "dispatches" in result["data"]
        assert "unallocated_packages" in result["data"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_no_vehicle(self, db_session, test_nodes):
        """
        调度失败：无可用车辆
        """
        # 创建全局调度方案
        from models.global_schedule import GlobalSchedule
        schedule = GlobalSchedule(
            schedule_code="GS_TEST002",
            order_codes=["O001"],
            goods_schedules=[],
            total_distance=0,
            total_time=0,
            total_goods=0,
            score=0,
        )
        db_session.add(schedule)
        db_session.flush()

        # 创建包裹（但无车辆）
        pkg = Package(
            package_code="PKG_TEST002",
            weight=10.0,
            volume=0.5,
            status="packed",
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO001"].id,
            goods_items=[{"goods_code": "G001", "order_code": "O001"}],
            schedule_id=schedule.id,
        )
        db_session.add(pkg)
        db_session.commit()

        # 调用服务（应失败）
        result = await DispatchService.create_node_dispatch(
            schedule_code="GS_TEST002",
            demo_mode=True,
            db=db_session,
        )

        # 验证错误响应
        assert result["code"] == 40001
        assert "调度失败" in result["message"]


class TestGetDispatchBatches:
    """测试 get_dispatch_batches 服务"""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_empty(self, db_session):
        """空数据库 → 返回空列表"""
        result = await DispatchService.get_dispatch_batches(
            schedule_code=None,
            status=None,
            db=db_session,
        )

        assert result["code"] == 0
        data = result["data"]
        assert data["total"] == 0
        assert data["items"] == []

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_with_data(self, db_session, test_nodes, test_vehicles):
        """有数据 → 返回批次列表"""
        # 创建测试数据
        from models.global_schedule import GlobalSchedule
        schedule = GlobalSchedule(
            schedule_code="GS_TEST003",
            order_codes=["O001"],
            goods_schedules=[],
            total_distance=0,
            total_time=0,
            total_goods=0,
            score=0,
        )
        db_session.add(schedule)
        db_session.flush()

        # 创建批次
        batch = DispatchBatch(
            batch_code="BATCH_TEST001",
            global_schedule_id=schedule.id,
            status="completed",
            demo_mode=True,
            l0_l1_dispatch_count=2,
            l1_l2_dispatch_count=3,
            unallocated_packages=json.dumps(["PKG001", "PKG002"], ensure_ascii=False),
        )
        db_session.add(batch)
        db_session.commit()

        # 查询
        result = await DispatchService.get_dispatch_batches(
            schedule_code=None,
            status=None,
            db=db_session,
        )

        assert result["code"] == 0
        data = result["data"]
        assert data["total"] == 1
        assert len(data["items"]) == 1
        item = data["items"][0]
        assert item["batch_code"] == "BATCH_TEST001"
        assert item["status"] == "completed"
        assert item["l0_l1_dispatch_count"] == 2
        assert item["l1_l2_dispatch_count"] == 3

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_filter_by_status(self, db_session):
        """按状态筛选"""
        # 创建测试数据
        from models.global_schedule import GlobalSchedule
        schedule = GlobalSchedule(
            schedule_code="GS_TEST004",
            order_codes=["O001"],
            goods_schedules=[],
            total_distance=0,
            total_time=0,
            total_goods=0,
            score=0,
        )
        db_session.add(schedule)
        db_session.flush()

        # 创建两个批次（不同状态）
        batch1 = DispatchBatch(
            batch_code="BATCH_TEST002",
            global_schedule_id=schedule.id,
            status="l0_l1_done",
            demo_mode=False,
            l0_l1_dispatch_count=1,
            l1_l2_dispatch_count=0,
        )
        batch2 = DispatchBatch(
            batch_code="BATCH_TEST003",
            global_schedule_id=schedule.id,
            status="completed",
            demo_mode=True,
            l0_l1_dispatch_count=1,
            l1_l2_dispatch_count=1,
        )
        db_session.add_all([batch1, batch2])
        db_session.commit()

        # 按 status='completed' 筛选
        result = await DispatchService.get_dispatch_batches(
            schedule_code=None,
            status="completed",
            db=db_session,
        )

        assert result["code"] == 0
        data = result["data"]
        assert data["total"] == 1
        assert data["items"][0]["batch_code"] == "BATCH_TEST003"


class TestGetDispatchBatchDetail:
    """测试 get_dispatch_batch_detail 服务"""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_detail_success(self, db_session):
        """正常获取批次详情"""
        # 创建测试数据
        from models.global_schedule import GlobalSchedule
        schedule = GlobalSchedule(
            schedule_code="GS_TEST005",
            order_codes=["O001"],
            goods_schedules=[],
            total_distance=0,
            total_time=0,
            total_goods=0,
            score=0,
        )
        db_session.add(schedule)
        db_session.flush()

        # 创建批次
        batch = DispatchBatch(
            batch_code="BATCH_TEST004",
            global_schedule_id=schedule.id,
            status="completed",
            demo_mode=True,
            l0_l1_dispatch_count=1,
            l1_l2_dispatch_count=1,
            unallocated_packages=json.dumps(["PKG001", "PKG002"], ensure_ascii=False),
        )
        db_session.add(batch)
        db_session.flush()

        # 创建调度明细
        vehicle = db_session.query(Vehicle).first()
        driver = db_session.query(Driver).first()
        
        dispatch = NodeDispatch(
            dispatch_code="DISP_TEST001",
            dispatch_batch_id=batch.id,
            level_phase=0,
            vehicle_id=vehicle.id if vehicle else 1,
            driver_id=driver.id if driver else None,
            tasks=[
                {
                    "from_node_code": "SC001",
                    "to_node_code": "SO001",
                    "package_codes": ["PKG001"],
                    "is_return": False
                }
            ],
            total_distance=15.2,
            total_time=0.5,
        )
        db_session.add(dispatch)
        db_session.commit()

        # 查询详情
        result = await DispatchService.get_dispatch_batch_detail(
            batch_code="BATCH_TEST004",
            db=db_session,
        )

        # 验证
        assert result["code"] == 0
        data = result["data"]
        assert data["batch_code"] == "BATCH_TEST004"
        assert data["status"] == "completed"
        assert "unallocated_packages" in data
        assert len(data["unallocated_packages"]) == 2
        assert "PKG001" in data["unallocated_packages"]
        assert len(data["dispatches"]) == 1
        assert data["dispatches"][0]["dispatch_code"] == "DISP_TEST001"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_detail_with_unallocated(self, db_session):
        """批次详情包含 unallocated_packages"""
        # 创建测试数据
        from models.global_schedule import GlobalSchedule
        schedule = GlobalSchedule(
            schedule_code="GS_TEST006",
            order_codes=["O001"],
            goods_schedules=[],
            total_distance=0,
            total_time=0,
            total_goods=0,
            score=0,
        )
        db_session.add(schedule)
        db_session.flush()

        # 创建批次（有未分配包裹）
        unallocated = ["PKG001", "PKG002", "PKG003"]
        batch = DispatchBatch(
            batch_code="BATCH_TEST005",
            global_schedule_id=schedule.id,
            status="completed",
            demo_mode=True,
            l0_l1_dispatch_count=1,
            l1_l2_dispatch_count=1,
            unallocated_packages=json.dumps(unallocated, ensure_ascii=False),
        )
        db_session.add(batch)
        db_session.commit()

        # 查询详情
        result = await DispatchService.get_dispatch_batch_detail(
            batch_code="BATCH_TEST005",
            db=db_session,
        )

        # 验证 unallocated_packages
        assert result["code"] == 0
        data = result["data"]
        assert len(data["unallocated_packages"]) == 3
        assert data["unallocated_packages"] == unallocated

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_detail_not_found(self, db_session):
        """批次不存在 → 返回错误"""
        result = await DispatchService.get_dispatch_batch_detail(
            batch_code="BATCH_NONEXIST",
            db=db_session,
        )

        assert result["code"] == 40402
        assert "不存在" in result["message"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_detail_no_unallocated(self, db_session):
        """批次详情（无未分配包裹）"""
        # 创建测试数据
        from models.global_schedule import GlobalSchedule
        schedule = GlobalSchedule(
            schedule_code="GS_TEST007",
            order_codes=["O001"],
            goods_schedules=[],
            total_distance=0,
            total_time=0,
            total_goods=0,
            score=0,
        )
        db_session.add(schedule)
        db_session.flush()

        # 创建批次（无未分配包裹）
        batch = DispatchBatch(
            batch_code="BATCH_TEST006",
            global_schedule_id=schedule.id,
            status="completed",
            demo_mode=True,
            l0_l1_dispatch_count=1,
            l1_l2_dispatch_count=1,
            unallocated_packages=None,  # 无未分配包裹
        )
        db_session.add(batch)
        db_session.commit()

        # 查询详情
        result = await DispatchService.get_dispatch_batch_detail(
            batch_code="BATCH_TEST006",
            db=db_session,
        )

        # 验证 unallocated_packages 为空列表
        assert result["code"] == 0
        data = result["data"]
        assert data["unallocated_packages"] == []
>>>>>>> backend/phase-5:src/backend/tests/test_services/test_dispatch_service.py
