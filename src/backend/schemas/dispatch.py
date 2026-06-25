from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class NodeDispatchRequest(BaseModel):
    """F005节点调度请求"""
    schedule_code: str
    demo_mode: bool = False


class GoodsItemDetail(BaseModel):
    """货物项详情（展开后，含货物描述和订单编码）"""
    goods_code: str
    goods_name: str
    goods_type: str
    order_code: str


class PackageDetail(BaseModel):
    """包裹详情（展开后，含货物项详情）"""
    package_code: str
    weight: float
    volume: float
    goods_items: List[GoodsItemDetail]


class NodeDispatchTaskResponse(BaseModel):
    """节点调度任务响应（P1-07 修改：新增 node_name，展开 package_details）"""
    from_node_code: str
    from_node_name: str
    to_node_code: str
    to_node_name: str
    package_details: List[PackageDetail]
    is_return: bool

    class Config:
        from_attributes = True


class NodeDispatchResponse(BaseModel):
    """节点调度明细响应"""
    dispatch_code: str
    vehicle_code: str
    driver_code: Optional[str] = None
    level_phase: int
    tasks: List[NodeDispatchTaskResponse]
    total_distance: float
    total_time: float

    class Config:
        from_attributes = True


class DispatchBatchResponse(BaseModel):
    """调度批次响应"""
    batch_code: str
    schedule_code: str
    status: str
    demo_mode: bool
    l0_l1_dispatch_count: int
    l1_l2_dispatch_count: int
    unallocated_packages: Optional[List[str]] = None  # 未分配的包裹编码列表
    created_at: datetime
    updated_at: datetime
    dispatches: Optional[List[NodeDispatchResponse]] = None

    class Config:
        from_attributes = True


class DispatchBatchListResponse(BaseModel):
    """调度批次列表响应"""
    items: List[DispatchBatchResponse]
    total: int


class DispatchDetailResponse(BaseModel):
    """调度明细详情响应（用于 GET /api/schedule/dispatches/{dispatch_code}）"""
    dispatch_code: str
    batch_code: str
    vehicle_code: str
    vehicle_name: Optional[str] = None
    driver_code: Optional[str] = None
    driver_name: Optional[str] = None
    level_phase: int
    tasks: List[NodeDispatchTaskResponse]
    total_distance: float
    total_time: float


class DispatchesListResponse(BaseModel):
    """调度明细列表响应（用于 GET /api/schedule/batches/{batch_code}/dispatches 等）"""
    items: List[DispatchDetailResponse]
    total: int
