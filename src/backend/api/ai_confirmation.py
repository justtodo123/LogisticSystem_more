"""
AI 建议确认闸门 API（T6-2）

1. GET  /api/ai/suggestions              — 列出 AI 建议（可按 status 过滤）
2. POST /api/ai/suggestions/{id}/confirm — 确认建议（suggestion/action 级别触发实际调度修改）
3. POST /api/ai/suggestions/{id}/reject  — 拒绝建议（仅记录，不触发调度修改）
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import (
    get_current_user,
    require_dispatcher,
    require_dispatcher_with_idempotency,
)
from config.database import get_db
from models.user import User
from services.ai_suggestion_service import (
    confirm_suggestion,
    list_suggestions,
    reject_suggestion,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai/suggestions", tags=["AI 建议闸门"])


class SuggestionDecisionRequest(BaseModel):
    """确认/拒绝建议时可选的操作备注"""
    note: Optional[str] = None


@router.get("")
async def get_suggestions(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """列出 AI 建议（默认全部，可按 status=pending/confirmed/rejected 过滤）"""
    return list_suggestions(db=db, status=status)


@router.post("/{suggestion_id}/confirm")
async def confirm_suggestion_endpoint(
    suggestion_id: int,
    request: Optional[SuggestionDecisionRequest] = None,
    current_user: User = Depends(require_dispatcher_with_idempotency),
    db: Session = Depends(get_db),
):
    """
    确认 AI 建议（应用建议）

    suggestion/action 级别：确认关联 draft 调度方案（F021 打包 + draft → active）
    info 级别：仅标记确认
    """
    note = (request.note if request else None) or ""
    return await confirm_suggestion(
        db=db,
        suggestion_id=suggestion_id,
        user=current_user,
        note=note,
    )


@router.post("/{suggestion_id}/reject")
async def reject_suggestion_endpoint(
    suggestion_id: int,
    request: Optional[SuggestionDecisionRequest] = None,
    current_user: User = Depends(require_dispatcher_with_idempotency),
    db: Session = Depends(get_db),
):
    """拒绝 AI 建议（仅记录审计，不触发任何调度修改）"""
    note = (request.note if request else None) or ""
    return reject_suggestion(
        db=db,
        suggestion_id=suggestion_id,
        user=current_user,
        note=note,
    )
