from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from sqlalchemy.orm import Session
from typing import List, Callable

from config.database import settings
from config.database import get_db
from models.user import User
from services.auth_service import get_user_by_username
from core.error_codes import CODE_IDEMPOTENCY_KEY_MISSING
from core.errors import DomainError
from core.permissions import get_user_permissions, PERMISSIONS
from middleware.idempotency import claim_idempotency

security = HTTPBearer()


async def get_current_user(
    request: Request,
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
        # 供审计中间件（middleware/audit_log.py）读取，记录操作者
        request.state.current_user = user
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


async def get_current_user_with_optional_idempotency(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> User:
    """Claim a supplied key after active-user authentication."""
    await claim_idempotency(
        request,
        f"user:{current_user.username}",
        settings.IDEMPOTENCY_PROCESSING_LEASE_SECONDS,
    )
    return current_user


async def require_dispatcher_with_optional_idempotency(
    request: Request,
    current_user: User = Depends(require_dispatcher),
) -> User:
    """Claim a supplied key after dispatcher authorization."""
    await claim_idempotency(
        request,
        f"user:{current_user.username}",
        settings.IDEMPOTENCY_PROCESSING_LEASE_SECONDS,
    )
    return current_user

async def require_dispatcher_with_idempotency(
    request: Request,
    current_user: User = Depends(require_dispatcher),
) -> User:
    """Require and claim a durable key after dispatcher authorization."""
    if not request.headers.get("X-Idempotency-Key"):
        raise DomainError(CODE_IDEMPOTENCY_KEY_MISSING)
    await claim_idempotency(
        request,
        f"user:{current_user.username}",
        settings.IDEMPOTENCY_PROCESSING_LEASE_SECONDS,
    )
    return current_user
