from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from api.dependencies import get_current_user, require_dispatcher_with_optional_idempotency
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
from models.user import User

router = APIRouter(prefix="/api/orders", tags=["订单管理"])


@router.get("", response_model=ResponseSchema[OrderListData])
async def list_orders(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """订单列表"""
    result = await OrderService.get_orders(page, page_size, status, db)
    return result


@router.post("", response_model=ResponseSchema[OrderCreateData])
async def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dispatcher_with_optional_idempotency)
):
    """新增订单"""
    result = await OrderService.create_order(order, db)
    return result


@router.get("/{order_code}", response_model=ResponseSchema[OrderDetailData])
async def get_order(
    order_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """订单详情"""
    result = await OrderService.get_order(order_code, db)
    return result


@router.put("/{order_code}", response_model=ResponseSchema[OrderUpdateData])
async def update_order(
    order_code: str,
    order: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dispatcher_with_optional_idempotency)
):
    """编辑订单"""
    result = await OrderService.update_order(order_code, order, db)
    return result


@router.delete("/{order_code}", response_model=ResponseSchema[OrderDeleteData])
async def delete_order(
    order_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dispatcher_with_optional_idempotency)
):
    """删除订单"""
    result = await OrderService.delete_order(order_code, db)
    return result


@router.post("/import", response_model=ResponseSchema[OrderImportData])
async def import_orders(
    file: UploadFile = File(...),
    skip_errors: bool = True,
    column_mapping: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dispatcher_with_optional_idempotency)
):
    """批量导入订单

    - skip_errors=true（默认）：错误行跳过，成功行入库，返回 failed_rows 指明失败行
    - skip_errors=false：存在任一错误行则整体回滚
    - column_mapping：可选 JSON 字符串，自定义列映射，格式 {"文件表头名": "系统字段名"}
      系统字段：destination_node_code / storage_center_code / time_window /
               goods_name / goods_type / weight / volume
      不传时默认文件表头即为系统字段名（向后兼容原模板）
    """
    result = await OrderService.import_orders(file, skip_errors, db, column_mapping)
    return result


@router.post("/{order_code}/close", response_model=ResponseSchema[OrderUpdateData])
async def close_order(
    order_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dispatcher_with_optional_idempotency)
):
    """关闭订单（T1-1 新增：unassigned/assigned → closed）"""
    result = await OrderService.close_order(order_code, db)
    return result
