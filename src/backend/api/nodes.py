from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from schemas.node import StorageCenterCreate, StorageCenterUpdate, SortingCenterCreate, SortingCenterUpdate
from services.node_service import NodeService
from config.database import get_db
from core.response_schema import (
    ResponseSchema,
    NodeListData,
    NodeDetailData,
    StorageCenterCreateData,
    StorageCenterUpdateData,
    StorageCenterDeleteData,
    SortingCenterCreateData,
    SortingCenterUpdateData,
    SortingCenterDeleteData
)

router = APIRouter(prefix="/api/nodes", tags=["节点管理"])


@router.get("", response_model=ResponseSchema[NodeListData])
async def list_nodes(
    page: int = 1,
    page_size: int = 20,
    node_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """节点列表"""
    result = await NodeService.get_nodes(page, page_size, node_type, db)
    return result


@router.post("/storage-centers", response_model=ResponseSchema[StorageCenterCreateData])
async def create_storage_center(
    center: StorageCenterCreate,
    db: Session = Depends(get_db)
):
    """新增存储中心"""
    result = await NodeService.create_storage_center(center.dict(), db)
    return result


@router.put("/storage-centers/{node_code}", response_model=ResponseSchema[StorageCenterUpdateData])
async def update_storage_center(
    node_code: str,
    center: StorageCenterUpdate,
    db: Session = Depends(get_db)
):
    """编辑存储中心"""
    result = await NodeService.update_storage_center(node_code, center.dict(exclude_unset=True), db)
    return result


@router.delete("/storage-centers/{node_code}", response_model=ResponseSchema[StorageCenterDeleteData])
async def delete_storage_center(
    node_code: str,
    db: Session = Depends(get_db)
):
    """删除存储中心"""
    result = await NodeService.delete_storage_center(node_code, db)
    return result


@router.post("/sorting-centers", response_model=ResponseSchema[SortingCenterCreateData])
async def create_sorting_center(
    center: SortingCenterCreate,
    db: Session = Depends(get_db)
):
    """新增分拣中心"""
    result = await NodeService.create_sorting_center(center.dict(), db)
    return result


@router.put("/sorting-centers/{node_code}", response_model=ResponseSchema[SortingCenterUpdateData])
async def update_sorting_center(
    node_code: str,
    center: SortingCenterUpdate,
    db: Session = Depends(get_db)
):
    """编辑分拣中心"""
    result = await NodeService.update_sorting_center(node_code, center.dict(exclude_unset=True), db)
    return result


@router.delete("/sorting-centers/{node_code}", response_model=ResponseSchema[SortingCenterDeleteData])
async def delete_sorting_center(
    node_code: str,
    db: Session = Depends(get_db)
):
    """删除分拣中心"""
    result = await NodeService.delete_sorting_center(node_code, db)
    return result


@router.get("/{node_code}", response_model=ResponseSchema[NodeDetailData])
async def get_node(
    node_code: str,
    db: Session = Depends(get_db)
):
    """节点详情"""
    result = await NodeService.get_node(node_code, db)
    return result

