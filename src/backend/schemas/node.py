from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class NodeResponse(BaseModel):
    """节点响应"""
    node_code: str
    name: str
    location: str
    latitude: float
    longitude: float
    node_type: str  # storage_center / sorting_center
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StorageCenterCreate(BaseModel):
    """存储中心创建请求"""
    node_code: str
    name: str
    location: str
    latitude: float
    longitude: float
    capacity: float
    inventory: Optional[int] = 0


class StorageCenterUpdate(BaseModel):
    """存储中心更新请求"""
    name: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    capacity: Optional[float] = None
    inventory: Optional[int] = None


class StorageCenterResponse(BaseModel):
    """存储中心响应"""
    node_code: str
    name: str
    location: str
    latitude: float
    longitude: float
    capacity: float
    inventory: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SortingCenterCreate(BaseModel):
    """分拣中心创建请求"""
    node_code: str
    name: str
    location: str
    latitude: float
    longitude: float
    level: int  # 0=0级, 1=1级
    capacity: Optional[float] = None
    max_storage_time: Optional[int] = None


class SortingCenterUpdate(BaseModel):
    """分拣中心更新请求"""
    name: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    level: Optional[int] = None
    capacity: Optional[float] = None
    max_storage_time: Optional[int] = None


class SortingCenterResponse(BaseModel):
    """分拣中心响应"""
    node_code: str
    name: str
    location: str
    latitude: float
    longitude: float
    level: int
    capacity: Optional[float] = None
    max_storage_time: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
