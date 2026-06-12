from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from schemas.goods import GoodsUpdate
from services.goods_service import GoodsService
from config.database import get_db
from core.response_schema import (
    ResponseSchema,
    GoodsListData,
    GoodsDetailData,
    GoodsUpdateData
)

router = APIRouter(prefix="/api/goods", tags=["货物管理"])


@router.get("", response_model=ResponseSchema[GoodsListData])
async def list_goods(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    node_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """货物列表"""
    result = await GoodsService.get_goods(page, page_size, status, node_code, db)
    return result


@router.get("/{goods_code}", response_model=ResponseSchema[GoodsDetailData])
async def get_good(
    goods_code: str,
    db: Session = Depends(get_db)
):
    """货物详情"""
    result = await GoodsService.get_good(goods_code, db)
    return result


@router.put("/{goods_code}", response_model=ResponseSchema[GoodsUpdateData])
async def update_good(
    goods_code: str,
    goods: GoodsUpdate,
    db: Session = Depends(get_db)
):
    """编辑货物"""
    result = await GoodsService.update_good(goods_code, goods, db)
    return result
