"""
AI 助手 Pydantic 模型

功能：
1. 定义 AI 助手相关请求/响应模型
2. P0 实现：AiParseRequest / AiParseResponse
3. P1 预留：AiExplainRequest / AiReviewRequest / AiAnalyzeExceptionRequest
"""
from pydantic import BaseModel
from typing import Dict, Any, Optional, List


# ==================== P0：自然语言解析 ====================

class AiParseRequest(BaseModel):
    """AI 解析请求模型（F014）"""
    message: str  # 用户自然语言输入
    auto_execute: bool = True  # 是否自动执行调度链路


class AiParseResponse(BaseModel):
    """AI 解析响应模型（F014）"""
    schedule_code: Optional[str] = None  # 调度方案编号（auto_execute=true 时返回）
    algorithm_params: Dict[str, Any]  # 解析出的算法参数
    degraded: bool = False  # 是否降级
    degraded_reason: Optional[str] = None  # 降级原因


# ==================== P1：方案解释（预留） ====================

class AiExplainRequest(BaseModel):
    """方案解释请求模型（F015，P1）"""
    schedule_code: str
    detail_level: str = "brief"  # brief / detailed


class AiExplainResponse(BaseModel):
    """方案解释响应模型（F015，P1）"""
    explanation: str
    key_decisions: List[str]
    potential_risks: List[str]


# ==================== P1：方案审查（预留） ====================

class AiReviewRequest(BaseModel):
    """方案审查请求模型（F016，P1）"""
    schedule_code: str
    check_items: List[str] = ["timeout", "overload", "carbon"]


class AiReviewResponse(BaseModel):
    """方案审查响应模型（F016，P1）"""
    risks: List[Dict[str, Any]]
    suggestions: List[str]


# ==================== P1：异常分析（预留） ====================

class AiAnalyzeExceptionRequest(BaseModel):
    """异常分析请求模型（F017，P1）"""
    exception_event_code: str


class AiAnalyzeExceptionResponse(BaseModel):
    """异常分析响应模型（F017，P1）"""
    root_cause: str
    suggestions: List[str]
    auto_fix_available: bool
