"""
AI 输出结构化校验模型（T6-1）

为 4 个 AI 功能（parse / explain / review / analyze）定义 Pydantic 校验 Schema，
供 core/ai_guard.py 的「校验 → 重试 → 业务规则」管线使用：
- schema 负责结构校验（字段缺失、类型不对、取值范围）
- core/ai_guard 负责业务规则（权重归一化、枚举白名单）
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ═══ parse：自然语言 → 算法参数（F014）═══

class AlgorithmWeights(BaseModel):
    """全局调度权重（业务规则：非负、三权重之和≈1.0）"""
    # 允许 AI 多带未知键（extra="allow" 仅校验已知字段，未知键由 normalize 丢弃）
    model_config = ConfigDict(extra="allow")

    distance: float = Field(ge=0, le=1, description="距离权重")
    time: float = Field(ge=0, le=1, description="时间权重")
    package_count: float = Field(ge=0, le=1, description="包裹数权重")


class GlobalScheduleParams(BaseModel):
    """global_schedule 节（算法 + 权重）"""
    algorithm: str = Field(default="traditional", description="调度算法标识")
    weights: AlgorithmWeights


class ParsedAlgorithmParams(BaseModel):
    """parse_natural_language 的整体输出"""
    global_schedule: GlobalScheduleParams


# ═══ explain：调度方案解释（F015）═══

class ExplainResult(BaseModel):
    """explain_schedule 输出"""
    explanation: str = Field(min_length=1)
    key_decisions: List[str] = Field(default_factory=list)
    potential_risks: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


# ═══ review：调度方案审查（F016）═══

class RiskItem(BaseModel):
    """单个风险条目（类型/级别白名单由 core/ai_guard 业务规则校验）"""
    type: str = "road"
    description: str = Field(min_length=1)
    severity: str = "medium"
    suggestion: str = ""


class ReviewResult(BaseModel):
    """review_schedule 输出"""
    risks: List[RiskItem] = Field(default_factory=list)


# ═══ analyze：异常事件分析（F017）═══

class AnalyzeExceptionResult(BaseModel):
    """analyze_exception 输出"""
    root_cause: str = Field(min_length=1)
    suggestions: List[str] = Field(default_factory=list)
    auto_fix_available: bool = False
