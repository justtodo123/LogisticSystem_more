from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from config.database import get_db
from schemas.user import UserLoginRequest, UserLoginResponse, UserResponse
from services.auth_service import (
    create_access_token,
    authenticate_user,
)
from api.dependencies import get_current_user
from models.user import User
from models.log_event import LogEvent

router = APIRouter(prefix="/api/auth", tags=["认证"])
security = HTTPBearer()


@router.post("/login")
async def login(credentials: UserLoginRequest, db: Session = Depends(get_db)):
    """登录接口"""
    user = authenticate_user(db, credentials.username, credentials.password)
    if not user:
        return {
            "code": 40100,
            "message": "用户名或密码错误",
            "data": None,
            "meta": {"degraded": False, "degraded_reason": None},
        }

    if not user.is_active:
        return {
            "code": 40100,
            "message": "账号未激活，请联系管理员",
            "data": None,
            "meta": {"degraded": False, "degraded_reason": None},
        }

    access_token = create_access_token(username=user.username, role=user.role)
    return {
        "code": 0,
        "message": "success",
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 86400,
            "role": user.role,
            "display_name": user.display_name,
        },
        "meta": {"degraded": False, "degraded_reason": None},
    }


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return {
        "code": 0,
        "message": "success",
        "data": {
            "username": current_user.username,
            "role": current_user.role,
            "display_name": current_user.display_name,
            "is_active": current_user.is_active,
        },
        "meta": {"degraded": False, "degraded_reason": None},
    }


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """登出接口"""
    # 记录登出日志
    log_event = LogEvent(
        event_name="logout",
        user_id=current_user.id,
        role=current_user.role,
        event_data={"username": current_user.username},
    )
    db.add(log_event)
    db.commit()

    return {
        "code": 0,
        "message": "登出成功",
        "data": None,
        "meta": {"degraded": False, "degraded_reason": None},
    }
