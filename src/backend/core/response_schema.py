"""统一响应Schema定义"""
from datetime import datetime
from typing import Generic, TypeVar, Optional, Any, Dict, List
from pydantic import BaseModel

# 泛型类型
T = TypeVar('T')


class MetaSchema(BaseModel):
    """Meta信息Schema"""
    degraded: bool = False
    degraded_reason: Optional[str] = None


class ResponseSchema(BaseModel, Generic[T]):
    """统一响应Schema"""
    code: int
    message: str
    data: Optional[T] = None
    meta: Optional[MetaSchema] = None


# 订单相关Response Schema
class OrderListData(BaseModel):
    """订单列表Data"""
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int


class OrderDetailData(BaseModel):
    """订单详情Data"""
    order_code: str
    destination_node_code: str
    destination_node_name: str
    time_window: str
    status: str
    goods: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class OrderCreateData(BaseModel):
    """订单创建Data"""
    order_code: str
    destination_node_code: str
    destination_node_name: str
    time_window: str
    status: str
    goods_count: int
    created_at: datetime
    updated_at: datetime


class OrderUpdateData(BaseModel):
    """订单更新Data"""
    order_code: str
    destination_node_code: str
    destination_node_name: str
    time_window: str
    status: str
    created_at: datetime
    updated_at: datetime


class OrderImportData(BaseModel):
    """订单导入Data"""
    success_count: int
    failed_count: int
    failed_rows: List[Dict[str, Any]]


class OrderDeleteData(BaseModel):
    """订单删除Data - 无返回数据"""
    pass


# 货物相关Response Schema
class GoodsListData(BaseModel):
    """货物列表Data"""
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int


class GoodsDetailData(BaseModel):
    """货物详情Data"""
    goods_code: str
    goods_name: str
    goods_type: str
    weight: float
    volume: float
    status: str
    order_code: str
    node_code: str
    node_name: str
    created_at: datetime
    updated_at: datetime


class GoodsUpdateData(BaseModel):
    """货物更新Data"""
    goods_code: str
    goods_name: str
    goods_type: str
    weight: float
    volume: float
    status: str
    order_code: str
    node_code: str
    node_name: str
    created_at: datetime
    updated_at: datetime


# 包裹相关Response Schema
class PackageListData(BaseModel):
    """包裹列表Data"""
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int


class PackageDetailData(BaseModel):
    """包裹详情Data"""
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


class PackageRepackData(BaseModel):
    """包裹重新打包Data"""
    package_code: str
    weight: float
    volume: float
    status: str
    from_node_code: str
    from_node_name: str
    to_node_code: str
    to_node_name: str
    goods_items: List[Dict[str, str]]
    created_at: datetime
    updated_at: datetime


# 车辆相关Response Schema
class VehicleListData(BaseModel):
    """车辆列表Data"""
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int


class VehicleDetailData(BaseModel):
    """车辆详情Data"""
    vehicle_code: str
    model: str
    capacity: float
    energy_type: str
    vehicle_type: str
    capability_tags: Optional[List[str]] = None
    last_arrived_node_code: str
    last_arrived_node_name: str
    status: str
    node_code: str
    node_name: str
    created_at: datetime
    updated_at: datetime


class VehicleCreateData(BaseModel):
    """车辆创建Data"""
    vehicle_code: str
    model: str
    capacity: float
    energy_type: str
    vehicle_type: str
    capability_tags: Optional[List[str]] = None
    last_arrived_node_code: str
    last_arrived_node_name: str
    status: str
    node_code: str
    node_name: str
    created_at: datetime
    updated_at: datetime


class VehicleUpdateData(BaseModel):
    """车辆更新Data"""
    vehicle_code: str
    model: str
    capacity: float
    energy_type: str
    vehicle_type: str
    capability_tags: Optional[List[str]] = None
    last_arrived_node_code: str
    last_arrived_node_name: str
    status: str
    node_code: str
    node_name: str
    created_at: datetime
    updated_at: datetime


class VehicleDeleteData(BaseModel):
    """车辆删除Data - 无返回数据"""
    pass


# 司机相关Response Schema
class DriverListData(BaseModel):
    """司机列表Data"""
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int


class DriverDetailData(BaseModel):
    """司机详情Data"""
    driver_code: str
    name: str
    phone: str
    license_type: str
    shift: str
    node_code: str
    node_name: str
    status: str
    created_at: datetime
    updated_at: datetime


class DriverCreateData(BaseModel):
    """司机创建Data"""
    driver_code: str
    name: str
    phone: str
    license_type: str
    shift: str
    node_code: str
    node_name: str
    status: str
    created_at: datetime
    updated_at: datetime


class DriverUpdateData(BaseModel):
    """司机更新Data"""
    driver_code: str
    name: str
    phone: str
    license_type: str
    shift: str
    node_code: str
    node_name: str
    status: str
    created_at: datetime
    updated_at: datetime


class DriverDeleteData(BaseModel):
    """司机删除Data - 无返回数据"""
    pass


# 节点相关Response Schema
class NodeListData(BaseModel):
    """节点列表Data"""
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int


class NodeDetailData(BaseModel):
    """节点详情Data"""
    node_code: str
    name: str
    location: str
    latitude: float
    longitude: float
    node_type: str
    capacity: Optional[float] = None
    inventory: Optional[int] = None
    level: Optional[int] = None
    max_storage_time: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class StorageCenterCreateData(BaseModel):
    """存储中心创建Data"""
    node_code: str
    name: str
    location: str
    latitude: float
    longitude: float
    capacity: float
    inventory: int
    created_at: datetime
    updated_at: datetime


class StorageCenterUpdateData(BaseModel):
    """存储中心更新Data"""
    node_code: str
    name: str
    location: str
    latitude: float
    longitude: float
    capacity: float
    inventory: int
    created_at: datetime
    updated_at: datetime


class StorageCenterDeleteData(BaseModel):
    """存储中心删除Data - 无返回数据"""
    pass


class SortingCenterCreateData(BaseModel):
    """分拣中心创建Data"""
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


class SortingCenterUpdateData(BaseModel):
    """分拣中心更新Data"""
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


class SortingCenterDeleteData(BaseModel):
    """分拣中心删除Data - 无返回数据"""
    pass
