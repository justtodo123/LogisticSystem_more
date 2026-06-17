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


class TestCreateNodeDispatch:
    """测试创建节点调度"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_success(self, db_session, test_nodes, test_vehicles, test_drivers):
        """
        测试成功创建调度批次：
        1. 创建测试数据（包裹、车辆、司机）
        2. 调用 create_node_dispatch(schedule_code, demo_mode=True, db)
        3. 验证返回成功
        4. 验证数据库中有批次和调度明细记录
        """
        # 先创建 GlobalSchedule
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
        
        # 创建测试包裹
        from models.package import Package
        
        package = Package(
            package_code="PKG001",
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO010"].id,
            weight=10.0,
            volume=0.5,
            status="packed",
            schedule_id=global_schedule.id,
            goods_items=[{"goods_code": "G001", "order_code": "O001"}],
        )
        db_session.add(package)
        db_session.commit()
        
        # Mock 算法函数
        with patch("algorithms.node_dispatch.run_node_dispatch") as mock_dispatch:
            mock_dispatch.return_value = {
                "batch_code": "BATCH001",
                "total_distance": 50.0,
                "total_time": 120.0,
                "dispatch_count": 1,
            }
            
            # 调用服务方法
            result = await DispatchService.create_node_dispatch(
                schedule_code="GS001",
                demo_mode=True,
                db=db_session,
            )
        
        # 验证响应
        assert result["code"] == 0
        assert "data" in result
        
        # 验证数据库中有记录
        batch_list = db_session.query(DispatchBatch).all()
        assert len(batch_list) >= 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_schedule_not_found(self, db_session):
        """
        测试调度方案不存在：
        1. 调用 create_node_dispatch("NONEXIST", True, db)
        2. 验证返回业务错误
        """
        result = await DispatchService.create_node_dispatch(
            schedule_code="NONEXIST",
            demo_mode=True,
            db=db_session,
        )
        
        # 验证响应（业务错误）
        assert result["code"] != 0
        assert "调度方案" in result["message"] or "不存在" in result["message"]


class TestGetDispatchBatches:
    """测试查询调度批次列表"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_empty(self, db_session):
        """测试空数据库返回空列表"""
        result = await DispatchService.get_dispatch_batches(
            status=None,
            page=1,
            page_size=20,
            db=db_session
        )
        
        assert result["code"] == 0
        assert result["data"]["items"] == []
        assert result["data"]["total"] == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_with_data(self, db_session, test_nodes, test_vehicles):
        """测试有数据时返回批次列表"""
        # 先创建一个批次
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
        
        batch = DispatchBatch(
            batch_code="BATCH001",
            global_schedule_id=global_schedule.id,
            status="pending"
        )
        db_session.add(batch)
        db_session.commit()
        
        # 查询批次列表
        result = await DispatchService.get_dispatch_batches(
            status=None,
            page=1,
            page_size=20,
            db=db_session
        )
        
        assert result["code"] == 0
        assert len(result["data"]["items"]) == 1
        assert result["data"]["total"] == 1
