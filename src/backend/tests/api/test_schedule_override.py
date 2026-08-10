"""
API测试：人工干预调度（schedule_override.py，T2-4）

测试目标：
- PUT /api/override/vehicle：换车成功 / 约束拒绝
- PUT /api/override/driver：换司机成功
- POST /api/override/recalculate：批量重算
- POST /api/override/undo：撤销干预
- 权限：仅调度员/管理员可操作
"""
import json

import pytest

from models.user import User
from services.auth_service import get_password_hash
from models.global_schedule import GlobalSchedule
from models.dispatch_batch import DispatchBatch
from models.node_dispatch import NodeDispatch
from models.route import Route
from models.package import Package


def _create_dispatch_context(db_session, test_nodes, test_vehicles, test_drivers):
    """构造完整的调度上下文，返回 (gs, batch, dispatch)"""
    gs = GlobalSchedule(
        schedule_code="GS_OVR_API001",
        order_codes=json.dumps(["O001"]),
        goods_schedules=json.dumps([]),
        total_distance=10.0,
        total_time=0.5,
        total_goods=1,
        score=0.5,
        algorithm_type="traditional",
        version=1,
        is_replan=False,
    )
    db_session.add(gs)
    db_session.commit()

    batch = DispatchBatch(
        batch_code="BATCH_OVR_API001",
        global_schedule_id=gs.id,
        status="pending",
    )
    db_session.add(batch)
    db_session.commit()

    dispatch = NodeDispatch(
        dispatch_code="ND_OVR_API001",
        dispatch_batch_id=batch.id,
        vehicle_id=test_vehicles["VEH001"].id,
        driver_id=test_drivers["DRV001"].id,
        level_phase=0,
        tasks=json.dumps([
            {"from_node_code": "SC001", "to_node_code": "SO010",
             "package_codes": ["PKG_OVR_API1"], "is_return": False},
            {"from_node_code": "SO010", "to_node_code": "SC001",
             "package_codes": [], "is_return": True},
        ]),
        total_distance=10.0,
        total_time=1.0,
    )
    db_session.add(dispatch)
    db_session.commit()

    pkg = Package(
        package_code="PKG_OVR_API1",
        weight=10.0,
        volume=0.5,
        from_node_id=test_nodes["SC001"].id,
        to_node_id=test_nodes["SO010"].id,
        goods_items=json.dumps([]),
        dispatch_id=dispatch.id,
    )
    db_session.add(pkg)
    db_session.commit()

    route = Route(
        route_code="RT_OVR_API001",
        dispatch_id=dispatch.id,
        vehicle_id=test_vehicles["VEH001"].id,
        route_segments=json.dumps([
            {"road_name": "虚拟道路", "start_lng": 114.3, "start_lat": 30.58,
             "end_lng": 114.315, "end_lat": 30.54}
        ]),
        total_distance=10.0,
        total_time=60.0,
        total_emission=2.0,
        algorithm_type="traditional",
        version=1,
    )
    db_session.add(route)
    db_session.commit()
    return gs, batch, dispatch


def _login(client, username="testuser", password="123456"):
    resp = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    return resp.json()["data"]["access_token"]


