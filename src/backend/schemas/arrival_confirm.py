"""
到货确认 Pydantic 模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ArrivalConfirmRequest(BaseModel):
    """单个到货确认请求"""
    schedule_code: str = Field(..., description="调度方案编号")
    package_code: str = Field(..., description="到站包裹编号")
    is_normal: bool = Field(..., description="是否正常到站")
    exception_subtype: Optional[str] = Field(None, description="异常子类型（仅 is_normal=false 时必填）")
    remark: Optional[str] = Field(None, description="备注")


class BatchArrivalConfirmItem(BaseModel):
    """批量到货确认项"""
    package_code: str = Field(..., description="包裹编号")
    is_normal: bool = Field(..., description="是否正常到站")
    exception_subtype: Optional[str] = Field(None, description="异常子类型（仅 is_normal=false 时必填）")
    remark: Optional[str] = Field(None, description="备注")


class BatchArrivalConfirmRequest(BaseModel):
    """批量到货确认请求"""
    schedule_code: str = Field(..., description="调度方案编号（所有包裹必须属于该方案）")
    confirmations: List[BatchArrivalConfirmItem] = Field(..., description="确认列表")


class ArrivalConfirmResponse(BaseModel):
    """到货确认响应"""
    package_code: str
    status: str
    goods_status: Optional[str] = None
    order_status: Optional[str] = None
    triggered_repacking: Optional[bool] = None
    new_package_code: Optional[str] = None


class BatchArrivalConfirmResponse(BaseModel):
    """批量到货确认响应"""
    total: int
    success_count: int
    failed_count: int
    results: Optional[List[Dict[str, Any]]] = None
    errors: Optional[List[Dict[str, Any]]] = None


class ArrivalPackageResponse(BaseModel):
    """到站包裹响应"""
    package_code: str
    schedule_code: str
    from_node_code: str
    to_node_code: str
    status: str
    arrived_at: Optional[str] = None
