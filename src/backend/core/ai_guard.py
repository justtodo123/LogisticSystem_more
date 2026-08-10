"""
AI 规则闸门（T6-1）

管线：校验 → 业务规则检查 → 发布
- 校验：Pydantic Schema（schemas/ai_output.py）结构化校验
- 重试：校验/解析失败时把错误反馈给 AI 重新生成（最多 max_retries 次）
- 业务规则：语义约束（权重归一化、枚举白名单）
- 发布：规则通过 → 返回结构化结果；重试耗尽仍失败 → AIValidationError
  （携带原始输出 + 校验错误，由调用方降级/展示）
"""
import json
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional, Type

from pydantic import BaseModel, ValidationError

from schemas.ai_output import (
    AnalyzeExceptionResult,
    ParsedAlgorithmParams,
    ReviewResult,
)

logger = logging.getLogger(__name__)

# ── 业务规则常量 ──
VALID_RISK_TYPES = ("road", "package", "node", "vehicle", "route")
VALID_SEVERITIES = ("high", "medium", "low")
WEIGHT_KEYS = ("distance", "time", "package_count")
DEFAULT_WEIGHTS = {"distance": 0.5, "time": 0.3, "package_count": 0.2}

# ── AI 建议确认闸门（T6-2）──
SUGGESTION_LEVELS = ("info", "suggestion", "action")
SUGGESTION_STATUSES = ("pending", "confirmed", "rejected")


class AIValidationError(ValueError):
    """AI 输出校验失败（重试耗尽后抛出），携带原始输出与校验错误详情"""

    def __init__(self, raw_output: str, errors: Any, context: str = ""):
        self.raw_output = raw_output
        self.errors = errors  # pydantic ValidationError.errors() 列表
        self.context = context
        super().__init__(self._build_message())

    def _build_message(self) -> str:
        raw_snippet = self.raw_output[:300]
        if len(self.raw_output) > 300:
            raw_snippet += "..."
        err_lines = []
        for e in self.errors or []:
            loc = ".".join(str(x) for x in e.get("loc", []))
            err_lines.append(f"{loc or '整体'}: {e.get('msg', e.get('type', '?'))}")
        detail = "; ".join(err_lines) or "未知校验错误"
        return f"AI 输出校验失败：{detail} | 原始输出：{raw_snippet}"


async def validate_and_retry(
    schema: Type[BaseModel],
    api_call: Callable[[str, Optional[str]], Awaitable[str]],
    user_prompt: str,
    system_prompt: Optional[str] = None,
    max_retries: int = 3,
) -> BaseModel:
    """
    调用 AI → 提取 JSON → 校验 Schema；失败时把错误反馈给 AI 重试。

    Args:
        schema: Pydantic 校验模型
        api_call: 异步回调 (user_prompt, system_prompt) -> AI 响应文本
        user_prompt: 用户提示词
        system_prompt: 系统提示词
        max_retries: 最多尝试次数（默认 3 次 = 初始 1 次 + 2 次修正重试）

    Returns:
        校验通过的结构化结果（BaseModel 实例）

    Raises:
        AIValidationError: 重试耗尽仍校验失败（含原始输出与校验错误）
    """
    prompt = user_prompt
    last_error: Optional[AIValidationError] = None

    for attempt in range(max_retries):
        content = await api_call(prompt, system_prompt)

        # ① 提取 JSON（解析失败同样作为"格式偏差"反馈重试）
        try:
            raw_dict = _extract_json(content)
        except json.JSONDecodeError as e:
            last_error = AIValidationError(
                raw_output=content,
                errors=[{"loc": ("json",), "msg": f"JSON 解析失败：{e}", "type": "json_decode"}],
            )
            if attempt == max_retries - 1:
                break
            logger.warning("AI 输出第 %d 次 JSON 解析失败，反馈错误后重试", attempt + 1)
            prompt = _append_error_feedback(prompt, content, last_error)
            continue

        # ② Pydantic 结构校验
        try:
            return schema.model_validate(raw_dict)
        except ValidationError as e:
            last_error = AIValidationError(raw_output=content, errors=e.errors())
            if attempt == max_retries - 1:
                break
            logger.warning(
                "AI 输出第 %d 次校验失败，反馈错误后重试：%s",
                attempt + 1, last_error,
            )
            prompt = _append_error_feedback(prompt, content, e)

    # 重试耗尽
    assert last_error is not None
    logger.error("AI 输出 %s 次校验全部失败：%s", max_retries, last_error)
    raise last_error


