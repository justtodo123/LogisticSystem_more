from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/exceptions", tags=["exceptions"])


class ExceptionEventCreate(BaseModel):
    exception_type: str
    severity: str
    recommended_action: str
    trigger_node_code: Optional[str] = None
    related_route_code: Optional[str] = None
    description: str


class ExceptionEventUpdate(BaseModel):
    status: Optional[str] = None
    resolution_note: Optional[str] = None


class ReplanRequest(BaseModel):
    action: str
    reason: str


@router.get("")
async def get_exceptions():
    """获取异常事件列表 - P1 占位"""
    raise HTTPException(status_code=501, detail="异常管理API尚未实现")


@router.post("")
async def create_exception(exception: ExceptionEventCreate):
    """创建异常事件 - P1 占位"""
    raise HTTPException(status_code=501, detail="异常管理API尚未实现")


@router.get("/{code}")
async def get_exception_detail(code: str):
    """获取异常事件详情 - P1 占位"""
    raise HTTPException(status_code=501, detail="异常管理API尚未实现")


@router.put("/{code}")
async def update_exception(code: str, update: ExceptionEventUpdate):
    """更新异常事件 - P1 占位"""
    raise HTTPException(status_code=501, detail="异常管理API尚未实现")


@router.post("/{code}/replan")
async def replan(code: str, replan_request: ReplanRequest):
    """触发重规划 - P1 占位"""
    raise HTTPException(status_code=501, detail="异常管理API尚未实现")
