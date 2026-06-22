"""
异常管理 API 路由

提供异常事件的 CRUD 和重规划触发功能：
- GET   /api/exceptions              : 异常事件列表
- POST  /api/exceptions              : 创建异常事件
- GET   /api/exceptions/{event_code} : 异常详情
- POST  /api/exceptions/{event_code}/replan  : 触发重规划
- PUT   /api/exceptions/{event_code}/resolve  : 标记已解决

阶段7实现。
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from services.exception_service import ExceptionService
from schemas.exception_event import (
    CreateExceptionEventRequest,
    TriggerReplanRequest,
    UpdateExceptionRequest,
)
from config.database import get_db
from api.dependencies import get_current_user, require_dispatcher
from models.user import User

router = APIRouter(prefix="/api/exceptions", tags=["异常管理"])


@router.get("")
async def get_exceptions(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(default=None, description="状态筛选：open / resolved"),
    exception_type: Optional[str] = Query(default=None, description="异常类型：road / package / node"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取异常事件列表（分页、筛选）

    需要角色：dispatcher / manager
    """
    return await ExceptionService.get_exception_events(
        db=db,
        page=page,
        page_size=page_size,
        status=status,
        exception_type=exception_type,
    )


@router.post("")
async def create_exception(
    body: CreateExceptionEventRequest,
    current_user: User = Depends(require_dispatcher),
    db: Session = Depends(get_db),
):
    """
    创建异常事件

    需要角色：dispatcher

    请求体示例：
    {
        "exception_type": "node",
        "exception_subtype": "capacity_limit",
        "target_type": "node",
        "target_code": "SC001",
        "description": "存储中心容量不足",
        "recommended_action": "redispatch",
        "related_schedule_code": "GS20260609001"
    }
    """
    return await ExceptionService.create_exception_event(
        db=db,
        data=body,
    )


@router.get("/{event_code}")
async def get_exception_detail(
    event_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取异常事件详情

    需要角色：dispatcher / manager
    """
    return await ExceptionService.get_exception_event_by_code(
        db=db,
        event_code=event_code,
    )


@router.post("/{event_code}/replan")
async def trigger_replan(
    event_code: str,
    body: TriggerReplanRequest,
    current_user: User = Depends(require_dispatcher),
    db: Session = Depends(get_db),
):
    """
    触发重规划（redispatch 或 reroute）

    需要角色：dispatcher

    根据请求体中的 action 选择重规划类型：
    - redispatch: 重新执行 F007→F021→F005→F006
    - reroute: 重新执行 F006 路径规划
    """
    return await ExceptionService.trigger_replan(
        db=db,
        event_code=event_code,
        action=body.action,
        replan_reason=body.reason,
    )


@router.put("/{event_code}")
async def update_exception(
    event_code: str,
    body: UpdateExceptionRequest,
    current_user: User = Depends(require_dispatcher),
    db: Session = Depends(get_db),
):
    """
    更新异常事件

    需要角色：dispatcher

    可更新 status。
    """
    return await ExceptionService.update_exception(
        db=db,
        event_code=event_code,
        status=body.status,
    )


@router.put("/{event_code}/resolve")
async def resolve_exception(
    event_code: str,
    current_user: User = Depends(require_dispatcher),
    db: Session = Depends(get_db),
):
    """
    标记异常已解决

    需要角色：dispatcher

    将异常状态从 open 改为 resolved，自动记录 resolved_at。
    """
    return await ExceptionService.resolve_exception(
        db=db,
        event_code=event_code,
    )
