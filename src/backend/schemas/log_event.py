from pydantic import BaseModel
from datetime import datetime


class LogEventCreate(BaseModel):
    """创建日志事件请求模型"""
    event_name: str
    user_id: int
    role: str
    event_data: dict | None = None


class LogEventResponse(BaseModel):
    """日志事件响应模型"""
    id: int
    event_name: str
    user_id: int
    role: str
    event_data: dict | None = None
    created_at: datetime

    class Config:
        from_attributes = True
