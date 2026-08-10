from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from sqlalchemy.orm import Session
from typing import List, Callable

from config.database import settings
from config.database import get_db
from models.user import User
from services.auth_service import get_user_by_username
from core.permissions import get_user_permissions, PERMISSIONS

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """从Authorization header中提取Token，解码后返回当前用户ORM对象。

    Token 无效/过期时抛出 HTTPException(401)，
    由 main.py 全局异常处理器统一转为 {code, message, data, meta} 格式。
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="未登录或 Token 无效")
        user = get_user_by_username(db, username)
        if user is None or not user.is_active:
            raise HTTPException(status_code=401, detail="未登录或 Token 无效")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已过期，请重新登录")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="未登录或 Token 无效")


def require_role(*roles: str) -> Callable:
    """要求用户拥有指定角色之一（工厂函数）

    Usage:
        current_user: User = Depends(require_role("admin", "dispatcher"))
    """
    async def _require_role(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要以下角色之一: {', '.join(roles)}",
            )
        return current_user
    return _require_role


def require_permission(permission: str) -> Callable:
    """要求用户拥有指定权限位（工厂函数）

    Usage:
        current_user: User = Depends(require_permission("orders:write"))
    """
    async def _require_permission(
        current_user: User = Depends(get_current_user),
    ) -> User:
        user_perms = get_user_permissions(current_user)
        if permission not in user_perms:
            perm_desc = PERMISSIONS.get(permission, permission)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少权限: {perm_desc}",
            )
        return current_user
    return _require_permission


def require_dispatcher(current_user: User = Depends(get_current_user)) -> User:
    """检查当前用户角色是否为dispatcher（向后兼容包装）

    内部调用 require_role，保留原函数名以兼容已有 API 端点。
    """
    if current_user.role != "dispatcher" and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限执行此操作（仅调度员可操作）",
        )
    return current_user
