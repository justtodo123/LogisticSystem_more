from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class GoodsCreate(BaseModel):
    """货物创建Schema - 嵌入在OrderCreate中，不单独使用"""
    goods_name: str
    goods_type: str
    weight: float
    volume: float
    node_code: str  # 存储中心编号


class GoodsUpdate(BaseModel):
    """货物更新Schema - 可编辑基本信息"""
    goods_name: Optional[str] = None
    goods_type: Optional[str] = None
    weight: Optional[float] = None
    volume: Optional[float] = None
    node_code: Optional[str] = None


class GoodsResponse(BaseModel):
    """货物响应"""
    goods_code: str
    goods_name: str
    goods_type: str
    weight: float
    volume: float
    node_code: str
    node_name: str
    order_code: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
