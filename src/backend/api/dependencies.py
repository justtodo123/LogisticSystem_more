from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from sqlalchemy.orm import Session
from typing import Callable

from config.database import settings
from config.database import get_db
from models.user import User
from services.auth_service import get_user_by_username
from core.error_codes import (
    CODE_FORBIDDEN,
    CODE_IDEMPOTENCY_KEY_MISSING,
    CODE_TOKEN_EXPIRED,
    CODE_UNAUTHORIZED,
)
from core.errors import DomainError
from core.permissions import user_has_permission
from core.request_context import update_request_context
from middleware.idempotency import claim_idempotency

security = HTTPBearer()


def _token_version_from_payload(payload: dict) -> int:
    raw = payload.get("tv", 0)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Decode the bearer token and load an active user with a matching token_version."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        username = payload.get("sub")
        if username is None:
            raise DomainError(CODE_UNAUTHORIZED)
        user = get_user_by_username(db, username)
        if user is None or not user.is_active:
            raise DomainError(CODE_UNAUTHORIZED)
        if _token_version_from_payload(payload) != int(user.token_version or 0):
            raise DomainError(CODE_UNAUTHORIZED)
        request.state.current_user = user
        update_request_context(user_id=str(user.id), role=str(user.role or ""))
        return user
    except DomainError:
        raise
    except jwt.ExpiredSignatureError:
        raise DomainError(CODE_TOKEN_EXPIRED)
    except jwt.InvalidTokenError:
        raise DomainError(CODE_UNAUTHORIZED)


def require_role(*roles: str) -> Callable:
    async def _require_role(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in roles:
            raise DomainError(CODE_FORBIDDEN)
        return current_user
    return _require_role


def require_permission(permission: str) -> Callable:
    async def _require_permission(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if not user_has_permission(current_user, permission):
            raise DomainError(CODE_FORBIDDEN)
        return current_user
    return _require_permission


def require_dispatcher(current_user: User = Depends(get_current_user)) -> User:
    """Backward-compatible dispatcher/admin check; new routes should use require_permission."""
    if current_user.role not in ("dispatcher", "admin"):
        raise DomainError(CODE_FORBIDDEN)
    return current_user


def require_permission_with_optional_idempotency(permission: str) -> Callable:
    async def _require_permission_with_optional_idempotency(
        request: Request,
        current_user: User = Depends(require_permission(permission)),
    ) -> User:
        await claim_idempotency(
            request,
            f"user:{current_user.username}",
            settings.IDEMPOTENCY_PROCESSING_LEASE_SECONDS,
        )
        return current_user
    return _require_permission_with_optional_idempotency


def require_permission_with_idempotency(permission: str) -> Callable:
    async def _require_permission_with_idempotency(
        request: Request,
        current_user: User = Depends(require_permission(permission)),
    ) -> User:
        if not request.headers.get("X-Idempotency-Key"):
            raise DomainError(CODE_IDEMPOTENCY_KEY_MISSING)
        await claim_idempotency(
            request,
            f"user:{current_user.username}",
            settings.IDEMPOTENCY_PROCESSING_LEASE_SECONDS,
        )
        return current_user
    return _require_permission_with_idempotency


async def get_current_user_with_optional_idempotency(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> User:
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
    if not request.headers.get("X-Idempotency-Key"):
        raise DomainError(CODE_IDEMPOTENCY_KEY_MISSING)
    await claim_idempotency(
        request,
        f"user:{current_user.username}",
        settings.IDEMPOTENCY_PROCESSING_LEASE_SECONDS,
    )
    return current_user
