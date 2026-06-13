from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel


class PackageRepack(BaseModel):
    """包裹重新打包请求"""
    goods_codes: List[str]


class PackageResponse(BaseModel):
    """包裹响应"""
    package_code: str
    weight: float
    volume: float
    status: str
    from_node_code: str
    from_node_name: str
    to_node_code: str
    to_node_name: str
    from_longitude: Optional[float] = None
    from_latitude: Optional[float] = None
    to_longitude: Optional[float] = None
    to_latitude: Optional[float] = None
    goods_items: List[Dict[str, str]]
    dispatch_code: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
