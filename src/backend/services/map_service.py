"""
地图服务（T5-2）：路网距离 / ETA 计算，无 API Key 时降级

距离来源三档：
1. road     — 配置了 MAP_PROVIDER + MAP_API_KEY，走真实路网 API（高德/百度），结果缓存 1h
2. approx   — MAP_ROAD_APPROX=true 时，直线距离 × MAP_ROAD_FACTOR 估算道路距离
3. haversine— 纯直线距离（默认，保持既有行为）

所有真实 API 失败均自动降级到直线距离，不阻断调度主流程。
"""
import json
import math
import urllib.parse
import urllib.request

from config.settings import settings
from core.dependency import outbound_trace_headers, track_dependency
from utils.cache import memory_cache

# 路网距离结果缓存 TTL（秒）：真实 API 结果波动小，缓存 1 小时
ROAD_CACHE_TTL = 3600
CACHE_PREFIX = "map:dist"

# 距离来源文案（用于 route_segments.road_name）
SOURCE_LABEL = {
    "road": "真实道路导航",
    "approx": "估算道路",
    "haversine": "虚拟道路",
}


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Haversine 公式计算两点间球面距离（公里）"""
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    a = (math.sin(delta_phi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def is_road_enabled() -> bool:
    """是否启用真实路网距离（provider 与 key 均已配置）"""
    return bool(settings.MAP_PROVIDER and settings.MAP_API_KEY)


def _cache_key(lat1: float, lng1: float, lat2: float, lng2: float, mode: str) -> str:
    return f"{CACHE_PREFIX}:{mode}:{lat1:.6f}|{lng1:.6f}|{lat2:.6f}|{lng2:.6f}"


def _call_amap(lat1, lng1, lat2, lng2, mode: str):
    """调用高德 Web 服务 API，返回 (distance_km, duration_seconds)

    Raises:
        Exception: 网络/参数/返回异常，由调用方降级处理
    """
    if mode == "walking":
        url = "https://restapi.amap.com/v3/direction/walking"
    else:
        url = "https://restapi.amap.com/v3/direction/driving"
    params = {
        "origin": f"{lng1},{lat1}",
        "destination": f"{lng2},{lat2}",
        "key": settings.MAP_API_KEY,
    }
    query = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        query,
        headers=outbound_trace_headers({"User-Agent": "logistics-platform"}),
    )
    with track_dependency("map", "amap"):
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    if body.get("status") != "1":
        raise ValueError(f"高德返回异常: {body.get('info')}")
    path = (body.get("route") or {}).get("paths") or []
    if not path:
        raise ValueError("高德无可用路径")
    return float(path[0].get("distance", 0)) / 1000.0, float(path[0].get("duration", 0))


def _call_baidu(lat1, lng1, lat2, lng2, mode: str):
    """调用百度地图 Web 服务 API（方向骑行/驾车），返回 (distance_km, duration_seconds)"""
    endpoint = "walking" if mode == "walking" else "driving"
    url = f"https://api.map.baidu.com/directionlite/v1/{endpoint}"
    params = {
        "origin": f"{lat1},{lng1}",
        "destination": f"{lat2},{lng2}",
        "ak": settings.MAP_API_KEY,
    }
    query = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        query,
        headers=outbound_trace_headers({"User-Agent": "logistics-platform"}),
    )
    with track_dependency("map", "baidu"):
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    if body.get("status") != 0:
        raise ValueError(f"百度返回异常: {body.get('message')}")
    result = body.get("result") or {}
    routes = result.get("routes") or []
    if not routes:
        raise ValueError("百度无可用路径")
    return float(routes[0].get("distance", 0)) / 1000.0, float(routes[0].get("duration", 0))


def _fallback(lat1, lng1, lat2, lng2):
    """直线距离降级：返回 (distance_km, duration_minutes, source)"""
    straight = _haversine(lat1, lng1, lat2, lng2)
    if settings.MAP_ROAD_APPROX:
        dist = straight * settings.MAP_ROAD_FACTOR
        return round(dist, 3), round(dist / settings.MAP_AVG_SPEED_KMH * 60, 2), "approx"
    return (
        round(straight, 3),
        round(straight / settings.MAP_AVG_SPEED_KMH * 60, 2),
        "haversine",
    )


def get_route_distance(lat1: float, lng1: float, lat2: float, lng2: float,
                       mode: str = "driving") -> dict:
    """计算两点间距离与 ETA

    Returns:
        {
            "distance_km": float,      # 公里
            "duration_minutes": float, # 分钟
            "source": "road"|"approx"|"haversine",
        }
    """
    # 未启用真实路网 → 直接降级
    if not is_road_enabled():
        dist, dur, source = _fallback(lat1, lng1, lat2, lng2)
        return {"distance_km": dist, "duration_minutes": dur, "source": source}

    key = _cache_key(lat1, lng1, lat2, lng2, mode)
    cached = memory_cache.get(key)
    if cached is not None:
        return {**cached, "source": "road"}

    try:
        if settings.MAP_PROVIDER == "amap":
            dist, dur_s = _call_amap(lat1, lng1, lat2, lng2, mode)
        elif settings.MAP_PROVIDER == "baidu":
            dist, dur_s = _call_baidu(lat1, lng1, lat2, lng2, mode)
        else:
            raise ValueError(f"不支持的 MAP_PROVIDER: {settings.MAP_PROVIDER}")
        straight = _haversine(lat1, lng1, lat2, lng2)
        if dist <= 0:
            dist = straight  # 同点/异常距离兜底
        dur_min = dur_s / 60.0 if dur_s > 0 else straight / settings.MAP_AVG_SPEED_KMH * 60
        payload = {
            "distance_km": round(dist, 3),
            "duration_minutes": round(dur_min, 2),
        }
        memory_cache.set(key, payload, ROAD_CACHE_TTL)
        return {**payload, "source": "road"}
    except Exception:
        # 网络失败/参数错误 → 降级直线距离，不阻断主流程
        dist, dur, source = _fallback(lat1, lng1, lat2, lng2)
        return {"distance_km": dist, "duration_minutes": dur, "source": source}
