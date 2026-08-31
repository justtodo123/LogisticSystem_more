"""异常重规划 API 到 Saga/业务产物的真实集成验收。"""
import json

import pytest
from fastapi.testclient import TestClient

from models.dispatch_batch import DispatchBatch
from models.exception_event import ExceptionEvent
from models.global_schedule import GlobalSchedule
from models.node_dispatch import NodeDispatch
from models.replan_task import ReplanTask
from models.route import Route


@pytest.fixture
def client(test_db):
    """让 HTTP 请求、幂等存储和断言会话共享测试数据库。"""
    from config import database as db_mod
    from main import app
    from utils.idempotency_store import reset_session_factory, set_session_factory

    _engine, session_factory = test_db

    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[db_mod.get_db] = override_get_db
    set_session_factory(session_factory)
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        reset_session_factory()
        app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client, test_users):
    response = client.post(
        "/api/auth/login",
        json={"username": "dispatcher", "password": "123456"},
    )
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _post_replan(client, headers, event_code, key, action, reason):
    return client.post(
        f"/api/exceptions/{event_code}/replan",
        json={"action": action, "reason": reason},
        headers={**headers, "X-Idempotency-Key": key},
    )


def _prepare_redispatch(db, test_orders, *, code="GS_INT_REDISPATCH_1", version=1):
    order_codes = list(test_orders)[:3]
    schedule = GlobalSchedule(
        schedule_code=code,
        order_codes=order_codes,
        goods_schedules=[],
        total_distance=100,
        total_time=5,
        total_goods=len(order_codes),
        score=1,
        algorithm_type="traditional",
        version=version,
        is_replan=version > 1,
    )
    db.add(schedule)
    for order_code in order_codes:
        order = test_orders[order_code]
        order.status = "exception"
        for goods in order.goods:
            goods.status = "exception"
    db.commit()
    return schedule


def _node_event(db, schedule, node_code, event_code):
    event = ExceptionEvent(
        event_code=event_code,
        exception_type="node",
        exception_subtype="capacity_limit",
        target_type="node",
        target_code=node_code,
        recommended_action="redispatch",
        related_schedule_code=schedule.schedule_code,
        description="节点容量异常",
        status="open",
    )
    db.add(event)
    db.commit()
    return event


def _prepare_reroute(db, test_nodes, test_vehicles, test_drivers, suffix):
    node = test_nodes["SC001"]
    vehicle = test_vehicles["VEH001"]
    driver = test_drivers["DRV001"]
    schedule = GlobalSchedule(
        schedule_code=f"GS_INT_ROUTE_{suffix}",
        order_codes=["O001"],
        goods_schedules=[],
        total_distance=10,
        total_time=1,
        total_goods=1,
        score=1,
    )
    db.add(schedule)
    db.flush()
    batch = DispatchBatch(
        batch_code=f"DB_INT_ROUTE_{suffix}",
        global_schedule_id=schedule.id,
        status="pending",
        l0_l1_dispatch_count=1,
        l1_l2_dispatch_count=0,
    )
    db.add(batch)
    db.flush()
    dispatch = NodeDispatch(
        dispatch_code=f"ND_INT_ROUTE_{suffix}",
        dispatch_batch_id=batch.id,
        vehicle_id=vehicle.id,
        driver_id=driver.id,
        level_phase=0,
        tasks=json.dumps([{
            "from_node_code": node.node_code,
            "to_node_code": "SO001",
            "package_codes": [],
        }]),
        total_distance=10,
        total_time=1,
    )
    db.add(dispatch)
    db.flush()
    route = Route(
        route_code=f"RT_INT_ROUTE_{suffix}",
        dispatch_id=dispatch.id,
        vehicle_id=vehicle.id,
        route_segments=[],
        total_distance=10,
        total_time=1,
        total_emission=1,
        version=1,
        is_replan=False,
    )
    db.add(route)
    event = ExceptionEvent(
        event_code=f"EX_INT_ROUTE_{suffix}",
        exception_type="road",
        exception_subtype="congestion",
        target_type="route",
        target_code=route.route_code,
        recommended_action="reroute",
        description="道路异常",
        status="open",
    )
    db.add(event)
    db.commit()
    return route, event


