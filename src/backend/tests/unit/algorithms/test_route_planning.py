"""
算法单元测试：F006 路径规划（route_planning）

测试目标：
- run_route_planning 函数的正常流程和异常流程
- 验证输出结构、路径优化、错误处理
"""
import pytest
from algorithms.route_planning import run_route_planning
from models.node_dispatch import NodeDispatch
from models.vehicle import Vehicle
from models.node import Node
import json


class TestRoutePlanningNormal:
    """正常情况：生成路径"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_simple_two_nodes(self, db_session, test_nodes, test_vehicles):
        """
        测试两个节点之间的路径规划：
        1. 创建节点调度记录（dispatch）
        2. 调用 run_route_planning(db, dispatch.id)
        3. 验证返回结构
        """
        # 创建 NodeDispatch 记录
        dispatch = NodeDispatch(
            dispatch_code="ND_TEST001",
            dispatch_batch_id=1,
            vehicle_id=test_vehicles["VEH001"].id,
            driver_id=None,
            level_phase=0,
            tasks=[{"from_node_code": "SC001", "to_node_code": "SO001", "package_codes": ["PKG001"]}],
            total_distance=10.0,
            total_time=30.0,
        )
        db_session.add(dispatch)
        db_session.commit()

        # 调用算法
        result = run_route_planning(db_session, dispatch.id)

        # 验证返回结构
        assert "route_code" in result
        assert "dispatch_id" in result
        assert "vehicle_id" in result
        assert "route_segments" in result
        assert "total_distance" in result
        assert "total_time" in result
        assert "total_emission" in result
        assert "algorithm_type" in result

        # 验证 route_segments 是列表
        assert isinstance(result["route_segments"], list)
        assert len(result["route_segments"]) > 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_route_segments_content(self, db_session, test_nodes, test_vehicles):
        """
        测试路径段内容：
        1. 调用 run_route_planning
        2. 验证 route_segments 中每个元素包含必要字段
        """
        dispatch = NodeDispatch(
            dispatch_code="ND_TEST002",
            dispatch_batch_id=1,
            vehicle_id=test_vehicles["VEH001"].id,
            driver_id=None,
            level_phase=0,
            tasks=[{"from_node_code": "SC001", "to_node_code": "SO001", "package_codes": ["PKG001"]}],
            total_distance=10.0,
            total_time=30.0,
        )
        db_session.add(dispatch)
        db_session.commit()

        result = run_route_planning(db_session, dispatch.id)

        # 验证 route_segments 内容
        for segment in result["route_segments"]:
            assert "road_name" in segment
            assert "start_lng" in segment
            assert "start_lat" in segment
            assert "end_lng" in segment
            assert "end_lat" in segment


class TestRoutePlanningEdgeCases:
    """边界情况"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_dispatch_not_found(self, db_session):
        """
        测试调度记录不存在：
        1. 调用 run_route_planning(db, 9999)
        2. 验证抛出异常
        """
        with pytest.raises(Exception):
            run_route_planning(db_session, 9999)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_vehicle_not_found(self, db_session, test_nodes):
        """
        测试车辆不存在：
        1. 创建 dispatch 但 vehicle_id 不存在
        2. 验证抛出异常
        """
        dispatch = NodeDispatch(
            dispatch_code="ND_TEST003",
            dispatch_batch_id=1,
            vehicle_id=9999,  # 不存在的车辆
            driver_id=None,
            level_phase=0,
            tasks=[{"from_node_code": "SC001", "to_node_code": "SO001", "package_codes": ["PKG001"]}],
            total_distance=10.0,
            total_time=30.0,
        )
        db_session.add(dispatch)
        db_session.commit()

        with pytest.raises(Exception):
            run_route_planning(db_session, dispatch.id)
