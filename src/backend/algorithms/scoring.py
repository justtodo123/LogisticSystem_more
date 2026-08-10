"""
多目标评分引擎（T2-2）

对多个候选调度方案进行多目标综合评价：
1. 采集各目标原始指标（distance / time / load_rate / on_time_rate / cost 等）
2. 跨候选 min-max 归一化（direction 决定高分方向：minimize 低值优，maximize 高值优）
3. 按 `global_schedule_objectives` 权重加权求和 → 0~1 综合分
4. 按综合分降序排序，返回带分项评分的排名

使用示例：
    candidates = [
        {"profile": "balanced", "metrics": {"distance": 120, "time": 3.2, ...}},
        {"profile": "distance_first", "metrics": {"distance": 118, "time": 3.4, ...}},
    ]
    ranked = rank_candidates(candidates, objectives_config)
"""
from typing import Dict, List, Any


def normalize_scores(candidates: List[float], direction: str) -> List[float]:
    """
    min-max 归一化（0~1）。

    Args:
        candidates: 某目标在多个候选方案上的原始值列表
        direction: "minimize"（越低越好，归一化后反向）或 "maximize"（越高越好）

    Returns:
        归一化分数列表；单样本或全部相等时返回 0.5 中性分（无法跨候选区分）
    """
    if not candidates:
        return []
    lo, hi = min(candidates), max(candidates)
    if hi == lo:
        return [0.5] * len(candidates)
    norm = [(v - lo) / (hi - lo) for v in candidates]
    if direction == "minimize":
        # 低值 → 高分
        return [1.0 - v for v in norm]
    return norm


def weighted_score(
    objective_scores: Dict[str, float],
    objectives_config: Dict[str, Dict[str, Any]],
) -> float:
    """
    按权重加权平均各目标的归一化分，返回 0~1 综合分。

    Args:
        objective_scores: {objective_name: 归一化分(0~1)}
        objectives_config: {objective_name: {"weight": float, "direction": str, "metric": str}}

    Returns:
        加权综合分（0~1，越高越好）
    """
    total_weight = 0.0
    acc = 0.0
    for name, cfg in objectives_config.items():
        weight = float(cfg.get("weight", 0.0))
        total_weight += weight
        acc += weight * objective_scores.get(name, 0.0)
    if total_weight <= 0:
        return 0.0
    return acc / total_weight


def score_breakdown(
    raw_metrics: Dict[str, float],
    objectives_config: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    计算单方案的评分拆解（分项评分）。

    Args:
        raw_metrics: 方案的原始指标 {metric: value}
        objectives_config: 目标配置

    Returns:
        {
            "overall": float,   # 综合分（0~1）
            "breakdown": {
                objective: {
                    "metric": str, "raw": float, "direction": str,
                    "weight": float, "normalized": float(0.5 中性)
                }, ...
            }
        }
    """
    breakdown: Dict[str, Any] = {}
    normalized_scores: Dict[str, float] = {}
    for name, cfg in objectives_config.items():
        metric_key = cfg.get("metric", name)
        raw = float(raw_metrics.get(metric_key, 0.0))
        normalized_scores[name] = 0.5  # 单方案无跨候选参照，取中性分
        breakdown[name] = {
            "metric": metric_key,
            "raw": round(raw, 4),
            "direction": cfg.get("direction", "minimize"),
            "weight": float(cfg.get("weight", 0.0)),
            "normalized": 0.5,
        }
    overall = weighted_score(normalized_scores, objectives_config)
    return {"overall": round(overall, 4), "breakdown": breakdown}


def rank_candidates(
    candidates: List[Dict[str, Any]],
    objectives_config: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    对多个候选方案按综合分降序排序。

    Args:
        candidates: [{ "profile": str, "metrics": {metric: value}, ... }]
        objectives_config: 目标配置

    Returns:
        排序后的候选列表（best 在前），每个候选附加：
        - objective_scores: {objective: 归一化分}
        - overall_score: 综合分（0~1）
    """
    if not candidates:
        return []

    # 1. 收集各目标在候选间的原始值
    raw_by_objective: Dict[str, List[float]] = {}
    for name, cfg in objectives_config.items():
        metric_key = cfg.get("metric", name)
        raw_by_objective[name] = [
            float(c.get("metrics", {}).get(metric_key, 0.0)) for c in candidates
        ]

    # 2. 跨候选归一化
    norm_by_objective: Dict[str, List[float]] = {
        name: normalize_scores(raw_by_objective[name], objectives_config[name].get("direction", "minimize"))
        for name in objectives_config
    }

    # 3. 加权综合分
    ranked = []
    for i, cand in enumerate(candidates):
        obj_scores = {
            name: round(norm_by_objective[name][i], 4) for name in objectives_config
        }
        overall = weighted_score(obj_scores, objectives_config)
        ranked.append({
            **cand,
            "objective_scores": obj_scores,
            "overall_score": round(overall, 4),
        })

    # 4. 降序（综合分高者优先）
    ranked.sort(key=lambda c: c["overall_score"], reverse=True)
    return ranked
