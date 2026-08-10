"""
方案差异对比服务（T3-1 重规划增强）

重规划完成后，自动对比原方案与新方案，生成差异报告：
- affected_count: 新方案重排的包裹数（受影响范围）
- new_eta_delta: 新方案总时长 - 原方案总时长（小时，正数=耗时更长）
- cost_delta: 估算成本变化 = 距离差 × 每公里成本（元，正数=成本上升）
"""

from typing import Dict, Any, Optional

from sqlalchemy.orm import Session

from models.global_schedule import GlobalSchedule
from models.package import Package


def _load_cost_per_km() -> float:
    """加载每公里运输成本（元/km），与 global_schedule cost 目标同源"""
    from algorithms.global_schedule import _cost_per_km

    return _cost_per_km()


def build_diff_report(
    db: Session,
    original: GlobalSchedule,
    new_schedule: GlobalSchedule,
    strategy: str = "full",
) -> Dict[str, Any]:
    """
    生成重规划差异报告（old vs new）。

    Args:
        db: 数据库会话
        original: 原调度方案
        new_schedule: 重规划后的新调度方案
        strategy: 本次重规划策略（partial/full/hybrid）

    Returns:
        diff_summary: {
            "strategy": str,
            "affected_count": int,     # 新方案重排包裹数
            "new_eta_delta": float,    # 总时长变化（小时）
            "cost_delta": float,       # 估算成本变化（元）
        }
    """
    affected_count = (
        db.query(Package).filter(Package.schedule_id == new_schedule.id).count()
    )
    new_eta_delta = round(
        float(new_schedule.total_time) - float(original.total_time), 3
    )
    distance_delta = float(new_schedule.total_distance) - float(original.total_distance)
    cost_delta = round(distance_delta * _load_cost_per_km(), 2)

    return {
        "strategy": strategy,
        "affected_count": affected_count,
        "new_eta_delta": new_eta_delta,
        "cost_delta": cost_delta,
    }
