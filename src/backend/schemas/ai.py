"""
AI 助手 Pydantic 模型

功能：
1. 定义 AI 助手相关请求/响应模型
2. P0 实现：AiParseRequest / AiParseResponse
3. P1 预留：AiExplainRequest / AiReviewRequest / AiAnalyzeExceptionRequest
"""
from pydantic import BaseModel
from typing import Dict, Any, Optional, List, Literal


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

    ── 速查示例（阶段8）──

    ① AI 重规划（最常用：对已有方案重新调度，AI 解析自然语言）
    {
      "message": "优先缩短距离，多用电车",
      "schedule_codes": ["GS20260622001"]
    }

    ② AI 重规划 + 权重覆盖（DeepSeek 解析后手动覆盖部分参数）
    {
      "message": "优先时效",
      "weights": {
        "global_schedule": {
          "weights": {
            "time": 0.7
          }
        }
      },
      "schedule_codes": ["GS20260622001"]
    }

    ③ 纯手动权重重规划（不调 DeepSeek，直接用指定权重）
    {
      "weights": {
        "global_schedule": {
          "weights": {
            "distance": 0.9,
            "time": 0.05,
            "package_count": 0.05
          }
        }
      },
      "schedule_codes": ["GS20260622001"]
    }

    ④ 默认参数重规划（无 message 无 weights，用 algorithm_config.json 默认值）
    {
      "schedule_codes": ["GS20260622001"]
    }

    ⑤ 批量重规划（逐条生成新版本，AI 参考所有方案指标）
    {
      "message": "缩短距离",
      "schedule_codes": [
        "GS20260622001",
        "GS20260622002",
        "GS20260622003"
      ]
    }

    ⑥ dry-run（仅查看解析参数，不执行调度、不写库）
    {
      "message": "优先缩短距离，多用电车",
      "execute": "dry-run"
    }

    ⑦ AI 新建 draft（无 schedule_codes → 对全部 pending 订单创建 draft 方案）
    {
      "message": "优先缩短距离，多用电车"
    }

    ⑧ 手动权重 dry-run（仅预览参数）
    {
      "weights": {
        "global_schedule": {
          "weights": {
            "time": 0.7
          }
        }
      },
      "execute": "dry-run"
    }
    """
    message: Optional[str] = None           # 自然语言指令（空=跳过 DeepSeek）
    weights: Optional[Dict[str, Any]] = None  # 手动权重（结构与 algorithm_config.json 一致）
    schedule_codes: Optional[List[str]] = None  # 目标方案列表（非空=重规划，空=新建）
    execute: Literal["dry-run", "draft"] = "draft"  # "draft"=生成 draft 方案 / "dry-run"=仅返回参数不落库


class AiParseResponse(BaseModel):
    """
    AI 解析响应模型（F014）
    
    新建和重规划模式响应结构完全一致，仅 is_replan 字段区分。
    """
    schedule_code: Optional[str] = None             # 新建/重规划返回的新方案编号
    algorithm_params: Dict[str, Any]                # 最终使用的算法参数（只含 global_schedule）
    mode: str = "default"                           # "ai" / "manual" / "hybrid" / "default"
    is_replan: bool = False                         # 是否重规划
    reference_codes: Optional[List[str]] = None     # 参考的方案编码列表（schedule_codes 原样回传）
    status: Optional[str] = None                    # draft 模式返回 "draft"；dry-run 不返回此字段
    degraded: bool = False                          # DeepSeek 是否降级
    degraded_reason: Optional[str] = None           # 降级原因


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
