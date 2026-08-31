from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from api.dependencies import require_permission, require_permission_with_optional_idempotency
from schemas.vehicle import VehicleCreate, VehicleUpdate
from services.vehicle_service import VehicleService
from config.database import get_db
from core.response_schema import (
    ResponseSchema,
    VehicleListData,
    VehicleDetailData,
    VehicleCreateData,
    VehicleUpdateData,
    VehicleDeleteData
)
from models.user import User
from utils.cache import cache_delete_prefix, cached
from core.error_codes import CODE_SUCCESS

router = APIRouter(prefix="/api/vehicles", tags=["车辆管理"])


@cached(ttl=300, key_prefix="vehicles:list", keys=("page", "page_size", "status", "node_code"))
async def _load_vehicles(page: int, page_size: int, status: Optional[str], node_code: Optional[str], db: Session):
    """车辆列表（带缓存，T4-3）"""
    return await VehicleService.get_vehicles(page, page_size, status, node_code, db)


async def _invalidate_vehicle_list_cache() -> None:
    """车辆数据变更后使列表缓存失效"""
    await cache_delete_prefix("vehicles:list")


@router.get("", response_model=ResponseSchema[VehicleListData])
async def list_vehicles(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    node_code: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("vehicles:read"))
):
    """车辆列表"""
    result = await _load_vehicles(page, page_size, status, node_code, db)
    return result


@router.post("", response_model=ResponseSchema[VehicleCreateData])
async def create_vehicle(
    vehicle: VehicleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission_with_optional_idempotency("vehicles:write"))
):
    """新增车辆"""
    result = await VehicleService.create_vehicle(vehicle, db)
    if result.get("code") == CODE_SUCCESS:
        await _invalidate_vehicle_list_cache()
    return result


@router.get("/{vehicle_code}", response_model=ResponseSchema[VehicleDetailData])
async def get_vehicle(
    vehicle_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("vehicles:read"))
):
    """车辆详情"""
    result = await VehicleService.get_vehicle(vehicle_code, db)
    return result


@router.put("/{vehicle_code}", response_model=ResponseSchema[VehicleUpdateData])
async def update_vehicle(
    vehicle_code: str,
    vehicle: VehicleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission_with_optional_idempotency("vehicles:write"))
):
    """编辑车辆"""
    result = await VehicleService.update_vehicle(vehicle_code, vehicle, db)
    if result.get("code") == CODE_SUCCESS:
        await _invalidate_vehicle_list_cache()
    return result


@router.delete("/{vehicle_code}", response_model=ResponseSchema[VehicleDeleteData])
async def delete_vehicle(
    vehicle_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission_with_optional_idempotency("vehicles:write"))
):
    """删除车辆"""
    result = await VehicleService.delete_vehicle(vehicle_code, db)
    if result.get("code") == CODE_SUCCESS:
        await _invalidate_vehicle_list_cache()
    return result
