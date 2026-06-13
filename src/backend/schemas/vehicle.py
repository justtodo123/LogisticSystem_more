from datetime import datetime
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
    last_arrived_node_code: str
    last_arrived_node_name: str
    status: str
    node_code: str
    node_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
