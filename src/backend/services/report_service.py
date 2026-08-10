"""
报表分析服务（T5-3）

4 类报表：
- SLA 达成率：准点率、平均延迟（已签收订单完成耗时 vs SLA 目标）
- 成本分析：按车辆（线路）/ 节点汇总成本（距离 × 每公里成本）
- 异常统计：按异常类型 / 子类型分布，open/resolved
- 运力效率：车辆状态、调度批次、包裹流转、平均行驶距离

统一返回 {code, message, data} 结构。
"""
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from config.settings import settings
from core.error_codes import CODE_SUCCESS, CODE_PARAM_ERROR
from models.exception_event import ExceptionEvent
from models.node import Node
from models.node_dispatch import NodeDispatch
from models.order import Order
from models.package import Package
from models.route import Route
from models.vehicle import Vehicle

# 订单状态（用于 SLA 统计）
_PROGRESS_STATUSES = ("unassigned", "assigned", "in_transit")


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    """解析 ISO 日期/时间；非法返回 None 由调用方报参数错误"""
    if not value:
        return None
    return datetime.fromisoformat(value)


# ── SLA 达成率 ────────────────────────────────────────────

def get_sla_report(date_from: Optional[str], date_to: Optional[str], db: Session) -> Dict[str, Any]:
    """SLA 达成率：准点率、平均延迟"""
    try:
        from_dt = _parse_date(date_from)
        to_dt = _parse_date(date_to)
    except ValueError:
        return {
            "code": CODE_PARAM_ERROR,
            "message": "日期格式错误，应为 ISO 格式（如 2026-06-15）",
            "data": None,
        }

    query = db.query(Order)
    if from_dt is not None:
        query = query.filter(Order.created_at >= from_dt)
    if to_dt is not None:
        query = query.filter(Order.created_at <= to_dt)
    orders = query.all()

    total = len(orders)
    signed_orders = [o for o in orders if o.status == "signed"]
    exception_count = sum(1 for o in orders if o.status == "exception")
    in_progress_count = sum(1 for o in orders if o.status in _PROGRESS_STATUSES)

    # 准点：已签收订单完成耗时 ≤ SLA 目标；延迟 = 超出目标的部分
    sla_target_hours = settings.SLA_TARGET_HOURS
    on_time = 0
    excess_hours = []
    for o in signed_orders:
        dur_hours = (o.updated_at - o.created_at).total_seconds() / 3600
        if dur_hours <= sla_target_hours:
            on_time += 1
        else:
            excess_hours.append(dur_hours - sla_target_hours)

    on_time_rate = round(on_time / len(signed_orders), 4) if signed_orders else 0.0
    avg_delay_minutes = (
        round(sum(excess_hours) / len(excess_hours) * 60, 2) if excess_hours else 0.0
    )

    return {
        "code": CODE_SUCCESS,
        "message": "success",
        "data": {
            "date_from": date_from,
            "date_to": date_to,
            "total_orders": total,
            "signed_orders": len(signed_orders),
            "in_progress_orders": in_progress_count,
            "exception_orders": exception_count,
            "on_time_rate": on_time_rate,
            "avg_delay_minutes": avg_delay_minutes,
            "sla_target_hours": sla_target_hours,
        },
    }


# ── 成本分析 ──────────────────────────────────────────────

