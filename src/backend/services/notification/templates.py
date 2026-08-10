"""通知内容模板（T3-2）

按场景渲染 (subject, content)。context 由业务服务传入具体编号。
"""
from typing import Any, Dict, Tuple

# 场景常量
SCENARIO_SCHEDULE_CONFIRMED = "schedule_confirmed"
SCENARIO_EXCEPTION_CREATED = "exception_created"
SCENARIO_REPLAN_COMPLETED = "replan_completed"
SCENARIO_ARRIVAL_CONFIRMED = "arrival_confirmed"

ALL_SCENARIOS = {
    SCENARIO_SCHEDULE_CONFIRMED,
    SCENARIO_EXCEPTION_CREATED,
    SCENARIO_REPLAN_COMPLETED,
    SCENARIO_ARRIVAL_CONFIRMED,
}


def build_notification(
    scenario: str,
    context: Dict[str, Any],
) -> Tuple[str, str]:
    """根据场景渲染 (subject, content)"""
    builder = _BUILDERS.get(scenario)
    if not builder:
        raise ValueError(f"未知通知场景: {scenario}")
    return builder(context)


def _schedule_confirmed(ctx: Dict[str, Any]) -> Tuple[str, str]:
    code = ctx.get("schedule_code", "—")
    goods = ctx.get("total_goods")
    distance = ctx.get("total_distance")
    time_cost = ctx.get("total_time")
    score = ctx.get("score")
    content = (
        f"调度方案 {code} 已确认并激活。\n"
        f"- 货物数：{goods if goods is not None else '—'}\n"
        f"- 总里程：{distance if distance is not None else '—'} km\n"
        f"- 预计总耗时：{time_cost if time_cost is not None else '—'} h\n"
        f"- 综合评分：{score if score is not None else '—'}\n"
        f"- 是否重规划：{'是' if ctx.get('is_replan') else '否'}"
    )
    return f"【调度确认】{code} 已激活", content


def _exception_created(ctx: Dict[str, Any]) -> Tuple[str, str]:
    code = ctx.get("event_code", "—")
    etype = ctx.get("exception_type", "—")
    subtype = ctx.get("exception_subtype")
    target = ctx.get("target_code")
    action = ctx.get("recommended_action", "—")
    desc = ctx.get("description", "—")
    content = (
        f"系统检测到异常事件 {code}。\n"
        f"- 异常类型：{etype}{'/' + subtype if subtype else ''}\n"
        f"- 关联对象：{target if target else '—'}\n"
        f"- 推荐动作：{action}\n"
        f"- 描述：{desc}"
    )
    return f"【异常告警】{code}（{etype}）", content


def _replan_completed(ctx: Dict[str, Any]) -> Tuple[str, str]:
    original = ctx.get("original_schedule_code", "—")
    new_code = ctx.get("new_schedule_code") or ctx.get("schedule_code")
    strategy = ctx.get("strategy", "—")
    reason = ctx.get("replan_reason", "—")
    diff = ctx.get("diff_summary")
    content = (
        f"原方案 {original} 已触发重规划。\n"
        f"- 新方案：{new_code if new_code else '—'}\n"
        f"- 策略：{strategy}\n"
        f"- 原因：{reason}"
    )
    if diff:
        content += (
            f"\n- 受影响包裹：{diff.get('affected_count', '—')}\n"
            f"- 总时长变化：{diff.get('new_eta_delta', '—')} h\n"
            f"- 成本变化：{diff.get('cost_delta', '—')} 元"
        )
    return f"【重规划完成】{original} → {new_code or '新方案'}", content


def _arrival_confirmed(ctx: Dict[str, Any]) -> Tuple[str, str]:
    pkg = ctx.get("package_code", "—")
    schedule = ctx.get("schedule_code", "—")
    content = (
        f"包裹 {pkg} 已到货并确认。\n"
        f"- 所属调度方案：{schedule if schedule else '—'}"
    )
    return f"【到货确认】{pkg} 已送达", content


_BUILDERS = {
    SCENARIO_SCHEDULE_CONFIRMED: _schedule_confirmed,
    SCENARIO_EXCEPTION_CREATED: _exception_created,
    SCENARIO_REPLAN_COMPLETED: _replan_completed,
    SCENARIO_ARRIVAL_CONFIRMED: _arrival_confirmed,
}
