import asyncio

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from config.database import get_db, settings
from schemas.user import UserLoginRequest
from services.auth_service import (
    bump_token_version,
    create_access_token,
    verify_password,
)
from services.log_service import LogService, build_login_event_data
from api.dependencies import get_current_user
from core.error_codes import CODE_UNAUTHORIZED
from core.login_rate_limit import (
    get_login_rate_limiter,
    login_rate_limit_key,
)
from core.permissions import get_user_permissions
from models.user import User
from models.log_event import LogEvent

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
async def login(credentials: UserLoginRequest, request: Request, db: Session = Depends(get_db)):
    limiter = get_login_rate_limiter()
    client_ip = request.client.host if request.client else None
    rate_key = login_rate_limit_key(credentials.username, client_ip)
    limiter.check(rate_key)

    user = db.query(User).filter(User.username == credentials.username).first()
    password_ok = False
    if user is not None:
        password_ok = await asyncio.to_thread(
            verify_password,
            credentials.password,
            user.password_hash,
        )
    if not user or not password_ok or not user.is_active:
        limiter.record_failure(rate_key)
        return {
            "code": CODE_UNAUTHORIZED,
            "message": "用户名或密码错误",
            "data": None,
            "meta": limiter.public_meta(),
        }

    limiter.record_success(rate_key)
    access_token = create_access_token(
        username=user.username,
        role=user.role,
        token_version=int(user.token_version or 0),
    )

    user_agent = request.headers.get("user-agent")
    LogService.log_event(
        event_name="login",
        user_id=user.id,
        role=user.role,
        event_data=build_login_event_data(ip=client_ip, user_agent=user_agent),
        db=db
    )

    return {
        "code": 0,
        "message": "success",
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_EXPIRE_SECONDS,
            "role": user.role,
            "display_name": user.display_name,
        },
        "meta": limiter.public_meta(),
    }


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "code": 0,
        "message": "success",
        "data": {
            "username": current_user.username,
            "role": current_user.role,
            "display_name": current_user.display_name,
            "is_active": current_user.is_active,
            "permissions": get_user_permissions(current_user),
        },
        "meta": {"degraded": False, "degraded_reason": None},
    }


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    log_event = LogEvent(
        event_name="logout",
        user_id=current_user.id,
        role=current_user.role,
        event_data={"username": current_user.username},
    )
    db.add(log_event)
    bump_token_version(db, current_user, commit=True)

    return {
        "code": 0,
        "message": "登出成功",
        "data": None,
        "meta": {"degraded": False, "degraded_reason": None},
    }
