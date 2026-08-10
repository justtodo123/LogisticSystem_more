"""
报表分析 API 测试（T5-3）

覆盖：
- GET /api/reports/sla — 准点率、平均延迟、订单分布、日期过滤
- GET /api/reports/cost — 按车辆（线路）/ 节点成本汇总
- GET /api/reports/exceptions — 异常类型 / 状态统计
- GET /api/reports/capacity — 运力效率
"""
from datetime import datetime, timedelta

import pytest

from core.error_codes import CODE_PARAM_ERROR
from models.exception_event import ExceptionEvent
from models.global_schedule import GlobalSchedule
from models.node import Node
from models.node_dispatch import NodeDispatch
from models.order import Order
from models.package import Package
from models.route import Route
from models.vehicle import Vehicle


@pytest.fixture
def auth_headers(client, test_users):
    """认证头（调度员）"""
    response = client.post("/api/auth/login", json={
        "username": "dispatcher",
        "password": "123456",
    })
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _make_order(db_session, node_id, status, created_at, updated_at=None, code="OR"):
    order = Order(
        order_code=code,
        destination_node_id=node_id,
        time_window="2026-06-15 全天",
        status=status,
        created_at=created_at,
        updated_at=updated_at or created_at,
    )
    db_session.add(order)
    return order


