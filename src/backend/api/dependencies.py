from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from sqlalchemy.orm import Session

from config.database import settings
from config.database import get_db
from models.user import User
from services.auth_service import get_user_by_username


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


def require_dispatcher(current_user: User = Depends(get_current_user)) -> User:
    """检查当前用户角色是否为dispatcher，否则抛出 HTTPException(403)。

    由 main.py 全局异常处理器统一转为 {code, message, data, meta} 格式。
    """
    if current_user.role != "dispatcher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限执行此操作（仅调度员可操作）",
        )
    return current_user
