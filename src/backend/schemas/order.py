from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class GoodsCreate(BaseModel):
    """货物创建Schema - 嵌入在OrderCreate中"""
    goods_name: str
    goods_type: str
    weight: float
    volume: float


class OrderCreate(BaseModel):
    """订单创建请求"""
    destination_node_code: str
    time_window: str
    goods: List[GoodsCreate]


class OrderResponse(BaseModel):
    """订单响应"""
    order_code: str
    destination_node_code: str
    destination_node_name: str
    time_window: str
    status: str
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
    time_window: Optional[str] = None