@pytest.mark.api
@pytest.mark.phase5
class TestSlaReport:
    def test_sla_on_time_and_late(self, client, auth_headers, db_session, test_nodes):
        """准点率与平均延迟计算"""
        now = datetime.now()
        # 准时签收：1 小时完成 ≤ 24h SLA 目标
        _make_order(db_session, test_nodes["SO010"].id, "signed",
                    now - timedelta(hours=1), now, code="O_SLA_ON")
        # 延迟订单①：48h 前创建、刚刚签收 → 完成耗时 48h > 24h
        _make_order(db_session, test_nodes["SO010"].id, "signed",
                    now - timedelta(hours=48), now,
                    code="O_SLA_LATE_created")
        # 延迟订单②：72h 前创建、24h 前签收 → 完成耗时 48h > 24h
        _make_order(db_session, test_nodes["SO010"].id, "signed",
                    now - timedelta(hours=72), now - timedelta(hours=24),
                    code="O_SLA_LATE")
        _make_order(db_session, test_nodes["SO011"].id, "exception",
                    now - timedelta(hours=5), code="O_SLA_EXC")
        _make_order(db_session, test_nodes["SO012"].id, "unassigned",
                    now - timedelta(hours=2), code="O_SLA_UN")
        db_session.commit()

        response = client.get("/api/reports/sla", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total_orders"] == 5
        assert data["signed_orders"] == 3
        assert data["exception_orders"] == 1
        assert data["in_progress_orders"] == 1
        assert data["on_time_rate"] == pytest.approx(round(1 / 3, 4))
        assert data["avg_delay_minutes"] > 0

    def test_sla_date_filter(self, client, auth_headers, db_session, test_nodes):
        """日期过滤：仅统计日期范围内创建的订单"""
        now = datetime.now()
        _make_order(db_session, test_nodes["SO010"].id, "signed",
                    now - timedelta(days=30), code="O_OLD")
        _make_order(db_session, test_nodes["SO010"].id, "signed",
                    now - timedelta(days=1), code="O_NEW")
        db_session.commit()

        response = client.get(
            "/api/reports/sla",
            params={"date_from": (now - timedelta(days=7)).date().isoformat()},
            headers=auth_headers,
        )
        data = response.json()["data"]
        assert data["total_orders"] == 1
        assert data["signed_orders"] == 1

    def test_sla_invalid_date(self, client, auth_headers, db_session, test_nodes):
        """非法日期 → 参数错误"""
        response = client.get(
            "/api/reports/sla",
            params={"date_from": "not-a-date"},
            headers=auth_headers,
        )
        assert response.json()["code"] == CODE_PARAM_ERROR

    def test_sla_requires_auth(self, client):
        """未登录 → 401"""
        response = client.get("/api/reports/sla")
        assert response.status_code == 401


@pytest.mark.api
@pytest.mark.phase5
class TestCostReport:
    def test_cost_by_vehicle_and_node(self, client, auth_headers, db_session,
                                      test_nodes, test_vehicles):
        """按车辆与节点汇总成本（距离 × cost_per_km）"""
        # 创建两辆车对应的调度明细与路线
        dispatch1 = NodeDispatch(
            dispatch_code="ND_COST1", dispatch_batch_id=1,
            vehicle_id=test_vehicles["VEH001"].id, driver_id=None, level_phase=0,
            tasks=[{"from_node_code": "SC001", "to_node_code": "SO001"}],
            total_distance=0, total_time=0,
        )
        db_session.add(dispatch1)
        db_session.flush()
        route1 = Route(
            route_code="R_COST1", dispatch_id=dispatch1.id,
            vehicle_id=test_vehicles["VEH001"].id,
            route_segments=[], total_distance=100.0, total_time=60.0, total_emission=0,
        )
        db_session.add(route1)

        dispatch2 = NodeDispatch(
            dispatch_code="ND_COST2", dispatch_batch_id=1,
            vehicle_id=test_vehicles["VEH002"].id, driver_id=None, level_phase=0,
            tasks=[{"from_node_code": "SC001", "to_node_code": "SO011"}],
            total_distance=0, total_time=0,
        )
        db_session.add(dispatch2)
        db_session.flush()
        route2 = Route(
            route_code="R_COST2", dispatch_id=dispatch2.id,
            vehicle_id=test_vehicles["VEH002"].id,
            route_segments=[], total_distance=50.0, total_time=30.0, total_emission=0,
        )
        db_session.add(route2)
        db_session.commit()

        response = client.get("/api/reports/cost", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        # VEH001: 100km×5=500；VEH002: 50km×5=250
        assert data["total_cost"] == pytest.approx(750.0)
        by_veh = {v["vehicle_code"]: v for v in data["by_vehicle"]}
        assert by_veh["VEH001"]["cost"] == pytest.approx(500.0)
        assert by_veh["VEH002"]["cost"] == pytest.approx(250.0)
        assert by_veh["VEH001"]["route_count"] == 1
        # 两辆车均归属 SC001
        by_node = {n["node_code"]: n for n in data["by_node"]}
        assert by_node["SC001"]["cost"] == pytest.approx(750.0)

    def test_cost_empty(self, client, auth_headers):
        """无路线时成本为 0"""
        response = client.get("/api/reports/cost", headers=auth_headers)
        data = response.json()["data"]
        assert data["total_cost"] == 0.0
        assert data["by_vehicle"] == []
        assert data["by_node"] == []


@pytest.mark.api
@pytest.mark.phase5
class TestExceptionReport:
    def test_exception_stats(self, client, auth_headers, db_session, test_nodes):
        """异常类型 / 状态统计"""
        ev1 = ExceptionEvent(
            event_code="EX_REP_1", exception_type="road", exception_subtype="congestion",
            target_type="route", target_code="R1", recommended_action="reroute",
            description="拥堵", status="open",
        )
        ev2 = ExceptionEvent(
            event_code="EX_REP_2", exception_type="road", exception_subtype="congestion",
            target_type="route", target_code="R2", recommended_action="reroute",
            description="拥堵", status="open",
        )
        ev3 = ExceptionEvent(
            event_code="EX_REP_3", exception_type="package", exception_subtype="damage",
            target_type="package", target_code="P1", recommended_action="redispatch",
            description="破损", status="resolved", resolved_at=datetime.now(),
        )
        db_session.add_all([ev1, ev2, ev3])
        db_session.commit()

        response = client.get("/api/reports/exceptions", headers=auth_headers)
        data = response.json()["data"]
        assert data["total_exceptions"] == 3
        assert data["open_count"] == 2
        assert data["resolved_count"] == 1
        by_type = {t["type"]: t["count"] for t in data["by_type"]}
        assert by_type["road"] == 2
        assert by_type["package"] == 1
        by_sub = {s["subtype"]: s["count"] for s in data["by_subtype"]}
        assert by_sub["congestion"] == 2
        assert by_sub["damage"] == 1


@pytest.mark.api
@pytest.mark.phase5
class TestCapacityReport:
    def test_capacity_stats(self, client, auth_headers, db_session, test_nodes,
                            test_vehicles):
        """运力效率统计"""
        # 一辆 delivering 车辆
        test_vehicles["VEH002"].status = "delivering"
        # 一个调度明细
        dispatch = NodeDispatch(
            dispatch_code="ND_CAP1", dispatch_batch_id=1,
            vehicle_id=test_vehicles["VEH001"].id, driver_id=None, level_phase=0,
            tasks=[], total_distance=0, total_time=0,
        )
        db_session.add(dispatch)
        db_session.flush()
        # 两个包裹，一个已送达
        db_session.add(Package(
            package_code="PKG_CAP1", weight=1, volume=0.1, status="delivered",
            from_node_id=test_nodes["SC001"].id, to_node_id=test_nodes["SO010"].id,
            goods_items=[], schedule_id=None,
        ))
        db_session.add(Package(
            package_code="PKG_CAP2", weight=1, volume=0.1, status="pending_dispatch",
            from_node_id=test_nodes["SC001"].id, to_node_id=test_nodes["SO010"].id,
            goods_items=[], schedule_id=None,
        ))
        db_session.commit()

        response = client.get("/api/reports/capacity", headers=auth_headers)
        data = response.json()["data"]
        assert data["total_vehicles"] == 5
        assert data["idle_count"] == 4
        assert data["delivering_count"] == 1
        assert data["dispatch_count"] == 1
        assert data["package_count"] == 2
        assert data["delivered_package_count"] == 1


@pytest.mark.api
@pytest.mark.phase5
class TestReportOverview:
    def test_overview_contains_all_sections(self, client, auth_headers, db_session,
                                            test_nodes):
        """overview 聚合四类报表"""
        _make_order(db_session, test_nodes["SO010"].id, "signed",
                    datetime.now() - timedelta(hours=1), code="O_OV")
        db_session.commit()

        response = client.get("/api/reports/overview", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "sla" in data and "cost" in data
        assert "exceptions" in data and "capacity" in data
        assert data["sla"]["total_orders"] == 1
