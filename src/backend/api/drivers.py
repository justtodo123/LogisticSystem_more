from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from schemas.driver import DriverCreate, DriverUpdate
from services.driver_service import DriverService
from config.database import get_db
from core.response_schema import (
    ResponseSchema,
    DriverListData,
    DriverDetailData,
    DriverCreateData,
    DriverUpdateData,
    DriverDeleteData
)

router = APIRouter(prefix="/api/drivers", tags=["司机管理"])


@router.get("", response_model=ResponseSchema[DriverListData])
async def list_drivers(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    node_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """司机列表"""
    result = await DriverService.get_drivers(page, page_size, status, node_code, db)
    return result


@router.post("", response_model=ResponseSchema[DriverCreateData])
async def create_driver(
    driver: DriverCreate,
    db: Session = Depends(get_db)
):
    """新增司机"""
    result = await DriverService.create_driver(driver, db)
    return result


@router.get("/{driver_code}", response_model=ResponseSchema[DriverDetailData])
async def get_driver(
    driver_code: str,
    db: Session = Depends(get_db)
):
    """司机详情"""
    result = await DriverService.get_driver(driver_code, db)
    return result


@router.put("/{driver_code}", response_model=ResponseSchema[DriverUpdateData])
async def update_driver(
    driver_code: str,
    driver: DriverUpdate,
    db: Session = Depends(get_db)
):
    """编辑司机"""
    result = await DriverService.update_driver(driver_code, driver, db)
    return result


@router.delete("/{driver_code}", response_model=ResponseSchema[DriverDeleteData])
async def delete_driver(
    driver_code: str,
    db: Session = Depends(get_db)
):
    """删除司机"""
    result = await DriverService.delete_driver(driver_code, db)
    return result
