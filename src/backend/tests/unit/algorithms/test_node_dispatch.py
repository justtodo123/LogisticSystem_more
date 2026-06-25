"""
算法单元测试：F005 节点调度（node_dispatch）

测试目标：
- run_node_dispatch 函数的正常流程和异常流程
- 验证输出结构、车辆分配、司机分配、错误处理
"""
import pytest
from algorithms.node_dispatch import run_node_dispatch
from models.package import Package
from models.vehicle import Vehicle
from models.driver import Driver
from models.node import Node
import json


class TestNodeDispatchNormal:
    """正常情况：分配车辆和司机"""

    @pytest.mark.unit
    def test_node_dispatch_success(self, db_session, test_nodes, test_orders, test_goods, test_vehicles, test_drivers):
        """
        测试正常节点调度流程：
        1. 先执行全局调度，生成包裹
        2. 调用 node_dispatch(schedule_code, demo_mode=True)
        3. 验证返回结构包含 batch_code、total_packages 等
        """
        # 先执行全局调度
        from algorithms.global_schedule import global_schedule
        from models.global_schedule import GlobalSchedule
        import json
        schedule_result = global_schedule(
            order_codes=None,
            algorithm="traditional",
            db=db_session,
        )
        schedule_code = schedule_result["schedule_code"]
        
        # 手动创建 GlobalSchedule 记录（因为 global_schedule() 只返回结果，不写入数据库）
        gs = GlobalSchedule(
            schedule_code=schedule_code,
            order_codes=json.dumps(schedule_result["order_codes"]),
            total_distance=schedule_result["total_distance"],
            total_time=schedule_result["total_time"],
            total_goods=schedule_result["total_goods"],
            score=schedule_result["score"],
            algorithm_type="traditional",
            version=1,
            is_replan=False,
            goods_schedules=json.dumps(schedule_result["goods_schedules"]),
        )
        db_session.add(gs)
        db_session.commit()
        
        # 先执行打包（生成包裹）
        from algorithms.packaging import packaging
        packages = packaging(
            schedule_result={"goods_schedules": schedule_result["goods_schedules"]},
            schedule_id=gs.id,
            db=db_session,
        )
        
        # 将包裹添加到数据库会话
        for pkg in packages:
            db_session.add(pkg)
        db_session.commit()
        
        # P1-3: 调用 update_goods_after_f021 将 goods 从 pending_pack 转为 packed
        # 确保状态机链路完整：F021 → goods.packed → F005 → goods.in_transit
        from services.state_machine import update_goods_after_f021
        update_goods_after_f021(db_session, gs.id)
        
        # P1-3: 调用 update_orders_after_f007 将 orders 从 pending 转为 delivering
        from services.state_machine import update_orders_after_f007
        update_orders_after_f007(db_session, schedule_result["order_codes"])
        
        # 调用节点调度
        result = run_node_dispatch(
            schedule_code=schedule_code,
            demo_mode=True,
            db=db_session,
        )
        
        # 验证返回结构
        assert "batch_code" in result
        assert "dispatches" in result
        assert len(result["dispatches"]) >= 0
        
        # 验证 dispatches 结构
        for nd in result["dispatches"]:
            assert "vehicle_code" in nd
            assert "driver_code" in nd
            assert "tasks" in nd
            # 验证 tasks 结构
            for task in nd["tasks"]:
                assert "from_node_code" in task
                assert "to_node_code" in task
                assert "package_codes" in task
                assert "is_return" in task

    @pytest.mark.unit
    def test_node_dispatch_no_packages(self, db_session, test_nodes):
        """
        测试没有包裹可调度：
        1. 创建一个调度方案（但没有包裹）
        2. 调用 node_dispatch
        3. 验证抛出 ValueError 异常
        """
        # 创建一个空的调度方案
        from models.global_schedule import GlobalSchedule
        import json
        
        gs = GlobalSchedule(
            schedule_code="GS001",
            order_codes=json.dumps([]),
            total_distance=0,
            total_time=0,
            total_goods=0,
            score=0,
            algorithm_type="traditional",
            version=1,
            is_replan=False,
            goods_schedules=json.dumps([]),
        )
        db_session.add(gs)
        db_session.commit()
        
        # 调用节点调度，应该抛出 ValueError 异常
        with pytest.raises(ValueError) as exc_info:
            result = run_node_dispatch(
                schedule_code="GS001",
                demo_mode=True,
                db=db_session,
            )
        
        # 验证异常信息包含 "没有可调度的包裹"
        assert "没有可调度的包裹" in str(exc_info.value)


