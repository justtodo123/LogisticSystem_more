"""
ExceptionEvent Pydantic 请求/响应模型

阶段7新增：异常事件管理所需的 Schema。
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CreateExceptionEventRequest(BaseModel):
    """创建异常事件请求体"""
    exception_type: str = Field(..., description="异常类型：road / package / node")
    exception_subtype: Optional[str] = Field(None, description="异常子类型：congestion / damage / capacity_limit")
    target_type: Optional[str] = Field(None, description="关联对象类型：node / package / route")
    target_code: Optional[str] = Field(None, description="关联对象业务编号")
    recommended_action: str = Field(..., description="推荐操作：redispatch / reroute")
    related_schedule_code: Optional[str] = Field(None, description="关联调度方案业务编号")
    description: str = Field(..., description="异常描述")


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
