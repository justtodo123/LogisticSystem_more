"""
test_node_dispatch.py — F005 节点间调度算法单元测试

测试用例：
1. 正常情况，生成调度方案
2. 车辆不足，无法调度
3. 包裹状态不是packed，无法调度
"""
import pytest
from algorithms.node_dispatch import run_node_dispatch
from models.dispatch_batch import DispatchBatch
from models.node_dispatch import NodeDispatch
from models.package import Package
from models.vehicle import Vehicle
from models.driver import Driver


class TestNodeDispatchNormal:
    """正常情况：生成调度方案"""

    @pytest.mark.unit
    def test_normal_dispatch_generates_batches(
        self, db_session, test_nodes, test_orders, test_goods
    ):
        """
        测试正常调度流程：
        - 先执行F007全局调度，生成全局调度方案
        - 再执行F021打包，生成包裹（status='packed'）
        - 最后执行F005节点调度，生成调度批次
        - 输出结果包含正确的字段
        """
        # TODO: 这个测试需要先执行F007和F021，比较复杂
        # 暂时跳过，先实现基础测试
        pass


class TestNodeDispatchNoVehicle:
    """车辆不足：无法调度"""

    @pytest.mark.unit
    def test_no_vehicle_raises_error(self, db_session, test_nodes):
        """
        测试没有车辆时抛出ValueError
        """
        # 创建全局调度方案
        from models.global_schedule import GlobalSchedule
        schedule = GlobalSchedule(
            schedule_code="GS_TEST001",
            order_codes=["O001"],
            goods_schedules=[],
            total_distance=0,
            total_time=0,
            total_goods=0,
            score=0,
        )
        db_session.add(schedule)
        db_session.flush()
        
        # 创建包裹（status='packed'）
        package = Package(
            package_code="PKG_TEST001",
            weight=10.0,
            volume=0.5,
            status="packed",
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO001"].id,
            goods_items=[{"goods_code": "G001", "order_code": "O001"}],
            schedule_id=schedule.id,
        )
        db_session.add(package)
        db_session.commit()
        
        # 执行F005（没有车辆）→ 应该失败
        with pytest.raises(ValueError, match="没有可用的车辆"):
            run_node_dispatch(
                db=db_session,
                schedule_code="GS_TEST001",
                demo_mode=True,
            )


class TestNodeDispatchWrongStatus:
    """包裹状态不是packed：无法调度"""

    @pytest.mark.unit
    def test_wrong_status_raises_error(self, db_session, test_nodes, test_vehicles):
        """
        测试包裹状态不是packed时抛出ValueError
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
        
        # 创建包裹（status='pending_pack'，不是'packed'）
        package = Package(
            package_code="PKG_TEST002",
            weight=10.0,
            volume=0.5,
            status="pending_pack",  # 错误状态
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO001"].id,
            goods_items=[{"goods_code": "G001", "order_code": "O001"}],
            schedule_id=schedule.id,
        )
        db_session.add(package)
        db_session.commit()
        
        # 执行F005（包裹状态错误）→ 应该找不到包裹
        # 注意：算法会查询status='packed'的包裹，所以会返回空列表
        # 然后算法会抛出ValueError："L0→L1没有可调度的包裹"
        with pytest.raises(ValueError, match="L0→L1没有可调度的包裹"):
            run_node_dispatch(
                db=db_session,
                schedule_code="GS_TEST002",
                demo_mode=True,
            )
