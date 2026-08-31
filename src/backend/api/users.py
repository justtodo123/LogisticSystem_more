from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.dependencies import require_permission
from config.database import get_db
from core.error_codes import CODE_NOT_FOUND, CODE_PARAM_ERROR
from core.errors import DomainError
from core.permissions import KNOWN_ROLES
from models.log_event import LogEvent
from models.user import User
from services.auth_service import get_user_by_username, update_user_security_state

router = APIRouter(prefix="/api/users", tags=["users"])


class UserSecurityUpdateRequest(BaseModel):
    role: Optional[str] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)


@router.patch("/{username}")
async def patch_user(
    username: str,
    body: UserSecurityUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("admin:users")),
):
    if body.role is None and body.is_active is None:
        raise DomainError(CODE_PARAM_ERROR)
    if body.role is not None and body.role not in KNOWN_ROLES:
        raise DomainError(CODE_PARAM_ERROR)

    target = get_user_by_username(db, username)
    if target is None:
        raise DomainError(CODE_NOT_FOUND)

    previous_role = target.role
    previous_active = target.is_active
    update_user_security_state(
        db,
        target,
        role=body.role,
        is_active=body.is_active,
        commit=False,
    )
    db.add(
        LogEvent(
            event_name="user_security_update",
            user_id=current_user.id,
            role=current_user.role,
            event_data={
                "target_username": target.username,
                "previous_role": previous_role,
                "new_role": target.role,
                "previous_is_active": previous_active,
                "new_is_active": target.is_active,
                "token_version": target.token_version,
            },
        )
    )
    db.commit()
    db.refresh(target)

    return {
        "code": 0,
        "message": "success",
        "data": {
            "username": target.username,
            "role": target.role,
            "is_active": target.is_active,
            "token_version": target.token_version,
        },
        "meta": {"degraded": False, "degraded_reason": None},
    }
