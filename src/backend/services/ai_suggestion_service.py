"""
AI 建议确认闸门服务（T6-2）

职责：
1. 创建 AI 建议记录（parse 成功后由 api/ai.py 调用）
2. 列出/查询建议
3. confirm：对 suggestion/action 级别建议执行实际调度修改（draft → active，F021 打包），
   对 info 级别建议仅标记确认（无执行动作）
4. reject：仅记录拒绝（不触发任何调度修改）
5. 确认/拒绝均写入 log_events 审计

level 语义（对应 core/ai_guard.classify_suggestion_level）：
- info:       仅供展示，无需确认（explain/review/analyze）
- suggestion: 需调度员确认后应用（parse → draft 预览）
- action:     可自动执行（当前未启用，预留）
"""
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from core.ai_guard import SUGGESTION_STATUSES
from models.ai_suggestion import AiSuggestion
from services.log_service import (
    EVENT_AI_SUGGESTION_CONFIRM,
    EVENT_AI_SUGGESTION_REJECT,
    LogService,
    build_ai_suggestion_decision_event_data,
)
from utils.response import success_response, error_response

logger = logging.getLogger(__name__)


def _next_suggestion_code(db: Session) -> str:
    """生成 AI 建议编码 AISGxxx（按现有记录数递增）"""
    count = db.query(AiSuggestion).count()
    return f"AISG{count + 1:03d}"


def create_suggestion(
    db: Session,
    *,
    level: str,
    source: str,
    title: str,
    content: str,
    user_id: int,
    role: str,
    payload: Optional[Dict[str, Any]] = None,
    related_schedule_code: Optional[str] = None,
) -> AiSuggestion:
    """创建 AI 建议记录（pending 状态）"""
    suggestion = AiSuggestion(
        suggestion_code=_next_suggestion_code(db),
        level=level,
        source=source,
        title=title,
        content=content,
        payload=payload,
        related_schedule_code=related_schedule_code,
        status="pending",
        created_by_user_id=user_id,
        created_by_role=role,
    )
    db.add(suggestion)
    db.commit()
    db.refresh(suggestion)
    logger.info(
        f"AI 建议已创建：{suggestion.suggestion_code} level={level} source={source}"
    )
    return suggestion


def to_dict(s: AiSuggestion) -> Dict[str, Any]:
    """序列化为 API 响应 dict"""
    return {
        "id": s.id,
        "suggestion_code": s.suggestion_code,
        "level": s.level,
        "source": s.source,
        "title": s.title,
        "content": s.content,
        "payload": s.payload,
        "related_schedule_code": s.related_schedule_code,
        "status": s.status,
        "applied_schedule_code": s.applied_schedule_code,
        "created_by_user_id": s.created_by_user_id,
        "created_by_role": s.created_by_role,
        "decision_note": s.decision_note,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "decided_at": s.decided_at.isoformat() if s.decided_at else None,
    }


def list_suggestions(
    db: Session,
    status: Optional[str] = None,
    limit: int = 100,
) -> Dict[str, Any]:
    """列出 AI 建议（按创建时间倒序，可按状态过滤）"""
    query = db.query(AiSuggestion)
    if status:
        if status not in SUGGESTION_STATUSES:
            return error_response(
                code=40000,
                message=f"无效的状态: {status}（可选: {'/'.join(SUGGESTION_STATUSES)}）",
            )
        query = query.filter(AiSuggestion.status == status)
    suggestions = query.order_by(AiSuggestion.created_at.desc()).limit(limit).all()
    return success_response(data={
        "items": [to_dict(s) for s in suggestions],
        "total": len(suggestions),
    })


async def confirm_suggestion(
    db: Session,
    suggestion_id: int,
    user,
    note: str = "",
) -> Dict[str, Any]:
    """
    确认 AI 建议（确认闸门 → 应用）。

    - suggestion/action 级别 + source=parse：对 related_schedule_code 执行 confirm_schedule
      （F021 打包 + draft → active，即"应用建议"触发实际调度修改）
    - info 级别：仅标记确认，不执行任何调度修改
    - 已处理（confirmed/rejected）的建议不可重复确认
    """
    suggestion = db.query(AiSuggestion).filter(AiSuggestion.id == suggestion_id).first()
    if not suggestion:
        return error_response(code=40401, message=f"AI 建议不存在: {suggestion_id}")

    if suggestion.status != "pending":
        return error_response(
            code=40003,
            message=f"AI 建议已处理（当前状态: {suggestion.status}）",
        )

    applied_code = None
    if suggestion.level in ("suggestion", "action") and suggestion.related_schedule_code:
        # 应用建议 → 确认关联的 draft 调度方案（触发实际调度修改）
        from services.schedule_service import ScheduleService
        confirm_result = await ScheduleService.confirm_schedule(
            schedule_code=suggestion.related_schedule_code,
            db=db,
        )
        if confirm_result["code"] != 0:
            # 确认失败（如 draft 已被确认/丢弃）→ 建议保持 pending，返回错误
            return confirm_result
        applied_code = suggestion.related_schedule_code

    suggestion.status = "confirmed"
    suggestion.decided_at = datetime.now()
    suggestion.decision_note = note or None
    suggestion.applied_schedule_code = applied_code

    LogService.log_event(
        event_name=EVENT_AI_SUGGESTION_CONFIRM,
        user_id=user.id,
        role=user.role,
        event_data=build_ai_suggestion_decision_event_data(
            suggestion_code=suggestion.suggestion_code,
            level=suggestion.level,
            source=suggestion.source,
            related_schedule_code=suggestion.related_schedule_code,
            applied_schedule_code=applied_code,
        ),
        db=db,
    )

    db.commit()
    db.refresh(suggestion)
    logger.info(f"AI 建议已确认：{suggestion.suggestion_code} applied={applied_code}")

    return success_response(data={
        "suggestion": to_dict(suggestion),
        "applied_schedule_code": applied_code,
    })


def reject_suggestion(
    db: Session,
    suggestion_id: int,
    user,
    note: str = "",
) -> Dict[str, Any]:
    """拒绝 AI 建议（仅记录，不触发任何调度修改）"""
    suggestion = db.query(AiSuggestion).filter(AiSuggestion.id == suggestion_id).first()
    if not suggestion:
        return error_response(code=40401, message=f"AI 建议不存在: {suggestion_id}")

    if suggestion.status != "pending":
        return error_response(
            code=40003,
            message=f"AI 建议已处理（当前状态: {suggestion.status}）",
        )

    suggestion.status = "rejected"
    suggestion.decided_at = datetime.now()
    suggestion.decision_note = note or None

    LogService.log_event(
        event_name=EVENT_AI_SUGGESTION_REJECT,
        user_id=user.id,
        role=user.role,
        event_data=build_ai_suggestion_decision_event_data(
            suggestion_code=suggestion.suggestion_code,
            level=suggestion.level,
            source=suggestion.source,
            related_schedule_code=suggestion.related_schedule_code,
            note=note,
        ),
        db=db,
    )

    db.commit()
    db.refresh(suggestion)
    logger.info(f"AI 建议已拒绝：{suggestion.suggestion_code}")

    return success_response(data={"suggestion": to_dict(suggestion)})
