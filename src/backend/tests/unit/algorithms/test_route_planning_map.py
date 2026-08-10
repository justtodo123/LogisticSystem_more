"""
路径规划地图距离测试（T5-2）

验证 run_route_planning 接入 map_service 后：
- 默认（无 API Key / 未开近似）：保持直线距离，road_name=虚拟道路，无 real_distance
- MAP_ROAD_APPROX=true：road_name=估算道路，total_distance 大于直线，段含 real_distance/eta_minutes
"""
import pytest

from config.settings import settings
from algorithms.route_planning import run_route_planning
from services import map_service
from models.node_dispatch import NodeDispatch
from models.vehicle import Vehicle


def _create_dispatch(db_session, test_vehicles, dispatch_code="ND_MAP001"):
    dispatch = NodeDispatch(
        dispatch_code=dispatch_code,
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
    return dispatch


@pytest.mark.unit
class TestRoutePlanningMapDistance:
    def test_default_straight_line(self, db_session, test_nodes, test_vehicles, monkeypatch):
        """默认：直线距离（Haversine），road_name=虚拟道路"""
        monkeypatch.setattr(settings, "MAP_PROVIDER", "")
        monkeypatch.setattr(settings, "MAP_API_KEY", "")
        monkeypatch.setattr(settings, "MAP_ROAD_APPROX", False)

        dispatch = _create_dispatch(db_session, test_vehicles)
        result = run_route_planning(db_session, dispatch.id)

        expected = round(
            map_service._haversine(
                test_nodes["SC001"].latitude, test_nodes["SC001"].longitude,
                test_nodes["SO001"].latitude, test_nodes["SO001"].longitude,
            ), 3,
        )
        assert result["total_distance"] == expected
        assert result["route_segments"][0]["road_name"] == "虚拟道路"
        assert "real_distance" not in result["route_segments"][0]

    def test_approx_road_distance(self, db_session, test_nodes, test_vehicles, monkeypatch):
        """近似道路：距离 = 直线 × 系数，段含 real_distance/eta_minutes"""
        monkeypatch.setattr(settings, "MAP_PROVIDER", "")
        monkeypatch.setattr(settings, "MAP_API_KEY", "")
        monkeypatch.setattr(settings, "MAP_ROAD_APPROX", True)
        monkeypatch.setattr(settings, "MAP_ROAD_FACTOR", 1.3)

        dispatch = _create_dispatch(db_session, test_vehicles)
        result = run_route_planning(db_session, dispatch.id)

        straight = map_service._haversine(
            test_nodes["SC001"].latitude, test_nodes["SC001"].longitude,
            test_nodes["SO001"].latitude, test_nodes["SO001"].longitude,
        )
        assert result["total_distance"] == pytest.approx(round(straight * 1.3, 3))
        seg = result["route_segments"][0]
        assert seg["road_name"] == "估算道路"
        assert seg["real_distance"] == pytest.approx(round(straight * 1.3, 3))
        assert "eta_minutes" in seg
        assert result["total_time"] > 0

    def test_road_enabled_segment(self, db_session, test_nodes, test_vehicles, monkeypatch):
        """真实路网（mock）：road_name=真实道路导航，段含 real_distance"""
        monkeypatch.setattr(settings, "MAP_PROVIDER", "amap")
        monkeypatch.setattr(settings, "MAP_API_KEY", "fake-key")
        monkeypatch.setattr(
            map_service, "_call_amap",
            lambda *a, **k: (15.0, 2700),  # 15km, 45min
        )

        dispatch = _create_dispatch(db_session, test_vehicles)
        result = run_route_planning(db_session, dispatch.id)

        seg = result["route_segments"][0]
        assert seg["road_name"] == "真实道路导航"
        assert seg["real_distance"] == 15.0
        assert seg["eta_minutes"] == 45.0
        assert result["total_distance"] == 15.0
