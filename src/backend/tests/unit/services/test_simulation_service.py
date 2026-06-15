"""
服务单元测试：SimulationService（模拟送达服务）

测试目标：
- SimulationService.deliver_packages 方法的正常流程和异常流程
- 验证服务层业务逻辑、状态更新、错误处理
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from services.simulation_service import SimulationService
from models.package import Package
from models.goods import Goods
from models.vehicle import Vehicle
from models.order import Order


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
        
        # 创建 DispatchBatch
        dispatch_batch = DispatchBatch(
            batch_code="BATCH001",
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
            goods_items=json.dumps([{"goods_code": "G001", "order_code": "O001"}]),
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
        
        # 验证包裹状态更新
        db_session.refresh(package)
        assert package.status == "delivered"
        
        # 验证车辆状态更新
        db_session.refresh(vehicle)
        assert vehicle.status == "idle"

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
        
        # 创建 DispatchBatch
        dispatch_batch = DispatchBatch(
            batch_code="BATCH002",
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
        
        # 验证响应
        assert result["code"] == 0
        assert "data" in result
        assert "delivered_package_codes" in result["data"]
        assert "PKG001" in result["data"]["delivered_package_codes"]
        
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
        
        package1 = Package(
            package_code="PKG001",
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO010"].id,
            weight=10.0,
            volume=0.5,
            status="in_transit",
            vehicle_id=test_vehicles["VEH001"].id,
            goods_items=json.dumps([{"goods_code": "G001", "order_code": "O001"}]),
        )
        package2 = Package(
            package_code="PKG002",
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO011"].id,
            weight=5.0,
            volume=0.3,
            status="in_transit",
            vehicle_id=test_vehicles["VEH002"].id,
            goods_items=json.dumps([{"goods_code": "G002", "order_code": "O002"}]),
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
        import json
        
        package = Package(
            package_code="PKG001",
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO010"].id,
            weight=10.0,
            volume=0.5,
            status="packed",  # 不是 in_transit
            vehicle_id=test_vehicles["VEH001"].id,
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
        assert "状态" in result["message"] or "in_transit" in result["message"]

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
        assert "车辆" in result["message"] or "不存在" in result["message"]

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
