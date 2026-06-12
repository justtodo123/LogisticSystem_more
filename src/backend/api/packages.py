from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from schemas.package import PackageRepack
from services.package_service import PackageService
from config.database import get_db
from core.response_schema import (
    ResponseSchema,
    PackageListData,
    PackageDetailData,
    PackageRepackData
)

router = APIRouter(prefix="/api/packages", tags=["包裹管理"])


@router.get("", response_model=ResponseSchema[PackageListData])
async def list_packages(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    from_node_code: Optional[str] = None,
    to_node_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """包裹列表"""
    result = await PackageService.get_packages(page, page_size, status, from_node_code, to_node_code, db)
    return result


@router.get("/{package_code}", response_model=ResponseSchema[PackageDetailData])
async def get_package(
    package_code: str,
    db: Session = Depends(get_db)
):
    """包裹详情"""
    result = await PackageService.get_package(package_code, db)
    return result


@router.post("/{package_code}/repack", response_model=ResponseSchema[PackageRepackData])
async def repack_package(
    package_code: str,
    repack: PackageRepack,
    db: Session = Depends(get_db)
):
    """手动重新打包"""
    result = await PackageService.repack_package(package_code, repack, db)
    return result
