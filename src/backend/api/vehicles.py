from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

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

router = APIRouter(prefix="/api/vehicles", tags=["车辆管理"])


@router.get("", response_model=ResponseSchema[VehicleListData])
async def list_vehicles(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    node_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """车辆列表"""
    result = await VehicleService.get_vehicles(page, page_size, status, node_code, db)
    return result


@router.post("", response_model=ResponseSchema[VehicleCreateData])
async def create_vehicle(
    vehicle: VehicleCreate,
    db: Session = Depends(get_db)
):
    """新增车辆"""
    result = await VehicleService.create_vehicle(vehicle, db)
    return result


@router.get("/{vehicle_code}", response_model=ResponseSchema[VehicleDetailData])
async def get_vehicle(
    vehicle_code: str,
    db: Session = Depends(get_db)
):
    """车辆详情"""
    result = await VehicleService.get_vehicle(vehicle_code, db)
    return result


@router.put("/{vehicle_code}", response_model=ResponseSchema[VehicleUpdateData])
async def update_vehicle(
    vehicle_code: str,
    vehicle: VehicleUpdate,
    db: Session = Depends(get_db)
):
    """编辑车辆"""
    result = await VehicleService.update_vehicle(vehicle_code, vehicle, db)
    return result


@router.delete("/{vehicle_code}", response_model=ResponseSchema[VehicleDeleteData])
async def delete_vehicle(
    vehicle_code: str,
    db: Session = Depends(get_db)
):
    """删除车辆"""
    result = await VehicleService.delete_vehicle(vehicle_code, db)
    return result