def _extract_json(content: str) -> Dict[str, Any]:
    """从 AI 返回文本提取 JSON（直接解析 / ```json ``` / ``` 三档）"""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    for fence in ("```json", "```"):
        if fence in content:
            start = content.find(fence) + len(fence)
            end = content.find("```", start)
            if end > start:
                return json.loads(content[start:end].strip())

    raise json.JSONDecodeError("无法从 AI 输出中提取 JSON", content, 0)


def _append_error_feedback(prompt: str, raw_output: str, errors: Any) -> str:
    """把校验错误反馈给 AI，要求下次生成修正"""
    if isinstance(errors, AIValidationError):
        err_lines = [f"- {errors}"]
    elif isinstance(errors, ValidationError):
        err_lines = []
        for e in errors.errors():
            loc = ".".join(str(x) for x in e.get("loc", []))
            err_lines.append(f"- {loc or '整体'}: {e.get('msg', e.get('type', '?'))}")
    else:
        err_lines = [f"- {errors}"]

    return (
        prompt
        + "\n\n【上次输出校验未通过，请修正后重新输出】\n"
        + f"上次输出：{raw_output[:500]}\n"
        + "校验错误：\n" + "\n".join(err_lines)
        + "\n请严格按要求的 JSON 结构重新输出，不要输出任何其他内容。"
    )


# ═══ 业务规则检查（校验通过后的语义约束）═══

def check_algorithm_params(result: ParsedAlgorithmParams) -> List[str]:
    """权重业务规则：三权重之和应≈1.0（非负已由 schema 保证）"""
    violations = []
    w = result.global_schedule.weights
    total = w.distance + w.time + w.package_count
    if abs(total - 1.0) > 0.01:
        violations.append(f"全局调度权重之和为 {total:.2f}，应为 1.0")
    return violations


def check_review_result(result: ReviewResult) -> List[str]:
    """审查结果业务规则：风险类型 / 严重级别应在白名单内、建议非空"""
    violations = []
    for i, risk in enumerate(result.risks):
        if risk.type not in VALID_RISK_TYPES:
            violations.append(
                f"risks[{i}].type={risk.type!r} 不在合法集合 {VALID_RISK_TYPES}"
            )
        if risk.severity not in VALID_SEVERITIES:
            violations.append(
                f"risks[{i}].severity={risk.severity!r} 不在合法集合 {VALID_SEVERITIES}"
            )
        if not risk.suggestion.strip():
            violations.append(f"risks[{i}].suggestion 为空，建议补充优化建议")
    return violations


def check_analyze_result(result: AnalyzeExceptionResult) -> List[str]:
    """异常分析业务规则：至少给出一条处理建议"""
    violations = []
    if not result.suggestions:
        violations.append("suggestions 为空，应给出至少一条处理建议")
    return violations


def classify_suggestion_level(source: str) -> str:
    """按 AI 功能来源标注建议级别（T6-2）

    - parse（生成调度参数/draft 方案）→ suggestion：需调度员确认后应用
    - explain / review / analyze → info：仅供展示，无需确认
    """
    if source == "parse":
        return "suggestion"
    return "info"


def should_gate(level: str) -> bool:
    """是否进入确认闸门：suggestion/action 需要人工确认，info 直接展示"""
    return level in ("suggestion", "action")


def normalize_algorithm_weights(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    发布前归一化：仅保留 3 个已知权重键并重新归一化到和为 1（防御 AI 输出异常权重）。

    - 丢弃未知权重键
    - 钳制到 [0, 1]
    - 和不为 1 时按比例归一化；全 0 时回退默认权重
    """
    global_schedule = dict(raw.get("global_schedule") or {})
    weights = dict(global_schedule.get("weights") or {})

    kept: Dict[str, float] = {}
    for k in WEIGHT_KEYS:
        if k in weights:
            try:
                kept[k] = max(0.0, min(1.0, float(weights[k])))
            except (TypeError, ValueError):
                continue

    total = sum(kept.values())
    if total <= 0:
        kept = dict(DEFAULT_WEIGHTS)
    elif abs(total - 1.0) > 1e-6:
        # 不四舍五入，直接按比例缩放，保证重归一化后权重之和精确为 1.0
        kept = {k: v / total for k, v in kept.items()}

    return {
        "global_schedule": {
            "algorithm": global_schedule.get("algorithm", "traditional"),
            "weights": kept,
        }
    }
