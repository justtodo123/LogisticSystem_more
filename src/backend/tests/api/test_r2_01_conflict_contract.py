"""HTTP conflict contract for R2-01 CAS."""

from unittest.mock import patch

import pytest

from models.exception_event import ExceptionEvent
from models.global_schedule import GlobalSchedule
from models.package import Package
from services.schedule_service import ScheduleService


@pytest.mark.api
@pytest.mark.asyncio
async def test_confirm_schedule_second_call_is_40901(
    client, db_session, test_nodes, test_orders, test_goods, test_users, dispatcher_token
):
    preview = await ScheduleService.create_global_schedule(
        order_codes=None,
        algorithm="traditional",
        db=db_session,
        preview=True,
    )
    schedule_code = preview["data"]["schedule_code"]
    headers = {
        "Authorization": f"Bearer {dispatcher_token}",
        "X-Idempotency-Key": "r2-01-conflict-first",
    }

    first = client.post(f"/api/schedule/confirm/{schedule_code}", headers=headers)
    assert first.status_code == 200
    assert first.json()["code"] == 0

    second = client.post(
        f"/api/schedule/confirm/{schedule_code}",
        headers={**headers, "X-Idempotency-Key": "r2-01-conflict-second"},
    )
    assert second.status_code == 409
    body = second.json()
    assert set(body) == {"code", "message", "data", "meta"}
    assert body["code"] == 40901
    assert body["data"] is None

    db_session.expire_all()
    assert db_session.query(GlobalSchedule).filter_by(schedule_code=schedule_code, status="active").count() == 1


@pytest.mark.api
def test_confirm_arrival_second_call_is_40901(
    client, db_session, test_nodes, test_orders, test_goods, test_users, dispatcher_token
):
    import json

    goods = test_goods["G001"]
    goods.status = "in_transit"
    goods.node_id = test_nodes["SC001"].id
    schedule = GlobalSchedule(
        schedule_code="GS_HTTP_ARRIVAL",
        order_codes=json.dumps([]),
        total_distance=0.0,
        total_time=0.0,
        total_goods=0,
        score=0.0,
        algorithm_type="traditional",
        version=1,
        is_replan=False,
        goods_schedules=json.dumps([
            {"goods_code": "G001", "order_code": "O001", "path": ["SC001", "SO001", "SO010"]}
        ]),
    )
    db_session.add(schedule)
    db_session.commit()
    package = Package(
        package_code="PKG_HTTP_ARRIVAL",
        from_node_id=test_nodes["SC001"].id,
        to_node_id=test_nodes["SO001"].id,
        weight=10.0,
        volume=0.5,
        status="in_transit",
        schedule_id=schedule.id,
        goods_items=[{"goods_code": "G001", "order_code": "O001"}],
    )
    db_session.add(package)
    db_session.commit()

    headers = {
        "Authorization": f"Bearer {dispatcher_token}",
        "X-Idempotency-Key": "r2-01-conflict-first",
    }
    payload = {
        "schedule_code": "GS_HTTP_ARRIVAL",
        "package_code": "PKG_HTTP_ARRIVAL",
        "is_normal": True,
    }
    with patch("services.notification.send_notification_fire_and_forget") as notify:
        first = client.post("/api/simulation/confirm-arrival", json=payload, headers=headers)
        assert first.status_code == 200
        assert first.json()["code"] == 0
        assert notify.call_count == 1

        second = client.post(
            "/api/simulation/confirm-arrival",
            json=payload,
            headers={**headers, "X-Idempotency-Key": "r2-01-conflict-second"},
        )
        assert second.status_code == 409
        body = second.json()
        assert body["code"] == 40901
        assert body["data"] is None
        assert notify.call_count == 1

    db_session.expire_all()
    assert db_session.query(Package).filter_by(package_code="PKG_HTTP_ARRIVAL", status="delivered").count() == 1
    assert db_session.query(ExceptionEvent).count() == 0


@pytest.mark.api
def test_confirm_arrival_batch_second_package_is_40901(
    client, db_session, test_nodes, test_orders, test_goods, test_users, dispatcher_token
):
    import json

    goods = test_goods["G001"]
    goods.status = "in_transit"
    goods.node_id = test_nodes["SC001"].id
    other = test_goods["G002"]
    other.status = "in_transit"
    other.node_id = test_nodes["SC001"].id
    schedule = GlobalSchedule(
        schedule_code="GS_HTTP_ARRIVAL_BATCH",
        order_codes=json.dumps([]),
        total_distance=0.0,
        total_time=0.0,
        total_goods=0,
        score=0.0,
        algorithm_type="traditional",
        version=1,
        is_replan=False,
        goods_schedules=json.dumps([
            {"goods_code": "G001", "order_code": "O001", "path": ["SC001", "SO001", "SO010"]},
            {"goods_code": "G002", "order_code": "O001", "path": ["SC001", "SO001", "SO010"]},
        ]),
    )
    db_session.add(schedule)
    db_session.commit()
    first_package = Package(
        package_code="PKG_HTTP_BATCH_OK",
        from_node_id=test_nodes["SC001"].id,
        to_node_id=test_nodes["SO001"].id,
        weight=10.0,
        volume=0.5,
        status="in_transit",
        schedule_id=schedule.id,
        goods_items=[{"goods_code": "G001", "order_code": "O001"}],
    )
    second_package = Package(
        package_code="PKG_HTTP_BATCH_DONE",
        from_node_id=test_nodes["SC001"].id,
        to_node_id=test_nodes["SO001"].id,
        weight=10.0,
        volume=0.5,
        status="delivered",
        schedule_id=schedule.id,
        goods_items=[{"goods_code": "G002", "order_code": "O001"}],
    )
    db_session.add(first_package)
    db_session.add(second_package)
    db_session.commit()

    headers = {
        "Authorization": f"Bearer {dispatcher_token}",
        "X-Idempotency-Key": "r2-01-conflict-first",
    }
    payload = {
        "schedule_code": "GS_HTTP_ARRIVAL_BATCH",
        "confirmations": [
            {"package_code": "PKG_HTTP_BATCH_OK", "is_normal": True},
            {"package_code": "PKG_HTTP_BATCH_DONE", "is_normal": True},
        ],
    }
    with patch("services.notification.send_notification_fire_and_forget") as notify:
        response = client.post("/api/simulation/confirm-arrival-batch", json=payload, headers=headers)
        assert notify.call_count == 0

    assert response.status_code == 409
    body = response.json()
    assert set(body) == {"code", "message", "data", "meta"}
    assert body["code"] == 40901
    assert body["data"] is None

    db_session.expire_all()
    assert db_session.query(Package).filter_by(package_code="PKG_HTTP_BATCH_OK", status="in_transit").count() == 1
    assert db_session.query(Package).filter_by(package_code="PKG_HTTP_BATCH_DONE", status="delivered").count() == 1
    assert db_session.query(ExceptionEvent).count() == 0
