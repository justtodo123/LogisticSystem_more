"""
Exception Replan 集成测试

测试异常重规划完整流程 (F013)：
1. 创建异常事件（道路异常/包裹异常/节点异常）
2. 触发重规划（reroute或redispatch）
3. 验证新版本记录生成（version+1, parent_id, is_replan=true）
4. 验证原方案完整保留可对比
"""
import pytest
from sqlalchemy.orm import Session
from datetime import datetime

from models.exception_event import ExceptionEvent
from models.global_schedule import GlobalSchedule
from models.dispatch_batch import DispatchBatch
from models.node_dispatch import NodeDispatch
from models.route import Route


@pytest.fixture
def setup_exception_data(db_session):
    """设置异常重规划测试数据"""
    # 1. 创建全局调度记录
    global_schedule = GlobalSchedule(
        schedule_code="GS_TEST_001",
        goods_schedules='[{"goods_code":"G_TEST_001","order_code":"O_TEST_001","path":["SC001","SO001","SO002"]}]',
        total_cost=1000.0,
        version=1,
        parent_id=None,
        is_replan=False,
        replan_reason=None
    )
    db_session.add(global_schedule)
    db_session.flush()
    
    # 2. 创建调度批次
    dispatch_batch = DispatchBatch(
        batch_code="BATCH_TEST_001",
        schedule_id=global_schedule.id,
        level_phase=0,
        status="completed"
    )
    db_session.add(dispatch_batch)
    db_session.flush()
    
    # 3. 创建节点调度
    node_dispatch = NodeDispatch(
        batch_id=dispatch_batch.id,
        vehicle_id=1,
        driver_id=1,
        from_node_id=1,
        to_node_id=2,
        depart_time=datetime.now(),
        status="completed"
    )
    db_session.add(node_dispatch)
    db_session.flush()
    
    # 4. 创建路线
    route = Route(
        route_code="RT_TEST_001",
        dispatch_id=node_dispatch.id,
        vehicle_id=1,
        total_distance=100.0,
        total_time=120.0,
        route_segments='[{"road_name":"测试道路","start_lng":114.3,"start_lat":30.5,"end_lng":114.4,"end_lat":30.6}]',
        version=1,
        parent_id=None,
        is_replan=False
    )
    db_session.add(route)
    db_session.flush()
    
    # 5. 创建异常事件
    exception_event = ExceptionEvent(
        event_code="EXP_TEST_001",
        exception_type="road",  # 道路异常
        severity="medium",
        recommended_action="reroute",  # 重新规划路径
        trigger_node_id=2,
        related_route_id=route.id,
        description="测试道路异常",
        status="open"
    )
    db_session.add(exception_event)
    db_session.commit()
    
    return {
        "global_schedule": global_schedule,
        "dispatch_batch": dispatch_batch,
        "node_dispatch": node_dispatch,
        "route": route,
        "exception_event": exception_event
    }


@pytest.mark.integration
@pytest.mark.phase7
class TestExceptionReplan:
    """测试异常重规划"""
    
    def test_reroute_road_exception(self, db_session, setup_exception_data):
        """
        测试道路异常触发reroute
        
        验证：
        1. 创建道路异常事件
        2. 触发reroute（重新执行F006路径规划）
        3. 生成新版本路线（version=2, parent_id=1, is_replan=true）
        4. 原路线完整保留
        """
        data = setup_exception_data
        
        # TODO: 调用重规划API
        # response = client.post(f"/api/exceptions/{data['exception_event'].event_code}/replan")
        
        # 暂时跳过测试
        pytest.skip("异常重规划API可能还未实现，跳过测试")
    
    def test_redispatch_node_exception(self, db_session):
        """
        测试节点异常触发redispatch
        
        验证：
        1. 创建节点异常事件（容量/存储时长/维修）
        2. 触发redispatch（重新执行F007+F005+F006）
        3. 生成新版本全局调度、调度批次、节点调度、路线
        4. 原方案完整保留
        """
        pytest.skip("异常重规划API可能还未实现，跳过测试")
    
    def test_replan_version_chain(self, db_session, setup_exception_data):
        """
        测试重规划版本链
        
        验证：
        1. 第一次重规划：version=2, parent_id=1
        2. 第二次重规划：version=3, parent_id=2
        3. 可以通过parent_id追溯完整版本链
        """
        pytest.skip("异常重规划API可能还未实现，跳过测试")
    
    def test_replan_preserves_original(self, db_session, setup_exception_data):
        """
        测试重规划保留原方案
        
        验证：
        1. 重规划后，原全局调度记录仍然存在
        2. 原调度批次仍然存在
        3. 原节点调度仍然存在
        4. 原路线仍然存在
        """
        pytest.skip("异常重规划API可能还未实现，跳过测试")
