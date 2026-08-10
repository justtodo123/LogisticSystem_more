"""
地图服务测试（T5-2）

覆盖三档距离来源：
- haversine：未配置 API Key / 关闭近似 → 直线距离
- approx：MAP_ROAD_APPROX=true → 直线 × 系数
- road：配置 provider+key → 真实路网 API（mock），失败自动降级
"""
import math

import pytest

from config.settings import settings
from services import map_service


def _straight(lat1, lng1, lat2, lng2):
    """独立实现直线距离用于断言"""
    return map_service._haversine(lat1, lng1, lat2, lng2)


# 测试坐标：武汉存储中心 → 武汉 1 级分拣中心（约 1~2 km）
LAT1, LNG1, LAT2, LNG2 = 30.580000, 114.300000, 30.590000, 114.310000


@pytest.mark.unit
class TestMapServiceFallback:
    def test_default_haversine(self, monkeypatch):
        """默认配置：source=haversine，距离为直线距离"""
        monkeypatch.setattr(settings, "MAP_PROVIDER", "")
        monkeypatch.setattr(settings, "MAP_API_KEY", "")
        monkeypatch.setattr(settings, "MAP_ROAD_APPROX", False)

        result = map_service.get_route_distance(LAT1, LNG1, LAT2, LNG2)
        expected = _straight(LAT1, LNG1, LAT2, LNG2)
        assert result["source"] == "haversine"
        assert result["distance_km"] == pytest.approx(round(expected, 3))
        # ETA = 距离 / 60km/h × 60
        assert result["duration_minutes"] == pytest.approx(
            round(expected / settings.MAP_AVG_SPEED_KMH * 60, 2)
        )

    def test_approx_road_factor(self, monkeypatch):
        """MAP_ROAD_APPROX=true：距离 = 直线 × 系数，标识为估算道路"""
        monkeypatch.setattr(settings, "MAP_PROVIDER", "")
        monkeypatch.setattr(settings, "MAP_API_KEY", "")
        monkeypatch.setattr(settings, "MAP_ROAD_APPROX", True)
        monkeypatch.setattr(settings, "MAP_ROAD_FACTOR", 1.3)

        result = map_service.get_route_distance(LAT1, LNG1, LAT2, LNG2)
        straight = _straight(LAT1, LNG1, LAT2, LNG2)
        assert result["source"] == "approx"
        assert result["distance_km"] == pytest.approx(round(straight * 1.3, 3))

    def test_is_road_enabled_false_without_key(self, monkeypatch):
        """无 key 时 road 不启用"""
        monkeypatch.setattr(settings, "MAP_PROVIDER", "amap")
        monkeypatch.setattr(settings, "MAP_API_KEY", "")
        assert map_service.is_road_enabled() is False

    def test_haversine_math(self):
        """Haversine 基准：武汉→长沙直线约 290~300 km"""
        dist = map_service._haversine(30.580000, 114.300000, 28.220000, 112.930000)
        assert 285 < dist < 305


@pytest.mark.unit
class TestMapServiceRoad:
    def test_road_source_and_cache(self, monkeypatch):
        """配置高德 key：调用 API（mock），结果缓存，二次调用命中缓存"""
        monkeypatch.setattr(settings, "MAP_PROVIDER", "amap")
        monkeypatch.setattr(settings, "MAP_API_KEY", "fake-key")

        call_count = 0

        def fake_call(lat1, lng1, lat2, lng2, mode):
            nonlocal call_count
            call_count += 1
            return 12.5, 1800  # 12.5km, 30min

        monkeypatch.setattr(map_service, "_call_amap", fake_call)

        r1 = map_service.get_route_distance(LAT1, LNG1, LAT2, LNG2)
        assert r1["source"] == "road"
        assert r1["distance_km"] == 12.5
        assert r1["duration_minutes"] == 30.0

        # 缓存命中，不再调用 API
        r2 = map_service.get_route_distance(LAT1, LNG1, LAT2, LNG2)
        assert r2 == r1
        assert call_count == 1

    def test_road_api_failure_falls_back(self, monkeypatch):
        """真实 API 抛异常 → 降级直线距离，不阻断"""
        monkeypatch.setattr(settings, "MAP_PROVIDER", "amap")
        monkeypatch.setattr(settings, "MAP_API_KEY", "fake-key")
        monkeypatch.setattr(settings, "MAP_ROAD_APPROX", False)

        def failing_call(lat1, lng1, lat2, lng2, mode):
            raise ValueError("网络超时")

        monkeypatch.setattr(map_service, "_call_amap", failing_call)

        result = map_service.get_route_distance(LAT1, LNG1, LAT2, LNG2)
        assert result["source"] == "haversine"
        assert result["distance_km"] == pytest.approx(
            round(_straight(LAT1, LNG1, LAT2, LNG2), 3)
        )

    def test_road_zero_distance_fallback(self, monkeypatch):
        """API 返回 0 距离（同点）→ 兜底直线距离"""
        monkeypatch.setattr(settings, "MAP_PROVIDER", "amap")
        monkeypatch.setattr(settings, "MAP_API_KEY", "fake-key")

        monkeypatch.setattr(
            map_service, "_call_amap",
            lambda *a, **k: (0.0, 0),
        )
        result = map_service.get_route_distance(LAT1, LNG1, LAT2, LNG2)
        assert result["source"] == "road"
        assert result["distance_km"] == pytest.approx(
            round(_straight(LAT1, LNG1, LAT2, LNG2), 3)
        )

    def test_unsupported_provider_falls_back(self, monkeypatch):
        """不支持的 provider → 降级"""
        monkeypatch.setattr(settings, "MAP_PROVIDER", "google")
        monkeypatch.setattr(settings, "MAP_API_KEY", "x")
        result = map_service.get_route_distance(LAT1, LNG1, LAT2, LNG2)
        assert result["source"] == "haversine"
