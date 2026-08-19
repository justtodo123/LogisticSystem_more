from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

from core.order_status import ORDER_STATUSES
from core.validators import normalize_time_window_requirement


class GoodsCreate(BaseModel):
    """货物创建Schema - 嵌入在OrderCreate中"""
    goods_name: str
    goods_type: str
    weight: float
    volume: float


class OrderCreate(BaseModel):
    """订单创建请求"""
    destination_node_code: str
    storage_center_code: Optional[str] = None
    time_window: str = Field(description="时效要求（自由文本，最长 32）")
    goods: List[GoodsCreate]

    @field_validator("time_window")
    @classmethod
    def normalize_time_window(cls, value: str) -> str:
        normalized, error = normalize_time_window_requirement(value)
        if error:
            raise ValueError(error)
        return normalized


class OrderResponse(BaseModel):
    """订单响应"""
    order_code: str
    destination_node_code: str
    destination_node_name: str
    time_window: str
    status: str = Field(description="订单六态之一: " + "/".join(ORDER_STATUSES))
    goods_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderImportResponse(BaseModel):
    """订单导入响应"""
    success_count: int
    failed_count: int
    failed_rows: List[Dict[str, Any]]


class OrderUpdate(BaseModel):
    """订单编辑Schema - 只能修改配送节点和时效要求"""
    destination_node_code: Optional[str] = None
    time_window: Optional[str] = Field(default=None, description="时效要求（自由文本，最长 32）")

    @field_validator("time_window")
    @classmethod
    def normalize_time_window(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized, error = normalize_time_window_requirement(value)
        if error:
            raise ValueError(error)
        return normalized
