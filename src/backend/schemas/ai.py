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
    """
    AI 解析请求模型（F014） — 3 字段，逻辑自洽

    字段语义:
    - message:    自然语言指令（非空 → DeepSeek 解析；空 + weights 空 → 默认参数）
    - weights:    手动覆盖（结构与 algorithm_config.json 一致，可部分覆盖）
    - schedule_codes: 指定历史方案（非空=对这些方案做版本化重规划）

    工作逻辑:
    ```
    message? ─┬─ 有 ──→ DeepSeek 解析 ──┬─ weights? ─┬─ 无 → AI 参数直接使用
              │                        │            └─ 有 → weights 覆盖 AI 结果
              │                        └─→ schedule_codes? ─┬─ 无 → 新建调度（全部 pending 订单）
              │                                              └─ 有 → 逐条重规划
              │
              └─ 无 ──→ weights? ─┬─ 有 → 手动参数 ─→ schedule_codes? ─┬─ 无 → 新建
                                  │                                     └─ 有 → 重规划
                                  └─ 无 → 默认参数 ─→ schedule_codes? ─┬─ 无 → 新建
                                                                       └─ 有 → 重规划
    ```

    ── 速查示例 ──

    ① 裸 AI（最常见）
    { "message": "优先缩短距离，多用电车" }

    ② 带权重
    { "message": "优先时效",
      "weights": {"global_schedule": {"weights": {"time": 0.7}}} }

    ③ 纯手动权重
    { "weights": {"global_schedule": {"weights": {"distance": 0.9, "time": 0.05, "package_count": 0.05}}} }

    ④ 对单个方案重规划
    { "message": "GS001 耗时太长，缩短时间",
      "schedule_codes": ["GS20260622001"] }

    ⑤ 批量重规划（AI 参考所有方案指标，逐条生成新版本）
    { "message": "缩短距离",
      "schedule_codes": ["GS001", "GS002", "GS003"] }

    ⑥ 默认参数重规划
    { "schedule_codes": ["GS001"] }
    """
    message: Optional[str] = None           # 自然语言指令（空=跳过 DeepSeek）
    weights: Optional[Dict[str, Any]] = None  # 手动权重（结构与 algorithm_config.json 一致）
    schedule_codes: Optional[List[str]] = None  # 目标方案列表（非空=重规划，空=新建）


class AiParseResponse(BaseModel):
    """AI 解析响应模型（F014）"""
    schedule_code: Optional[str] = None             # 新建模式返回的新方案编号
    replan_results: Optional[List[Dict[str, Any]]] = None  # 重规划模式返回 [{original, new}] 列表
    algorithm_params: Dict[str, Any]                 # 最终使用的算法参数
    mode: str = "default"                            # "ai" / "manual" / "hybrid" / "default"
    is_replan: bool = False                          # 是否重规划
    reference_codes: Optional[List[str]] = None      # 参考的方案编码列表
    degraded: bool = False                           # DeepSeek 是否降级
    degraded_reason: Optional[str] = None            # 降级原因


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
