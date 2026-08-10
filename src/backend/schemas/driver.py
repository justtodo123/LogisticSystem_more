from datetime import datetime, time
from typing import Optional
from pydantic import BaseModel


class DriverCreate(BaseModel):
    """司机创建请求"""
    driver_code: str
    name: str
    phone: str
    license_type: str  # C1/C2/B1/B2/A1/A2
    shift: str
    shift_start: Optional[str] = None   # HH:MM 格式
    shift_end: Optional[str] = None     # HH:MM 格式
    max_drive_hours: Optional[float] = 8.0
    max_continuous_hours: Optional[float] = 4.0
    node_code: str
    status: Optional[str] = "idle"


class DriverUpdate(BaseModel):
    """司机更新请求"""
    name: Optional[str] = None
    phone: Optional[str] = None
    license_type: Optional[str] = None
    shift: Optional[str] = None
    shift_start: Optional[str] = None
    shift_end: Optional[str] = None
    max_drive_hours: Optional[float] = None
    max_continuous_hours: Optional[float] = None
    node_code: Optional[str] = None
    status: Optional[str] = None


class DriverResponse(BaseModel):
    """司机响应"""
    driver_code: str
    name: str
    phone: str
    license_type: str
    shift: str
    shift_start: Optional[str] = None
    shift_end: Optional[str] = None
    max_drive_hours: float
    max_continuous_hours: float
    node_code: str
    node_name: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
