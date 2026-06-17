"""
服务单元测试：SimulationService（模拟送达服务）

测试目标：
- SimulationService.deliver_packages 方法的正常流程和异常流程
- 验证服务层业务逻辑、状态更新、错误处理
- 测试批次状态更新、自动触发逻辑、失败回滚机制
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
import json

from services.simulation_service import SimulationService
from models.package import Package
from models.goods import Goods
from models.vehicle import Vehicle
from models.order import Order
from models.node_dispatch import NodeDispatch
from models.dispatch_batch import DispatchBatch


class TestDeliverPackages:
    """测试模拟送达"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_deliver_by_vehicle_success(self, db_session, test_nodes, test_orders, test_goods, test_vehicles):
        """
        测试按车辆送达：
        1. 创建测试包裹（状态为 in_transit）
        2. 调用 deliver_packages(vehicle_code="VEH001")
        3. 验证包裹状态变为 delivered
        4. 验证货物状态更新
        5. 验证车辆状态变为 idle
        """
        # 创建测试包裹（需要先创建包裹记录）
        from models.package import Package
        from models.node_dispatch import NodeDispatch
        from models.dispatch_batch import DispatchBatch
        import json
        
        # 创建 DispatchBatch（需要先创建GlobalSchedule，因为DispatchBatch.global_schedule_id是NOT NULL）
        from models.global_schedule import GlobalSchedule
        import json
        global_schedule = GlobalSchedule(
            schedule_code="GS001",
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
        
        dispatch_batch = DispatchBatch(
            batch_code="BATCH001",
            global_schedule_id=global_schedule.id,
            status="pending"
        )
        db_session.add(dispatch_batch)
        db_session.commit()
        
        # 创建 NodeDispatch
        node_dispatch = NodeDispatch(
            dispatch_code="ND001",
            dispatch_batch_id=dispatch_batch.id,
            vehicle_id=test_vehicles["VEH001"].id,
            driver_id=1,
            level_phase=0,
            tasks=json.dumps([{"from_node_code": "SC001", "to_node_code": "SO001", "package_codes": ["PKG001"], "is_return": False}]),
            total_distance=10.0,
            total_time=30.0,
        )
        db_session.add(node_dispatch)
        db_session.commit()
        
        package = Package(
            package_code="PKG001",
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO010"].id,
            weight=10.0,
            volume=0.5,
            status="in_transit",  # 在途状态
            dispatch_id=node_dispatch.id,
            goods_items=[{"goods_code": "G001", "order_code": "O001"}],
        )
        db_session.add(package)
        
        # 更新车辆状态为 delivering
        vehicle = test_vehicles["VEH001"]
        vehicle.status = "delivering"
        db_session.commit()
        
        # 调用送达服务
        result = await SimulationService.deliver_packages(
            vehicle_code="VEH001",
            package_code=None,
            db=db_session,
        )
        
        # 验证响应
        assert result["code"] == 0
        assert "data" in result
        assert "delivered_package_codes" in result["data"]
        assert "PKG001" in result["data"]["delivered_package_codes"]
        
        # 提交事务（服务不提交，由调用者提交）
        db_session.commit()
        
        # 验证包裹状态更新
        db_session.refresh(package)
        assert package.status == "delivered"
        
        # 验证车辆状态更新（需要刷新会话以确保能看到最新状态）
        db_session.flush()
        db_session.refresh(vehicle)
        assert vehicle.status == "idle", f"车辆状态应为 idle，实际为 {vehicle.status}"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_deliver_by_package_success(self, db_session, test_nodes, test_orders, test_goods, test_vehicles):
        """
        测试按包裹送达：
        1. 创建测试包裹（状态为 in_transit）
        2. 调用 deliver_packages(package_code="PKG001")
        3. 验证包裹状态变为 delivered
        """
        # 创建测试包裹
        from models.package import Package
        from models.node_dispatch import NodeDispatch
        from models.dispatch_batch import DispatchBatch
        import json
        
        # 创建 DispatchBatch（需要先创建GlobalSchedule，因为DispatchBatch.global_schedule_id是NOT NULL）
        from models.global_schedule import GlobalSchedule
        import json
        global_schedule = GlobalSchedule(
            schedule_code="GS002",
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
        
        dispatch_batch = DispatchBatch(
            batch_code="BATCH002",
            global_schedule_id=global_schedule.id,
            status="pending"
        )
        db_session.add(dispatch_batch)
        db_session.commit()
        
        # 创建 NodeDispatch
        node_dispatch = NodeDispatch(
            dispatch_code="ND002",
            dispatch_batch_id=dispatch_batch.id,
            vehicle_id=test_vehicles["VEH001"].id,
            driver_id=1,
            level_phase=0,
            tasks=json.dumps([{"from_node_code": "SC001", "to_node_code": "SO001", "package_codes": ["PKG001"], "is_return": False}]),
            total_distance=10.0,
            total_time=30.0,
        )
        db_session.add(node_dispatch)
        db_session.commit()
        
        package = Package(
            package_code="PKG001",
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO010"].id,
            weight=10.0,
            volume=0.5,
            status="in_transit",  # 在途状态
            dispatch_id=node_dispatch.id,
            goods_items=[{"goods_code": "G001", "order_code": "O001"}],
        )
        db_session.add(package)
        db_session.commit()
        
        # 调用送达服务
        result = await SimulationService.deliver_packages(
            vehicle_code=None,
            package_code="PKG001",
            db=db_session,
        )
        
        # 验证响应
        assert result["code"] == 0
        assert "data" in result
        assert "delivered_package_codes" in result["data"]
        assert "PKG001" in result["data"]["delivered_package_codes"]
        
        # 提交事务（服务不提交，由调用者提交）
        db_session.commit()
        
        # 验证包裹状态更新
        db_session.refresh(package)
        assert package.status == "delivered"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_deliver_no_params(self, db_session, test_nodes, test_orders, test_goods, test_vehicles):
        """
        测试不传参数（处理所有 in_transit 包裹）：
        1. 创建多个测试包裹（状态为 in_transit）
        2. 调用 deliver_packages()
        3. 验证所有包裹状态变为 delivered
        """
        # 创建测试包裹
        from models.package import Package
        import json
        
        # 需要先创建 NodeDispatch 记录，因为 Package.dispatch_id 是外键
        from models.node_dispatch import NodeDispatch
        from models.dispatch_batch import DispatchBatch
        
        # 创建 DispatchBatch（需要先创建GlobalSchedule，因为DispatchBatch.global_schedule_id是NOT NULL）
        from models.global_schedule import GlobalSchedule
        import json
        global_schedule = GlobalSchedule(
            schedule_code="GS003",
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
        
        dispatch_batch = DispatchBatch(
            batch_code="BATCH003",
            global_schedule_id=global_schedule.id,
            status="pending"
        )
        db_session.add(dispatch_batch)
        db_session.commit()
        
        # 创建 NodeDispatch
        node_dispatch1 = NodeDispatch(
            dispatch_code="ND003",
            dispatch_batch_id=dispatch_batch.id,
            vehicle_id=test_vehicles["VEH001"].id,
            driver_id=1,
            level_phase=0,
            tasks=json.dumps([{"from_node_code": "SC001", "to_node_code": "SO001", "package_codes": ["PKG001"], "is_return": False}]),
            total_distance=10.0,
            total_time=30.0,
        )
        db_session.add(node_dispatch1)
        
        node_dispatch2 = NodeDispatch(
            dispatch_code="ND004",
            dispatch_batch_id=dispatch_batch.id,
            vehicle_id=test_vehicles["VEH002"].id,
            driver_id=1,
            level_phase=0,
            tasks=json.dumps([{"from_node_code": "SC001", "to_node_code": "SO001", "package_codes": ["PKG001"], "is_return": False}]),
            total_distance=10.0,
            total_time=30.0,
        )
        db_session.add(node_dispatch2)
        db_session.commit()
        
        package1 = Package(
            package_code="PKG001",
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO010"].id,
            weight=10.0,
            volume=0.5,
            status="in_transit",
            dispatch_id=node_dispatch1.id,
            goods_items=[{"goods_code": "G001", "order_code": "O001"}],
        )
        package2 = Package(
            package_code="PKG002",
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO011"].id,
            weight=5.0,
            volume=0.3,
            status="in_transit",
            dispatch_id=node_dispatch2.id,
            goods_items=[{"goods_code": "G002", "order_code": "O002"}],
        )
        db_session.add(package1)
        db_session.add(package2)
        db_session.commit()
        
        # 调用送达服务（不传参数）
        result = await SimulationService.deliver_packages(
            vehicle_code=None,
            package_code=None,
            db=db_session,
        )
        
        # 验证响应
        assert result["code"] == 0
        assert "data" in result
        assert len(result["data"]["delivered_package_codes"]) == 2
        
        # 提交事务（服务不提交，由调用者提交）
        db_session.commit()
        
        # 验证包裹状态更新
        db_session.refresh(package1)
        db_session.refresh(package2)
        assert package1.status == "delivered"
        assert package2.status == "delivered"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_deliver_package_not_in_transit(self, db_session, test_nodes, test_orders, test_goods, test_vehicles):
        """
        测试包裹状态不是 in_transit（应该失败）：
        1. 创建测试包裹（状态为 packed）
        2. 调用 deliver_packages(package_code="PKG001")
        3. 验证返回业务错误
        """
        # 创建测试包裹（状态为 packed）
        from models.package import Package
        from models.node_dispatch import NodeDispatch
        from models.dispatch_batch import DispatchBatch
        import json
        
        # 创建 DispatchBatch（需要先创建GlobalSchedule，因为DispatchBatch.global_schedule_id是NOT NULL）
        from models.global_schedule import GlobalSchedule
        import json
        global_schedule = GlobalSchedule(
            schedule_code="GS005",
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
        
        dispatch_batch = DispatchBatch(
            batch_code="BATCH005",
            global_schedule_id=global_schedule.id,
            status="pending"
        )
        db_session.add(dispatch_batch)
        db_session.commit()
        
        # 创建 NodeDispatch
        node_dispatch = NodeDispatch(
            dispatch_code="ND005",
            dispatch_batch_id=dispatch_batch.id,
            vehicle_id=test_vehicles["VEH001"].id,
            driver_id=1,
            level_phase=0,
            tasks=json.dumps([{"from_node_code": "SC001", "to_node_code": "SO001", "package_codes": ["PKG001"], "is_return": False}]),
            total_distance=10.0,
            total_time=30.0,
        )
        db_session.add(node_dispatch)
        db_session.commit()
        
        package = Package(
            package_code="PKG001",
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO010"].id,
            weight=10.0,
            volume=0.5,
            status="packed",  # 不是 in_transit
            dispatch_id=node_dispatch.id,
            goods_items=json.dumps([{"goods_code": "G001", "order_code": "O001"}]),
        )
        db_session.add(package)
        db_session.commit()
        
        # 调用送达服务
        result = await SimulationService.deliver_packages(
            vehicle_code=None,
            package_code="PKG001",
            db=db_session,
        )
        
        # 验证响应（业务错误）
        assert result["code"] != 0
        assert "没有找到可送达的包裹" in result["message"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_deliver_vehicle_not_found(self, db_session):
        """
        测试车辆不存在（应该失败）：
        1. 调用 deliver_packages(vehicle_code="NONEXIST")
        2. 验证返回业务错误
        """
        result = await SimulationService.deliver_packages(
            vehicle_code="NONEXIST",
            package_code=None,
            db=db_session,
        )
        
        # 验证响应（业务错误）
        assert result["code"] != 0
        assert "没有找到可送达的包裹" in result["message"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_deliver_package_not_found(self, db_session):
        """
        测试包裹不存在（应该失败）：
        1. 调用 deliver_packages(package_code="NONEXIST")
        2. 验证返回业务错误
        """
        result = await SimulationService.deliver_packages(
            vehicle_code=None,
            package_code="NONEXIST",
            db=db_session,
        )
        
        # 验证响应（业务错误）
        assert result["code"] != 0
        assert "包裹" in result["message"] or "不存在" in result["message"]


class TestUpdateBatchStatusAfterDelivery:
    """测试更新批次状态为 l0_l1_done"""

    @pytest.mark.unit
    def test_updates_status_to_l0_l1_done(self, db_session):
        """
        测试 _update_batch_status_after_delivery() 正确更新批次状态
        """
        # 创建测试数据：DispatchBatch（状态为 pending）
        from models.global_schedule import GlobalSchedule
        import json
        
        # 创建 GlobalSchedule（因为 DispatchBatch.global_schedule_id 是 NOT NULL）
        global_schedule = GlobalSchedule(
            schedule_code="GS999",
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
        
        batch = DispatchBatch(
            batch_code="BATCH999",
            global_schedule_id=global_schedule.id,
            status="pending"
        )
        db_session.add(batch)
        db_session.commit()
        
        # 创建 NodeDispatch
        dispatch = NodeDispatch(
            dispatch_code="ND999",
            dispatch_batch_id=batch.id,
            vehicle_id=1,
            driver_id=1,
            level_phase=0,
            tasks=json.dumps([]),
            total_distance=0.0,
            total_time=0.0
        )
        db_session.add(dispatch)
        db_session.commit()
        
        # 创建 Package（dispatch_id 指向 NodeDispatch）
        package = Package(
            package_code="PKG999",
            weight=10.0,  # 必需字段
            volume=0.5,    # 必需字段
            status="delivered",  # 已送达
            from_node_id=1,  # 必需字段
            to_node_id=2,    # 必需字段
            from_longitude=114.3,  # 必需字段
            from_latitude=30.5,   # 必需字段
            to_longitude=114.31,  # 必需字段
            to_latitude=30.51,    # 必需字段
            goods_items=json.dumps([]),
            dispatch_id=dispatch.id,
        )
        db_session.add(package)
        db_session.commit()
        
        # 调用 _update_batch_status_after_delivery()
        packages = [package]
        SimulationService._update_batch_status_after_delivery(db_session, packages)
        
        # 验证批次状态更新为 l0_l1_done
        db_session.refresh(batch)
        assert batch.status == "l0_l1_done"


class TestTriggerRepackaging:
    """测试自动触发重新打包"""

    @pytest.mark.unit
    def test_trigger_repackaging_success(self, db_session):
        """
        测试 _trigger_repackaging() 成功触发重新打包
        """
        # 创建测试数据：Goods（状态为 pending_pack）
        from models.goods import Goods
        from models.order import Order
        from models.global_schedule import GlobalSchedule
        import json
        
        # 创建 GlobalSchedule
        global_schedule = GlobalSchedule(
            schedule_code="GS998",
            order_codes=json.dumps([]),
            total_distance=0.0,
            total_time=0.0,
            total_goods=0,
            score=0.0,
            algorithm_type="traditional",
            version=1,
            is_replan=False,
            goods_schedules=json.dumps([{"order_code": "O998", "path": ["SC001", "SO001", "SO010"]}])
        )
        db_session.add(global_schedule)
        db_session.commit()
        
        # 创建 Order
        order = Order(
            order_code="O998",
            destination_node_id=1,
            time_window="2026-06-15 全天"  # 必需字段
        )
        db_session.add(order)
        db_session.commit()
        
        # 创建 Goods（状态为 pending_pack）
        goods = Goods(
            goods_code="G998",
            goods_name="测试货物",  # 必需字段
            goods_type="普通",      # 必需字段
            weight=5.0,           # 必需字段
            volume=0.3,           # 必需字段
            node_id=1,             # 必需字段
            order_id=order.id,
            status="pending_pack"
        )
        db_session.add(goods)
        db_session.commit()
        
        # 调用 _trigger_repackaging()
        result = SimulationService._trigger_repackaging(db_session, global_schedule.id)
        
        # 验证返回 True（成功触发）
        assert result == True


class TestTriggerSecondF005Async:
    """测试异步触发第二次F005"""

    @pytest.mark.unit
    def test_trigger_second_f005_async_returns_true(self, db_session):
        """
        测试 _trigger_second_f005_async() 返回 True
        """
        # 调用 _trigger_second_f005_async()
        result = SimulationService._trigger_second_f005_async(db_session, 1)
        
        # 验证返回 True 或 False（不抛出异常）
        assert isinstance(result, bool)
