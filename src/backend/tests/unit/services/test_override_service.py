"""
服务单元测试：人工干预调度（T2-4）

测试目标：
- override_vehicle: 换车成功 / 容量拒绝 / 时窗拒绝 / 同车拒绝 / 明细不存在
- override_driver: 换司机成功 / 驾时拒绝 / 节点不匹配拒绝
- recalculate_after_override: 仅重算已干预明细
- undo_override: 恢复到调整前状态 / 无干预不可撤销
"""
import json
from datetime import datetime, timedelta

import pytest

from models.global_schedule import GlobalSchedule
from models.dispatch_batch import DispatchBatch
from models.node_dispatch import NodeDispatch
from models.route import Route
from models.package import Package
from models.vehicle import Vehicle
from models.driver import Driver
from services.override_service import OverrideService


def _create_dispatch(
    db_session,
    test_nodes,
    test_vehicles,
    test_drivers,
    dispatch_code="ND_OVR001",
    vehicle_key="VEH001",
    driver_key="DRV001",
    package_weight=10.0,
    total_time=1.0,
):
    """构造：GlobalSchedule → DispatchBatch → NodeDispatch → Package → 原始 Route(v1)"""
    gs = GlobalSchedule(
        schedule_code="GS_OVR001",
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
        batch_code="BATCH_OVR001",
        global_schedule_id=gs.id,
        status="pending",
    )
    db_session.add(batch)
    db_session.commit()

    vehicle = test_vehicles[vehicle_key]
    driver = test_drivers[driver_key]
    dispatch = NodeDispatch(
        dispatch_code=dispatch_code,
        dispatch_batch_id=batch.id,
        vehicle_id=vehicle.id,
        driver_id=driver.id,
        level_phase=0,
        tasks=json.dumps([
            {"from_node_code": "SC001", "to_node_code": "SO010",
             "package_codes": ["PKG_OVR1"], "is_return": False},
            {"from_node_code": "SO010", "to_node_code": "SC001",
             "package_codes": [], "is_return": True},
        ]),
        total_distance=10.0,
        total_time=total_time,
    )
    db_session.add(dispatch)
    db_session.commit()

    pkg = Package(
        package_code="PKG_OVR1",
        weight=package_weight,
        volume=0.5,
        from_node_id=test_nodes["SC001"].id,
        to_node_id=test_nodes["SO010"].id,
        goods_items=json.dumps([]),
        dispatch_id=dispatch.id,
    )
    db_session.add(pkg)
    db_session.commit()

    # 原始路线 v1
    route = Route(
        route_code="RT_OVR001",
        dispatch_id=dispatch.id,
        vehicle_id=vehicle.id,
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


class TestOverrideVehicle:
    """更换调度车辆"""

    @pytest.mark.unit
    def test_override_vehicle_success(self, db_session, test_nodes, test_vehicles, test_drivers):
        """换车成功：更新分配 + 自动重算路线（新版本）"""
        gs, batch, dispatch = _create_dispatch(db_session, test_nodes, test_vehicles, test_drivers)
        new_vehicle = test_vehicles["VEH002"]

        result = OverrideService.override_vehicle(
            db_session, dispatch.id, new_vehicle.id, reason="测试换车"
        )

        assert result["code"] == 0
        data = result["data"]
        assert data["vehicle_code"] == "VEH002"
        assert data["recalculated"] is True
        assert data["can_undo"] is True

        db_session.refresh(dispatch)
        assert dispatch.vehicle_id == new_vehicle.id
        assert dispatch.version == 2
        assert dispatch.override_snapshot is not None
        assert dispatch.override_snapshot["vehicle_id"] == test_vehicles["VEH001"].id

        # 新路线版本 v2，绑定新车辆，electric → 零排放
        routes = (
            db_session.query(Route)
            .filter(Route.dispatch_id == dispatch.id)
            .order_by(Route.version.asc())
            .all()
        )
        assert len(routes) == 2
        new_route = routes[1]
        assert new_route.version == 2
        assert new_route.vehicle_id == new_vehicle.id
        assert new_route.is_replan is True
        assert new_route.replan_reason == "测试换车"
        assert float(new_route.total_emission) == 0.0  # electric

    @pytest.mark.unit
    def test_override_vehicle_rejects_capacity(self, db_session, test_nodes, test_vehicles, test_drivers):
        """容量不满足：包裹总重 > 新车辆有效载重 → 拒绝并提示原因"""
        # 大包裹（100kg）挂在 VEH002（有效载重 200*0.9=180）上，换到 VEH001（有效载重 90）应拒绝
        gs, batch, dispatch = _create_dispatch(
            db_session, test_nodes, test_vehicles, test_drivers,
            vehicle_key="VEH002", package_weight=100.0,
        )
        small_vehicle = test_vehicles["VEH001"]

        result = OverrideService.override_vehicle(db_session, dispatch.id, small_vehicle.id)

        assert result["code"] != 0
        assert "拒绝" in result["message"]
        assert "载重" in result["message"]
        # 分配未被修改
        db_session.refresh(dispatch)
        assert dispatch.vehicle_id == test_vehicles["VEH002"].id
        assert dispatch.override_snapshot is None

    @pytest.mark.unit
    def test_override_vehicle_rejects_time_window(self, db_session, test_nodes, test_vehicles, test_drivers):
        """时窗不满足：新车辆当前不在可用时段 → 拒绝"""
        gs, batch, dispatch = _create_dispatch(db_session, test_nodes, test_vehicles, test_drivers)

        # 构造一个可用时段位于过去 2 小时的车辆（当前时刻必然不在窗口内）
        now = datetime.now()
        past_start = (now - timedelta(hours=2)).time()
        past_end = (now - timedelta(hours=1)).time()
        windowed = Vehicle(
            vehicle_code="VEH_WINDOW",
            model="测试车型",
            capacity=200.0,
            energy_type="fuel",
            node_id=test_nodes["SC001"].id,
            last_arrived_node_id=test_nodes["SC001"].id,
            status="idle",
            time_window_start=past_start,
            time_window_end=past_end,
        )
        db_session.add(windowed)
        db_session.commit()

        result = OverrideService.override_vehicle(db_session, dispatch.id, windowed.id)

        assert result["code"] != 0
        assert "可用时段" in result["message"]

    @pytest.mark.unit
    def test_override_vehicle_same_vehicle_rejected(self, db_session, test_nodes, test_vehicles, test_drivers):
        """目标车辆与当前车辆相同 → 拒绝"""
        gs, batch, dispatch = _create_dispatch(db_session, test_nodes, test_vehicles, test_drivers)

        result = OverrideService.override_vehicle(db_session, dispatch.id, test_vehicles["VEH001"].id)

        assert result["code"] != 0
        assert "相同" in result["message"]

    @pytest.mark.unit
    def test_override_vehicle_dispatch_not_found(self, db_session, test_vehicles):
        """调度明细不存在 → 40400"""
        result = OverrideService.override_vehicle(db_session, 99999, test_vehicles["VEH002"].id)
        assert result["code"] == 40400

    @pytest.mark.unit
    def test_override_vehicle_target_not_found(self, db_session, test_nodes, test_vehicles, test_drivers):
        """目标车辆不存在 → 40400"""
        gs, batch, dispatch = _create_dispatch(db_session, test_nodes, test_vehicles, test_drivers)
        result = OverrideService.override_vehicle(db_session, dispatch.id, 99999)
        assert result["code"] == 40400


class TestOverrideDriver:
    """更换调度司机"""

    @pytest.mark.unit
    def test_override_driver_success(self, db_session, test_nodes, test_vehicles, test_drivers):
        """换司机成功：更新分配并 bump version"""
        gs, batch, dispatch = _create_dispatch(db_session, test_nodes, test_vehicles, test_drivers)
        new_driver = test_drivers["DRV002"]  # 同属 SC001

        result = OverrideService.override_driver(db_session, dispatch.id, new_driver.id)

        assert result["code"] == 0
        assert result["data"]["driver_code"] == "DRV002"
        db_session.refresh(dispatch)
        assert dispatch.driver_id == new_driver.id
        assert dispatch.version == 2

    @pytest.mark.unit
    def test_override_driver_rejects_drive_hours(self, db_session, test_nodes, test_vehicles, test_drivers):
        """驾时不满足：任务时长 > 单日最大驾驶时长 → 拒绝"""
        gs, batch, dispatch = _create_dispatch(
            db_session, test_nodes, test_vehicles, test_drivers, total_time=3.0,
        )
        tired_driver = Driver(
            driver_code="DRV_TIRED",
            name="疲劳司机",
            phone="13800000009",
            license_type="C1",
            shift="day",
            node_id=test_nodes["SC001"].id,  # 与车辆同节点，仅触发驾时约束
            status="idle",
            max_drive_hours=1.0,
        )
        db_session.add(tired_driver)
        db_session.commit()

        result = OverrideService.override_driver(db_session, dispatch.id, tired_driver.id)

        assert result["code"] != 0
        assert "驾驶时长" in result["message"]
        db_session.refresh(dispatch)
        assert dispatch.driver_id == test_drivers["DRV001"].id

    @pytest.mark.unit
    def test_override_driver_rejects_node_mismatch(self, db_session, test_nodes, test_vehicles, test_drivers):
        """节点不匹配：司机不在车辆所在节点 → 拒绝"""
        gs, batch, dispatch = _create_dispatch(db_session, test_nodes, test_vehicles, test_drivers)
        # DRV003 位于 SO001，车辆 VEH001 位于 SC001
        result = OverrideService.override_driver(db_session, dispatch.id, test_drivers["DRV003"].id)

        assert result["code"] != 0
        assert "所在节点" in result["message"]


class TestRecalculateOverride:
    """批量重算已干预明细"""

    @pytest.mark.unit
    def test_recalculate_after_override(self, db_session, test_nodes, test_vehicles, test_drivers):
        """换车后重算：仅处理 override_snapshot 非空的明细"""
        gs, batch, dispatch = _create_dispatch(db_session, test_nodes, test_vehicles, test_drivers)
        OverrideService.override_vehicle(db_session, dispatch.id, test_vehicles["VEH002"].id)

        result = OverrideService.recalculate_after_override(db_session, batch.id)

        assert result["code"] == 0
        assert result["data"]["batch_code"] == batch.batch_code
        assert result["data"]["recalculated_count"] >= 1
        assert result["data"]["dispatches"][0]["dispatch_code"] == dispatch.dispatch_code

    @pytest.mark.unit
    def test_recalculate_batch_not_found(self, db_session):
        """批次不存在 → 40400"""
        result = OverrideService.recalculate_after_override(db_session, 99999)
        assert result["code"] == 40400


class TestUndoOverride:
    """撤销干预"""

    @pytest.mark.unit
    def test_undo_restores_original_state(self, db_session, test_nodes, test_vehicles, test_drivers):
        """撤销恢复到调整前：车辆/司机还原 + 路线回退 v1 + undo_version 自增"""
        gs, batch, dispatch = _create_dispatch(db_session, test_nodes, test_vehicles, test_drivers)
        # 先换车再撤销
        OverrideService.override_vehicle(db_session, dispatch.id, test_vehicles["VEH002"].id)
        db_session.refresh(dispatch)
        assert dispatch.version == 2

        result = OverrideService.undo_override(db_session, dispatch.id)

        assert result["code"] == 0
        db_session.refresh(dispatch)
        assert dispatch.vehicle_id == test_vehicles["VEH001"].id
        assert dispatch.driver_id == test_drivers["DRV001"].id
        assert dispatch.override_snapshot is None
        assert dispatch.version == 3

        # 路线回退：仅保留原始 v1
        routes = (
            db_session.query(Route)
            .filter(Route.dispatch_id == dispatch.id)
            .order_by(Route.version.asc())
            .all()
        )
        assert len(routes) == 1
        assert routes[0].version == 1
        assert routes[0].vehicle_id == test_vehicles["VEH001"].id

        # GlobalSchedule.undo_version 自增
        db_session.refresh(gs)
        assert gs.undo_version == 1

    @pytest.mark.unit
    def test_undo_without_override_rejected(self, db_session, test_nodes, test_vehicles, test_drivers):
        """无干预记录时撤销 → 业务错误"""
        gs, batch, dispatch = _create_dispatch(db_session, test_nodes, test_vehicles, test_drivers)
        result = OverrideService.undo_override(db_session, dispatch.id)
        assert result["code"] != 0
        assert "无人工干预记录" in result["message"]
