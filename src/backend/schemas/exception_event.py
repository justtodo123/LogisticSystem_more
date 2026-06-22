"""
ExceptionEvent Pydantic 请求/响应模型

阶段7新增：异常事件管理所需的 Schema。
"""
from pydantic import BaseModel, Field, model_validator
from typing import Optional
from datetime import datetime

# 允许的枚举值（Schema 层校验，与服务层 ALLOWED_* 保持同步）
ALLOWED_EXCEPTION_TYPES = {"road", "package", "node"}
ALLOWED_TARGET_TYPES = {"node", "package", "route", "vehicle"}
ALLOWED_ACTIONS = {"redispatch", "reroute"}


class CreateExceptionEventRequest(BaseModel):
    """创建异常事件请求体"""
    exception_type: str = Field(..., description="异常类型：road / package / node")
    exception_subtype: Optional[str] = Field(None, description="异常子类型：congestion / damage / capacity_limit")
    target_type: Optional[str] = Field(None, description="关联对象类型：node / package / route / vehicle")
    target_code: Optional[str] = Field(None, description="关联对象业务编号")
    recommended_action: str = Field(..., description="推荐操作：redispatch / reroute")
    related_schedule_code: Optional[str] = Field(None, description="关联调度方案业务编号")
    description: str = Field(..., description="异常描述")

    @model_validator(mode='after')
    def validate_action_and_target(self):
        """校验 recommended_action 与 target_type/target_code 的一致性"""
        # 1) 校验 recommended_action
        if self.recommended_action not in ALLOWED_ACTIONS:
            raise ValueError(
                f"无效的 recommended_action: {self.recommended_action}，"
                f"允许值: {', '.join(sorted(ALLOWED_ACTIONS))}"
            )

        # 2) 校验 exception_type
        if self.exception_type not in ALLOWED_EXCEPTION_TYPES:
            raise ValueError(
                f"无效的 exception_type: {self.exception_type}，"
                f"允许值: {', '.join(sorted(ALLOWED_EXCEPTION_TYPES))}"
            )

        # 3) 校验 target_type（若提供）
        if self.target_type is not None and self.target_type not in ALLOWED_TARGET_TYPES:
            raise ValueError(
                f"无效的 target_type: {self.target_type}，"
                f"允许值: {', '.join(sorted(ALLOWED_TARGET_TYPES))}"
            )

        # 4) reroute 必须关联路线
        if self.recommended_action == "reroute":
            if self.target_type != "route":
                raise ValueError(
                    f"reroute 操作要求 target_type='route'，当前为: {self.target_type}"
                )
            if not self.target_code:
                raise ValueError(
                    "reroute 操作要求提供 target_code（路线编码）"
                )

        # 5) redispatch 建议关联节点/车辆/包裹
        if self.recommended_action == "redispatch":
            if self.target_type and self.target_type not in {"node", "vehicle", "package"}:
                raise ValueError(
                    f"redispatch 操作的 target_type 应为 node/vehicle/package，"
                    f"当前为: {self.target_type}"
                )

        return self


class TriggerReplanRequest(BaseModel):
    """触发重规划请求体"""
    action: str = Field(..., description="重规划类型：redispatch / reroute")
    reason: str = Field(..., description="重规划原因")


class UpdateExceptionRequest(BaseModel):
    """更新异常事件请求体"""
    status: Optional[str] = Field(None, description="异常状态：open / resolved")


class ResolveExceptionRequest(BaseModel):
    """标记异常已解决请求体（无必填字段）"""
    pass


class ExceptionEventResponse(BaseModel):
    """异常事件响应体"""
    event_code: str
    exception_type: str
    exception_subtype: Optional[str] = None
    target_type: Optional[str] = None
    target_code: Optional[str] = None
    recommended_action: str
    related_schedule_code: Optional[str] = None
    replan_batch_code: Optional[str] = None
    description: str
    status: str
    resolved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class ExceptionEventListResponse(BaseModel):
    """异常事件列表响应体"""
    items: list[ExceptionEventResponse]
    total: int
    page: int
    page_size: int
