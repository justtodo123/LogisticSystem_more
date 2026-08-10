from datetime import datetime, time
from typing import Optional
from pydantic import BaseModel


class VehicleCreate(BaseModel):
    """车辆创建请求"""
    vehicle_code: str
    model: str
    capacity: float
    energy_type: str  # fuel / electric
    vehicle_type: Optional[str] = "normal"  # normal / cold_chain
    capability_tags: Optional[list[str]] = None
    plate_number: Optional[str] = None
    time_window_start: Optional[str] = None  # HH:MM 格式
    time_window_end: Optional[str] = None    # HH:MM 格式
    route_limit: Optional[int] = 5
    cost_per_km: Optional[float] = 5.0
    load_rate_max: Optional[float] = 0.9
    last_arrived_node_code: str
    node_code: str
    status: Optional[str] = "idle"


class VehicleUpdate(BaseModel):
    """车辆更新请求"""
    model: Optional[str] = None
    capacity: Optional[float] = None
    energy_type: Optional[str] = None
    vehicle_type: Optional[str] = None
    capability_tags: Optional[list[str]] = None
    plate_number: Optional[str] = None
    time_window_start: Optional[str] = None
    time_window_end: Optional[str] = None
    route_limit: Optional[int] = None
    cost_per_km: Optional[float] = None
    load_rate_max: Optional[float] = None
    node_code: Optional[str] = None
    last_arrived_node_code: Optional[str] = None
    status: Optional[str] = None


class VehicleResponse(BaseModel):
    """车辆响应"""
    vehicle_code: str
    model: str
    capacity: float
    energy_type: str
    vehicle_type: str
    capability_tags: Optional[list[str]] = None
    plate_number: Optional[str] = None
    time_window_start: Optional[str] = None
    time_window_end: Optional[str] = None
    route_limit: int
    cost_per_km: float
    load_rate_max: float
    last_arrived_node_code: str
    last_arrived_node_name: str
    status: str
    node_code: str
    node_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
