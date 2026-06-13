from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class NodeDispatchRequest(BaseModel):
    """F005节点调度请求"""
    schedule_code: str
    demo_mode: bool = False


class NodeDispatchTaskResponse(BaseModel):
    """节点调度任务响应"""
    from_node_code: str
    to_node_code: str
    package_codes: List[str]
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
    created_at: datetime
    updated_at: datetime
    dispatches: Optional[List[NodeDispatchResponse]] = None

    class Config:
        from_attributes = True


class DispatchBatchListResponse(BaseModel):
    """调度批次列表响应"""
    items: List[DispatchBatchResponse]
    total: int