@pytest.mark.integration
@pytest.mark.phase7
class TestExceptionReplan:
    def test_node_exception_redispatch_and_task_artifacts(
        self, client, auth_headers, db_session, test_nodes, test_orders,
        test_goods, test_vehicles, test_drivers,
    ):
        original = _prepare_redispatch(db_session, test_orders)
        event = _node_event(db_session, original, "SO001", "EX_INT_NODE_1")

        response = _post_replan(
            client, auth_headers, event.event_code, "int-node-redispatch", "redispatch",
            "节点容量恢复验收",
        )

        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["code"] == 0, payload
        task = db_session.query(ReplanTask).filter_by(
            idempotency_key="int-node-redispatch"
        ).one()
        schedule = db_session.get(GlobalSchedule, task.new_schedule_id)
        batch = db_session.get(DispatchBatch, task.dispatch_batch_id)
        route = db_session.get(Route, task.new_route_id)
        assert task.status == "COMPLETED"
        assert task.operation_type == "redispatch"
        assert schedule.schedule_code == task.new_schedule_code == payload["data"]["schedule_code"]
        assert batch.batch_code == task.dispatch_batch_code == payload["data"]["batch_code"]
        assert route.route_code == task.new_route_code
        assert schedule.parent_id == original.id
        assert schedule.is_replan is True

    def test_road_exception_reroute_and_task_artifact(
        self, client, auth_headers, db_session, test_nodes, test_vehicles, test_drivers,
    ):
        original, event = _prepare_reroute(
            db_session, test_nodes, test_vehicles, test_drivers, "ONE"
        )

        response = _post_replan(
            client, auth_headers, event.event_code, "int-road-reroute", "reroute",
            "道路拥堵绕行验收",
        )

        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["code"] == 0, payload
        task = db_session.query(ReplanTask).filter_by(
            idempotency_key="int-road-reroute"
        ).one()
        new_route = db_session.get(Route, task.new_route_id)
        assert task.status == "COMPLETED"
        assert task.operation_type == "reroute"
        assert new_route.route_code == task.new_route_code == payload["data"]["new_route_code"]
        assert new_route.parent_id == original.id
        assert new_route.version == 2
        assert new_route.is_replan is True
        assert db_session.get(Route, original.id).route_code == original.route_code

    def test_http_idempotent_replay_does_not_create_saga_or_artifacts(
        self, client, auth_headers, db_session, test_nodes, test_vehicles, test_drivers,
    ):
        _original, event = _prepare_reroute(
            db_session, test_nodes, test_vehicles, test_drivers, "REPLAY"
        )
        key = "int-http-replay"

        first = _post_replan(
            client, auth_headers, event.event_code, key, "reroute", "相同请求回放"
        )
        counts = (
            db_session.query(ReplanTask).count(),
            db_session.query(Route).count(),
        )
        replay = _post_replan(
            client, auth_headers, event.event_code, key, "reroute", "相同请求回放"
        )

        assert first.status_code == replay.status_code == 200
        assert replay.json() == first.json()
        assert counts == (
            db_session.query(ReplanTask).count(),
            db_session.query(Route).count(),
        )
        assert db_session.query(ReplanTask).filter_by(idempotency_key=key).count() == 1

    def test_same_http_key_with_different_request_conflicts(
        self, client, auth_headers, db_session, test_nodes, test_vehicles, test_drivers,
    ):
        _original, event = _prepare_reroute(
            db_session, test_nodes, test_vehicles, test_drivers, "MISMATCH"
        )
        key = "int-http-mismatch"
        first = _post_replan(
            client, auth_headers, event.event_code, key, "reroute", "首次请求"
        )
        task_count = db_session.query(ReplanTask).count()
        route_count = db_session.query(Route).count()

        conflict = _post_replan(
            client, auth_headers, event.event_code, key, "reroute", "不同请求"
        )

        assert first.status_code == 200
        assert conflict.status_code == 409
        assert conflict.json()["code"] == 40903
        assert db_session.query(ReplanTask).count() == task_count
        assert db_session.query(Route).count() == route_count

    def test_redispatch_version_chain_1_2_3_preserves_originals(
        self, client, auth_headers, db_session, test_nodes, test_orders,
        test_goods, test_vehicles, test_drivers,
    ):
        original = _prepare_redispatch(
            db_session, test_orders, code="GS_INT_CHAIN_1", version=1
        )
        first_event = _node_event(db_session, original, "SO001", "EX_INT_CHAIN_1")
        first_response = _post_replan(
            client, auth_headers, first_event.event_code, "int-chain-one", "redispatch",
            "第一次重规划",
        )
        assert first_response.json()["code"] == 0, first_response.json()
        first = db_session.query(GlobalSchedule).filter_by(
            schedule_code=first_response.json()["data"]["schedule_code"]
        ).one()
        assert first.version == 2
        assert first.parent_id == original.id

        for order_code in original.order_codes:
            order = test_orders[order_code]
            order.status = "exception"
            for goods in order.goods:
                goods.status = "exception"
        second_event = _node_event(db_session, first, "SO001", "EX_INT_CHAIN_2")
        second_response = _post_replan(
            client, auth_headers, second_event.event_code, "int-chain-two", "redispatch",
            "第二次重规划",
        )

        assert second_response.json()["code"] == 0, second_response.json()
        second = db_session.query(GlobalSchedule).filter_by(
            schedule_code=second_response.json()["data"]["schedule_code"]
        ).one()
        assert [original.version, first.version, second.version] == [1, 2, 3]
        assert second.parent_id == first.id
        assert first.parent_id == original.id
        assert first.is_replan is second.is_replan is True
        assert original.is_replan is False
        assert all(db_session.get(GlobalSchedule, item.id) is not None for item in (original, first, second))