@pytest.fixture(scope="function")
def dispatcher_user(db_session):
    user = User(
        username="testuser",
        password_hash=get_password_hash("123456"),
        role="dispatcher",
        display_name="测试调度员",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


class TestOverrideVehicleAPI:
    """换车端点"""

    @pytest.mark.api
    def test_override_vehicle_success(self, client, db_session, dispatcher_user,
                                      test_nodes, test_vehicles, test_drivers):
        _create_dispatch_context(db_session, test_nodes, test_vehicles, test_drivers)
        token = _login(client)

        resp = client.put(
            "/api/override/vehicle",
            json={"dispatch_code": "ND_OVR_API001", "vehicle_code": "VEH002"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["vehicle_code"] == "VEH002"
        assert body["data"]["recalculated"] is True
        assert body["data"]["route_code"].startswith("ROUTE")

    @pytest.mark.api
    def test_override_vehicle_rejected_capacity(self, client, db_session, dispatcher_user,
                                                test_nodes, test_vehicles, test_drivers):
        # 100kg 大包裹挂在 VEH002（有效载重180）上，换到 VEH001（有效载重90）→ 拒绝
        gs, batch, dispatch = _create_dispatch_context(
            db_session, test_nodes, test_vehicles, test_drivers)
        # 加大包裹重量
        pkg = db_session.query(Package).filter(Package.package_code == "PKG_OVR_API1").first()
        pkg.weight = 100.0
        db_session.commit()
        # 当前车辆改为 VEH002
        dispatch.vehicle_id = test_vehicles["VEH002"].id
        db_session.commit()

        token = _login(client)
        resp = client.put(
            "/api/override/vehicle",
            json={"dispatch_code": "ND_OVR_API001", "vehicle_code": "VEH001"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] != 0
        assert "载重" in body["message"]

    @pytest.mark.api
    def test_override_vehicle_dispatch_not_found(self, client, db_session, dispatcher_user):
        token = _login(client)
        resp = client.put(
            "/api/override/vehicle",
            json={"dispatch_code": "ND_NOEXIST", "vehicle_code": "VEH002"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == 40400


class TestOverrideDriverAPI:
    """换司机端点"""

    @pytest.mark.api
    def test_override_driver_success(self, client, db_session, dispatcher_user,
                                     test_nodes, test_vehicles, test_drivers):
        _create_dispatch_context(db_session, test_nodes, test_vehicles, test_drivers)
        token = _login(client)

        resp = client.put(
            "/api/override/driver",
            json={"dispatch_code": "ND_OVR_API001", "driver_code": "DRV002"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["driver_code"] == "DRV002"


class TestOverrideRecalculateAPI:
    """批量重算端点"""

    @pytest.mark.api
    def test_recalculate_after_override(self, client, db_session, dispatcher_user,
                                        test_nodes, test_vehicles, test_drivers):
        _create_dispatch_context(db_session, test_nodes, test_vehicles, test_drivers)
        token = _login(client)
        # 先换车
        client.put(
            "/api/override/vehicle",
            json={"dispatch_code": "ND_OVR_API001", "vehicle_code": "VEH002"},
            headers={"Authorization": f"Bearer {token}"},
        )

        resp = client.post(
            "/api/override/recalculate",
            json={"batch_code": "BATCH_OVR_API001"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["recalculated_count"] >= 1


class TestOverrideUndoAPI:
    """撤销端点"""

    @pytest.mark.api
    def test_undo_override(self, client, db_session, dispatcher_user,
                           test_nodes, test_vehicles, test_drivers):
        _create_dispatch_context(db_session, test_nodes, test_vehicles, test_drivers)
        token = _login(client)
        client.put(
            "/api/override/vehicle",
            json={"dispatch_code": "ND_OVR_API001", "vehicle_code": "VEH002"},
            headers={"Authorization": f"Bearer {token}"},
        )

        resp = client.post(
            "/api/override/undo",
            json={"dispatch_code": "ND_OVR_API001"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["vehicle_code"] == "VEH001"
        assert body["data"]["undo_version"] == 1


class TestOverridePermission:
    """权限控制"""

    @pytest.mark.api
    def test_manager_forbidden(self, client, db_session, dispatcher_user):
        # 创建 manager 用户并登录（仅调度员/管理员可干预）
        manager = User(
            username="manager_user",
            password_hash=get_password_hash("123456"),
            role="manager",
            display_name="管理者",
            is_active=True,
        )
        db_session.add(manager)
        db_session.commit()

        resp = client.post(
            "/api/auth/login",
            json={"username": "manager_user", "password": "123456"},
        )
        token = resp.json()["data"]["access_token"]

        resp = client.put(
            "/api/override/vehicle",
            json={"dispatch_code": "ND_OVR_API001", "vehicle_code": "VEH002"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
