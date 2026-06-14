"""
模拟送达 Pydantic Schema 定义
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class DeliverRequest(BaseModel):
    """模拟送达请求体"""
    vehicle_code: Optional[str] = Field(None, description="车辆编号（可选）")
    package_code: Optional[str] = Field(None, description="包裹编号（可选）")


class DeliverResponse(BaseModel):
    """模拟送达响应数据"""
    delivered_package_codes: List[str] = Field(..., description="送达包裹编号列表")
    status_changed_goods_count: int = Field(..., description="状态变更的货物数量")
    updated_order_count: int = Field(..., description="更新的订单数量")
    delivered_order_codes: List[str] = Field(..., description="已送达订单编号列表")
