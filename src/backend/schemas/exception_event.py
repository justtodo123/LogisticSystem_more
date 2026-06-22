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
    severity: Optional[str] = Field("medium", description="严重程度：low / medium / high")
    recommended_action: str = Field(..., description="推荐操作：redispatch / reroute")
    trigger_node_code: Optional[str] = Field(None, description="触发节点业务编号")
    related_route_code: Optional[str] = Field(None, description="关联路线业务编号")
    related_schedule_code: Optional[str] = Field(None, description="关联调度方案业务编号")
    description: str = Field(..., description="异常描述")
    replan_reason: Optional[str] = Field(None, description="重规划原因")


class TriggerReplanRequest(BaseModel):
    """触发重规划请求体"""
    replan_reason: str = Field(..., description="重规划原因")


class ResolveExceptionRequest(BaseModel):
    """标记异常已解决请求体"""
    resolution_note: Optional[str] = Field(None, description="解决备注")


class ExceptionEventResponse(BaseModel):
    """异常事件响应体"""
    event_code: str
    exception_type: str
    exception_subtype: Optional[str] = None
    target_type: Optional[str] = None
    target_code: Optional[str] = None
    severity: str
    recommended_action: str
    trigger_node_code: Optional[str] = None
    related_route_code: Optional[str] = None
    related_schedule_code: Optional[str] = None
    replan_batch_code: Optional[str] = None
    description: str
    status: str
    resolution_note: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class ExceptionEventListResponse(BaseModel):
    """异常事件列表响应体"""
    items: list[ExceptionEventResponse]
    total: int
    page: int
    page_size: int
