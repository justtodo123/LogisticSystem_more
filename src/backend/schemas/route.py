"""
路径规划 Pydantic Schema 定义
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class RoutePlanRequest(BaseModel):
    """路径规划请求"""
    batch_code: str = Field(..., description="调度批次编码")
    dispatch_codes: Optional[List[str]] = Field(None, description="节点调度明细编码列表，不传则处理批次下所有dispatch")


class RouteSegment(BaseModel):
    """路径路段"""
    road_name: str = Field(..., description="道路名称")
    start_lng: float = Field(..., description="起点经度")
    start_lat: float = Field(..., description="起点纬度")
    end_lng: float = Field(..., description="终点经度")
    end_lat: float = Field(..., description="终点纬度")


class RouteItem(BaseModel):
    """路线列表项"""
    route_code: str = Field(..., description="路线编码")
    batch_code: str = Field(..., description="批次编码")
    dispatch_code: str = Field(..., description="调度明细编码")
    vehicle_code: str = Field(..., description="车辆编码")
    total_distance: float = Field(..., description="总距离(km)")
    total_time: float = Field(..., description="总时间(分钟)")
    total_emission: float = Field(..., description="总碳排放(kg)")
    created_at: str = Field(..., description="创建时间")


class RouteListResponse(BaseModel):
    """路线列表响应"""
    items: List[RouteItem] = Field(..., description="路线列表")
    total: int = Field(..., description="筛选后的唯一路线数")
    page: int = Field(..., description="当前页，从 1 开始")
    page_size: int = Field(..., description="每页数量，默认 20，最大 200")


class RouteDetailResponse(BaseModel):
    """路线详情响应"""
    route_code: str = Field(..., description="路线编码")
    batch_code: str = Field(..., description="批次编码")
    dispatch_code: str = Field(..., description="调度明细编码")
    vehicle_code: str = Field(..., description="车辆编码")
    route_segments: List[RouteSegment] = Field(..., description="路径路段")
    total_distance: float = Field(..., description="总距离(km)")
    total_time: float = Field(..., description="总时间(分钟)")
    total_emission: float = Field(..., description="总碳排放(kg)")
    algorithm_type: str = Field(..., description="算法类型")
    created_at: str = Field(..., description="创建时间")


class RouteCoordinate(BaseModel):
    """路线坐标"""
    route_code: str = Field(..., description="路线编码")
    batch_code: str = Field(..., description="批次编码")
    coordinates: List[List[float]] = Field(..., description="坐标数组")
    total_distance: float = Field(..., description="总距离(km)")


class RouteCoordinatesResponse(BaseModel):
    """车辆路线坐标响应"""
    vehicle_code: str = Field(..., description="车辆编码")
    routes: List[RouteCoordinate] = Field(..., description="路线坐标列表")