def get_cost_report(db: Session) -> Dict[str, Any]:
    """成本分析：按车辆（线路）/ 节点汇总（距离 × cost_per_km）"""
    routes = db.query(Route).all()
    vehicles = {v.id: v for v in db.query(Vehicle).all()}
    nodes = {n.id: n for n in db.query(Node).all()}

    total_cost = 0.0
    by_vehicle: Dict[str, dict] = {}
    by_node: Dict[str, dict] = {}

    for route in routes:
        veh = vehicles.get(route.vehicle_id)
        cost_per_km = float(veh.cost_per_km) if veh else 5.0
        distance = float(route.total_distance)
        cost = distance * cost_per_km
        total_cost += cost

        veh_code = veh.vehicle_code if veh else f"V{route.vehicle_id}"
        v_entry = by_vehicle.setdefault(
            veh_code, {"vehicle_code": veh_code, "distance_km": 0.0, "cost": 0.0, "route_count": 0}
        )
        v_entry["distance_km"] += distance
        v_entry["cost"] += cost
        v_entry["route_count"] += 1

        if veh:
            node = nodes.get(veh.node_id)
            node_code = node.node_code if node else "未知节点"
        else:
            node_code = "未知节点"
        n_entry = by_node.setdefault(
            node_code, {"node_code": node_code, "cost": 0.0, "route_count": 0}
        )
        n_entry["cost"] += cost
        n_entry["route_count"] += 1

    return {
        "code": CODE_SUCCESS,
        "message": "success",
        "data": {
            "total_cost": round(total_cost, 2),
            "by_vehicle": sorted(by_vehicle.values(), key=lambda x: -x["cost"]),
            "by_node": sorted(by_node.values(), key=lambda x: -x["cost"]),
        },
    }


# ── 异常统计 ──────────────────────────────────────────────

def get_exception_report(db: Session) -> Dict[str, Any]:
    """异常统计：类型 / 子类型分布，open/resolved"""
    events = db.query(ExceptionEvent).all()

    by_type: Dict[str, int] = {}
    by_subtype: Dict[str, int] = {}
    open_count = 0
    resolved_count = 0
    for e in events:
        if e.status == "resolved":
            resolved_count += 1
        else:
            open_count += 1
        t = e.exception_type or "unknown"
        by_type[t] = by_type.get(t, 0) + 1
        st = e.exception_subtype or "unknown"
        by_subtype[st] = by_subtype.get(st, 0) + 1

    return {
        "code": CODE_SUCCESS,
        "message": "success",
        "data": {
            "total_exceptions": len(events),
            "open_count": open_count,
            "resolved_count": resolved_count,
            "by_type": sorted(
                [{"type": k, "count": v} for k, v in by_type.items()],
                key=lambda x: -x["count"],
            ),
            "by_subtype": sorted(
                [{"subtype": k, "count": v} for k, v in by_subtype.items()],
                key=lambda x: -x["count"],
            ),
        },
    }


# ── 运力效率 ──────────────────────────────────────────────

def get_capacity_report(db: Session) -> Dict[str, Any]:
    """运力效率：车辆状态、调度、包裹流转、平均行驶距离"""
    vehicles = db.query(Vehicle).all()
    total_vehicles = len(vehicles)
    idle_count = sum(1 for v in vehicles if v.status == "idle")
    delivering_count = sum(1 for v in vehicles if v.status == "delivering")

    dispatch_count = db.query(NodeDispatch).count()
    package_count = db.query(Package).count()
    delivered_package_count = (
        db.query(Package).filter(Package.status == "delivered").count()
    )

    routes = db.query(Route).all()
    avg_distance_km = (
        round(sum(float(r.total_distance) for r in routes) / len(routes), 2)
        if routes
        else 0.0
    )

    return {
        "code": CODE_SUCCESS,
        "message": "success",
        "data": {
            "total_vehicles": total_vehicles,
            "idle_count": idle_count,
            "delivering_count": delivering_count,
            "dispatch_count": dispatch_count,
            "package_count": package_count,
            "delivered_package_count": delivered_package_count,
            "avg_distance_km": avg_distance_km,
        },
    }


# ── 汇总（供前端 Dashboard 一次拉取）────────────────────────

def get_overview(
    date_from: Optional[str], date_to: Optional[str], db: Session
) -> Dict[str, Any]:
    """汇总四类报表数据，供 Dashboard 展示"""
    sla = get_sla_report(date_from, date_to, db)
    if sla["code"] != CODE_SUCCESS:
        return sla
    return {
        "code": CODE_SUCCESS,
        "message": "success",
        "data": {
            "sla": sla["data"],
            "cost": get_cost_report(db)["data"],
            "exceptions": get_exception_report(db)["data"],
            "capacity": get_capacity_report(db)["data"],
        },
    }
