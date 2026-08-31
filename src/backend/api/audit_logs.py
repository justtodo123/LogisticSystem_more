"""
审计日志查询 API

GET /api/audit-logs — 分页查询审计日志（按事件类型、时间范围过滤）
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from config.database import get_db
from api.dependencies import require_permission
from models.user import User
from services.log_service import LogService
from utils.response import success_response, error_response

router = APIRouter(prefix="/api/audit-logs", tags=["审计日志"])


@router.get("")
async def list_audit_logs(
    event_name: Optional[str] = Query(None, description="事件类型过滤"),
    user_id: Optional[int] = Query(None, description="用户ID过滤"),
    start_time: Optional[datetime] = Query(None, description="开始时间（ISO 8601）"),
    end_time: Optional[datetime] = Query(None, description="结束时间（ISO 8601）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(require_permission("audit:read")),
    db: Session = Depends(get_db),
):
    """查询审计日志（分页）"""
    events = LogService.get_events(
        user_id=user_id,
        event_name=event_name,
        start_time=start_time,
        end_time=end_time,
        limit=page_size,
        db=db,
    )

    # 简单分页
    offset = (page - 1) * page_size
    items = [
        {
            "id": e.id,
            "event_name": e.event_name,
            "user_id": e.user_id,
            "role": e.role,
            "event_data": e.event_data,
            "ip_address": e.ip_address,
            "user_agent": e.user_agent,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]

    return success_response(
        data={"items": items[offset:offset + page_size], "total": len(items)},
    )
