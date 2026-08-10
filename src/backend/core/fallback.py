"""
降级策略定义

当外部服务（DeepSeek AI、数据库等）不可用时，
返回降级响应，确保核心功能仍可工作。
"""
from typing import Optional
from pydantic import BaseModel


class FallbackInfo(BaseModel):
    """降级信息"""
    degraded: bool = False
    reason: Optional[str] = None
    fallback_action: Optional[str] = None


# ── 预定义降级策略 ──

DEEPSEEK_DEGRADED = FallbackInfo(
    degraded=True,
    reason="DeepSeek API 调用失败，已使用默认算法参数完成调度",
    fallback_action="default_algorithm",
)

DEEPSEEK_TIMEOUT = FallbackInfo(
    degraded=True,
    reason="DeepSeek API 响应超时，已使用默认算法参数完成调度",
    fallback_action="default_algorithm",
)

DEEPSEEK_UNAVAILABLE = FallbackInfo(
    degraded=True,
    reason="DeepSeek API Key 未配置，AI 功能不可用",
    fallback_action="disabled",
)

DATABASE_DEGRADED = FallbackInfo(
    degraded=True,
    reason="数据库连接异常，已降级到只读模式",
    fallback_action="readonly_mode",
)


def build_degraded_response(
    data: Optional[dict] = None,
    fallback: FallbackInfo = DEEPSEEK_DEGRADED,
    code: int = 0,
    message: str = "success",
) -> dict:
    """构建降级响应

    Args:
        data: 业务数据
        fallback: 降级信息
        code: 业务状态码
        message: 提示消息

    Returns:
        统一响应格式 dict
    """
    return {
        "code": code,
        "message": message,
        "data": data or {},
        "meta": {
            "degraded": fallback.degraded,
            "degraded_reason": fallback.reason,
            "fallback_action": fallback.fallback_action,
        },
    }
