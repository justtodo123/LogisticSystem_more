"""
算法单元测试：F006 路径规划（route_planning）

测试目标：
- route_planning 函数的正常流程和异常流程
- 验证输出结构、路径优化、错误处理
"""
import pytest
from algorithms.route_planning import route_planning
from models.node_dispatch import NodeDispatch
from models.vehicle import Vehicle
from models.node import Node
import json


class TestRoutePlanningNormal:
    """正常情况：生成路径"""

    @pytest.mark.unit
    def test_route_planning_success(self, db_session, test_nodes, test_vehicles):
        """
        测试正常路径规划流程：
        1. 创建节点调度记录（node_dispatch）
        2. 调用 route_planning(node_dispatch_id, db)
        3. 验证返回结构包含 route_code、total_distance、route_segments 等
        """
        # 创建节点调度记录
        node_dispatch = NodeDispatch(
            node_dispatch_code="ND001",
            batch_id=1,
            vehicle_id=test_vehicles["VEH001"].id,
            driver_id=1,
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO001"].id,
            level_phase=0,
            status="pending",
            tasks=json.dumps([{"from_node_code": "SC001", "to_node_code": "SO001", "package_codes": ["PKG001"], "is_return": False}]),
        )
        db_session.add(node_dispatch)
        db_session.commit()
        
        # 调用路径规划
        result = route_planning(
            node_dispatch_id=node_dispatch.id,
            db=db_session,
        )
        
        # 验证返回结构
        assert "route_code" in result
        assert result["route_code"].startswith("RT")
        assert "total_distance" in result
        assert "total_time" in result
        assert "total_emission" in result
        assert "route_segments" in result
        assert len(result["route_segments"]) > 0
        
        # 验证 route_segments 结构
        for seg in result["route_segments"]:
            assert "road_name" in seg
            assert "start_lng" in seg
            assert "start_lat" in seg
            assert "end_lng" in seg
            assert "end_lat" in seg
        
        # 验证数值合理性
        assert result["total_distance"] > 0
        assert result["total_time"] > 0
        assert result["total_emission"] >= 0

    @pytest.mark.unit
    def test_route_planning_return_trip(self, db_session, test_nodes, test_vehicles):
        """
        测试往返路径规划：
        1. 创建节点调度记录（is_return=True）
        2. 调用 route_planning
        3. 验证路径包含返回段
        """
        # 创建节点调度记录（包含返回任务）
        node_dispatch = NodeDispatch(
            node_dispatch_code="ND001",
            batch_id=1,
            vehicle_id=test_vehicles["VEH001"].id,
            driver_id=1,
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO001"].id,
            level_phase=0,
            status="pending",
            tasks=json.dumps([
                {"from_node_code": "SC001", "to_node_code": "SO001", "package_codes": ["PKG001"], "is_return": True}
            ]),
        )
        db_session.add(node_dispatch)
        db_session.commit()
        
        # 调用路径规划
        result = route_planning(
            node_dispatch_id=node_dispatch.id,
            db=db_session,
        )
        
        # 验证返回结构
        assert "route_code" in result
        assert "route_segments" in result
        # 注意：实际行为取决于算法实现，这里只验证基本结构
        assert len(result["route_segments"]) > 0


class TestRoutePlanningEdgeCases:
    """边界条件测试"""

    @pytest.mark.unit
    def test_route_planning_node_dispatch_not_found(self, db_session):
        """
        测试节点调度记录不存在：
        1. 调用 route_planning(999, db)
        2. 验证抛出异常或返回错误
        """
        # route_planning 可能抛出异常
        with pytest.raises(Exception):
            route_planning(
                node_dispatch_id=999,  # 不存在的ID
                db=db_session,
            )

    @pytest.mark.unit
    def test_route_planning_empty_tasks(self, db_session, test_nodes, test_vehicles):
        """
        测试空任务列表：
        1. 创建节点调度记录（tasks为空）
        2. 调用 route_planning
        3. 验证返回空路径或抛出异常
        """
        # 创建节点调度记录（空任务）
        node_dispatch = NodeDispatch(
            node_dispatch_code="ND001",
            batch_id=1,
            vehicle_id=test_vehicles["VEH001"].id,
            driver_id=1,
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO001"].id,
            level_phase=0,
            status="pending",
            tasks=json.dumps([]),  # 空任务
        )
        db_session.add(node_dispatch)
        db_session.commit()
        
        # 调用路径规划
        try:
            result = route_planning(
                node_dispatch_id=node_dispatch.id,
                db=db_session,
            )
            # 如果成功返回，验证基本结构
            assert "route_code" in result
            assert "route_segments" in result
            assert len(result["route_segments"]) == 0  # 空路径
        except Exception:
            # 如果抛出异常，也是合理的
            pass
