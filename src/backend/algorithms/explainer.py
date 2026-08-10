"""
调度结果解释器（T2-3）

将调度方案的评分拆解、约束命中、备选方案组织为结构化 `explanation` 数据，
供：
1. `GET /api/schedule/global/{schedule_code}` 响应直接返回
2. `GlobalSchedule.explanation_data` 落库（随方案持久化）
3. DeepSeek `explain_schedule` 提示词使用（结构化数据，而非纯黑盒）

核心结构：
    explanation = {
        "score_breakdown": [ {objective, raw, score, weight, direction}, ... ],
        "composite_score": float,       # 综合分（0~1，越高越好）
        "constraints_hit": [ {name, detail, severity, hit}, ... ],
        "alternatives": [ ... ],        # 备选方案（T2-2 生成）
        "summary": "一句话方案总结",
    }
"""
from typing import Any, Dict, List

from algorithms import scoring


def _load_objectives_config() -> Dict[str, Any]:
    """加载多目标评分配置"""
    import json
    import os
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config", "algorithm_config.json"
    )
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f).get("global_schedule_objectives", {})


def analyze_constraints(schedule_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    分析调度方案中哪些硬约束被命中/生效。

    基于 goods_schedules（L0→L1→L2 路径）与 metrics 做静态分析，
    不依赖外部状态，输出可直接用于解释与提示词。

    Returns:
        [{"name": 约束名, "detail": 说明, "severity": "info|warning", "hit": bool}, ...]
    """
    constraints: List[Dict[str, Any]] = []
    goods_schedules = schedule_data.get("goods_schedules", []) or []

    # ── 约束 1：同订单汇聚（同订单货物必须走相同 L1） ──
    by_order: Dict[str, List[str]] = {}
    for gs in goods_schedules:
        path = gs.get("path", [])
        # path 可能是节点编码列表或对象列表
        l1_code = path[1] if len(path) > 1 else None
        if isinstance(l1_code, dict):
            l1_code = l1_code.get("node_code")
        if l1_code:
            by_order.setdefault(gs.get("order_code", "?"), []).append(str(l1_code))

    multi_goods_orders = {code: l1s for code, l1s in by_order.items() if len(l1s) > 1}
    if multi_goods_orders:
        diverged = {code: set(l1s) for code, l1s in multi_goods_orders.items() if len(set(l1s)) > 1}
        if diverged:
            constraints.append({
                "name": "同订单汇聚",
                "detail": f"{len(diverged)} 个订单的货物分散到不同 L1："
                          f"{', '.join(f'{c}({sorted(s)})' for c, s in list(diverged.items())[:5])}",
                "severity": "warning",
                "hit": True,
            })
        else:
            constraints.append({
                "name": "同订单汇聚",
                "detail": f"{len(multi_goods_orders)} 个多货物订单均汇聚到相同 L1",
                "severity": "info",
                "hit": True,
            })
    elif goods_schedules:
        constraints.append({
            "name": "同订单汇聚",
            "detail": "每个订单仅 1 票货物，约束不构成分叉（未实际约束）",
            "severity": "info",
            "hit": False,
        })

    # ── 约束 2：L1 容量 ──
    l1_load: Dict[str, int] = {}
    for gs in goods_schedules:
        path = gs.get("path", [])
        l1_code = path[1] if len(path) > 1 else None
        if isinstance(l1_code, dict):
            l1_code = l1_code.get("node_code")
        if l1_code:
            l1_load[str(l1_code)] = l1_load.get(str(l1_code), 0) + 1

    if l1_load:
        busiest = max(l1_load.items(), key=lambda kv: kv[1])
        constraints.append({
            "name": "L1 容量",
            "detail": f"{len(l1_load)} 个 L1 参与分拣，最繁忙 L1 {busiest[0]} 承载 {busiest[1]} 票货物",
            "severity": "info",
            "hit": True,
        })

    # ── 约束 3：最大存储时长 / 时效（基于 on_time_rate 指标） ──
    metrics = schedule_data.get("metrics", {}) or {}
    on_time_rate = metrics.get("on_time_rate")
    if on_time_rate is not None:
        if on_time_rate < 1.0:
            constraints.append({
                "name": "最大存储时长",
                "detail": f"仅 {on_time_rate:.0%} 货物满足时效预估，存在履约风险",
                "severity": "warning",
                "hit": True,
            })
        else:
            constraints.append({
                "name": "最大存储时长",
                "detail": "全部货物均满足时效预估",
                "severity": "info",
                "hit": True,
            })

    # ── 满载率提示（load_rate 指标） ──
    load_rate = metrics.get("load_rate")
    if load_rate is not None:
        severity = "warning" if load_rate < 0.5 else "info"
        constraints.append({
            "name": "满载率",
            "detail": f"L1 平均满载率 {load_rate:.0%}",
            "severity": severity,
            "hit": load_rate < 1.0,
        })

    return constraints


def _build_breakdown(schedule_data: Dict[str, Any], objectives_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    将 T2-2 评分数据整理为前端友好的分项列表。

    score_breakdown（T2-2）形如 {"overall": x, "breakdown": {obj: {raw, weight, direction, normalized}}}，
    此处将其与 objective_scores 合并为列表：
        [{"objective": "distance", "raw": 120.5, "score": 0.82, "weight": 0.30, "direction": "minimize"}, ...]
    """
    bd = schedule_data.get("score_breakdown", {}) or {}
    breakdown_map = bd.get("breakdown", {}) if isinstance(bd, dict) else {}
    obj_scores = schedule_data.get("objective_scores", {}) or {}

    items: List[Dict[str, Any]] = []
    for objective, cfg in objectives_config.items():
        info = breakdown_map.get(objective, {}) if isinstance(breakdown_map, dict) else {}
        items.append({
            "objective": objective,
            "metric": cfg.get("metric", objective),
            "raw": info.get("raw"),
            "weight": cfg.get("weight", 0.0),
            "direction": cfg.get("direction", "minimize"),
            "score": obj_scores.get(objective),
        })
    return items


def _build_summary(schedule_data: Dict[str, Any]) -> str:
    """生成一句话方案总结"""
    total_distance = schedule_data.get("total_distance")
    total_time = schedule_data.get("total_time")
    total_goods = schedule_data.get("total_goods")
    composite = schedule_data.get("composite_score")
    parts = []
    if total_goods is not None:
        parts.append(f"共调度 {total_goods} 票货物")
    if total_distance is not None:
        parts.append(f"总距离 {float(total_distance):.1f}km")
    if total_time is not None:
        parts.append(f"总时间 {float(total_time):.1f}h")
    if composite is not None:
        parts.append(f"综合分 {float(composite):.2f}")
    return "；".join(parts) if parts else "暂无数据"


def build_explanation(schedule_data: Dict[str, Any], objectives_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    构建调度方案的结构化解释。

    Args:
        schedule_data: 调度方案 dict（含 goods_schedules/metrics/objective_scores/score_breakdown/composite_score/alternatives）
        objectives_config: 目标配置（缺省时读取 algorithm_config.json）

    Returns:
        结构化 explanation（score_breakdown / composite_score / constraints_hit / alternatives / summary）
    """
    objectives_config = objectives_config or _load_objectives_config()

    return {
        "score_breakdown": _build_breakdown(schedule_data, objectives_config),
        "composite_score": schedule_data.get("composite_score"),
        "constraints_hit": analyze_constraints(schedule_data),
        "alternatives": schedule_data.get("alternatives", []),
        "summary": _build_summary(schedule_data),
    }


def build_prompt_section(schedule_data: Dict[str, Any]) -> str:
    """
    将结构化解释压缩为 AI 提示词可直接引用的文本块。

    验收标准：AI 解释接口的 prompt 包含结构化数据（评分拆解/约束命中/备选），而非仅方案 ID。
    """
    explanation = schedule_data.get("explanation")
    if not explanation:
        explanation = build_explanation(schedule_data)

    lines: List[str] = []

    # 评分拆解
    bd = explanation.get("score_breakdown", []) or []
    if bd:
        lines.append("分项目标评分（0~1，越高越好）：")
        for item in bd:
            raw = item.get("raw")
            raw_txt = f"原始值 {raw:.1f}" if raw is not None else "原始值 ?"
            lines.append(
                f"- {item.get('objective')} [{item.get('metric')}]: "
                f"得分 {item.get('score')}（{raw_txt}，方向 {item.get('direction')}，权重 {item.get('weight')}）"
            )
    composite = explanation.get("composite_score")
    if composite is not None:
        lines.append(f"综合评分：{composite:.3f}")

    # 约束命中
    constraints = explanation.get("constraints_hit", []) or []
    if constraints:
        lines.append("约束分析：")
        for c in constraints:
            lines.append(f"- [{c.get('severity')}] {c.get('name')}：{c.get('detail')}")

    # 备选方案
    alternatives = explanation.get("alternatives", []) or []
    if alternatives:
        lines.append("备选方案（按综合分降序）：")
        for alt in alternatives[:3]:
            lines.append(
                f"- {alt.get('profile')}: 综合分 {alt.get('overall_score')}, "
                f"距离 {alt.get('total_distance')}km, 时间 {alt.get('total_time')}h"
            )

    return "\n".join(lines)
