from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from schemas.order import OrderCreate, OrderUpdate
from services.order_service import OrderService
from config.database import get_db
from core.response_schema import (
    ResponseSchema,
    OrderListData,
    OrderDetailData,
    OrderCreateData,
    OrderUpdateData,
    OrderImportData,
    OrderDeleteData
)

router = APIRouter(prefix="/api/orders", tags=["订单管理"])


@router.get("", response_model=ResponseSchema[OrderListData])
async def list_orders(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """订单列表"""
    result = await OrderService.get_orders(page, page_size, status, db)
    return result


@router.post("", response_model=ResponseSchema[OrderCreateData])
async def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db)
):
    """新增订单"""
    result = await OrderService.create_order(order, db)
    return result


@router.get("/{order_code}", response_model=ResponseSchema[OrderDetailData])
async def get_order(
    order_code: str,
    db: Session = Depends(get_db)
):
    """订单详情"""
    result = await OrderService.get_order(order_code, db)
    return result


@router.put("/{order_code}", response_model=ResponseSchema[OrderUpdateData])
async def update_order(
    order_code: str,
    order: OrderUpdate,
    db: Session = Depends(get_db)
):
    """编辑订单"""
    result = await OrderService.update_order(order_code, order, db)
    return result


@router.delete("/{order_code}", response_model=ResponseSchema[OrderDeleteData])
async def delete_order(
    order_code: str,
    db: Session = Depends(get_db)
):
    """删除订单"""
    result = await OrderService.delete_order(order_code, db)
    return result


@router.post("/import", response_model=ResponseSchema[OrderImportData])
async def import_orders(
    file: UploadFile = File(...),
    skip_errors: bool = True,
    db: Session = Depends(get_db)
):
    """批量导入订单"""
    result = await OrderService.import_orders(file, skip_errors, db)
    return result