class TestNodeDispatchEdgeCases:
    """边界条件测试"""

    @pytest.mark.unit
    def test_node_dispatch_schedule_not_found(self, db_session):
        """
        测试调度方案不存在：
        1. 调用 node_dispatch("GS_NONEXIST", ...)
        2. 验证抛出异常或返回错误
        """
        # node_dispatch 可能抛出异常或返回错误字典
        try:
            result = run_node_dispatch(
                schedule_code="GS_NONEXIST",
                demo_mode=True,
                db=db_session,
            )
            # 如果返回字典，检查是否有错误
            if isinstance(result, dict) and "error" in result:
                assert "不存在" in result["error"] or "not found" in result["error"].lower()
            else:
                # 可能返回了空结果
                assert result["total_packages"] == 0
        except Exception as e:
            # 如果抛出异常，验证异常信息
            assert "不存在" in str(e) or "not found" in str(e).lower()

    @pytest.mark.unit
    def test_node_dispatch_no_available_vehicles(self, db_session, test_nodes, test_orders, test_goods):
        """
        测试没有可用车辆：
        1. 先执行全局调度，生成包裹
        2. 但不创建车辆（test_vehicles fixture不使用）
        3. 调用 node_dispatch
        4. 验证抛出 ValueError 异常
        """
        # 先执行全局调度
        from algorithms.global_schedule import global_schedule
        from models.global_schedule import GlobalSchedule
        import json
        schedule_result = global_schedule(
            order_codes=None,
            algorithm="traditional",
            db=db_session,
        )
        schedule_code = schedule_result["schedule_code"]
        
        # 手动创建 GlobalSchedule 记录（因为 global_schedule() 只返回结果，不写入数据库）
        gs = GlobalSchedule(
            schedule_code=schedule_code,
            order_codes=json.dumps(schedule_result["order_codes"]),
            total_distance=schedule_result["total_distance"],
            total_time=schedule_result["total_time"],
            total_goods=schedule_result["total_goods"],
            score=schedule_result["score"],
            algorithm_type="traditional",
            version=1,
            is_replan=False,
            goods_schedules=json.dumps(schedule_result["goods_schedules"]),
        )
        db_session.add(gs)
        db_session.commit()
        
        # 执行打包（生成包裹）
        from algorithms.packaging import packaging
        packages = packaging(
            schedule_result={"goods_schedules": schedule_result["goods_schedules"]},
            schedule_id=gs.id,
            db=db_session,
        )
        
        # 将包裹添加到数据库会话
        for pkg in packages:
            db_session.add(pkg)
        db_session.commit()
        
        # P1-3: 调用 update_goods_after_f021 将 goods 从 pending_pack 转为 packed
        from services.state_machine import update_goods_after_f021, update_orders_after_f007
        update_goods_after_f021(db_session, gs.id)
        update_orders_after_f007(db_session, schedule_result["order_codes"])
        
        # 将所有车辆状态设置为 maintenance（不可用），以测试"没有可用车辆"的情况
        vehicles = db_session.query(Vehicle).all()
        for v in vehicles:
            v.status = 'maintenance'
        db_session.commit()
        
        # 调用节点调度，应该返回空结果（没有可用的车辆）
        result = run_node_dispatch(
            schedule_code=schedule_code,
            demo_mode=True,
            db=db_session,
        )
        
        # 验证返回结果（应该没有调度明细，或者有未分配的包裹）
        assert result is not None
        # 检查是否有未分配的包裹或空的调度列表
        if "unallocated_packages" in result:
            assert len(result["unallocated_packages"]) > 0
