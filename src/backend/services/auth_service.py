from datetime import datetime, timedelta
from typing import Optional
import jwt
import bcrypt
from sqlalchemy.orm import Session

from config.database import settings
from models.user import User


def create_access_token(
    username: str,
    role: str,
    token_version: int = 0,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Issue a JWT access token carrying the current token_version."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(seconds=settings.JWT_EXPIRE_SECONDS)
    to_encode = {
        "sub": username,
        "role": role,
        "tv": int(token_version or 0),
        "exp": expire,
    }
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm="HS256")
    return encoded_jwt


def decode_token(token: str) -> dict:
    """解码Token"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise ValueError("Invalid token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def get_password_hash(password: str) -> str:
    """密码哈希"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """验证用户登录"""
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def get_user_by_username(db: Session, username: str) -> User | None:
    """根据用户名获取用户"""
    return db.query(User).filter(User.username == username).first()


def bump_token_version(db: Session, user: User, *, commit: bool = True) -> User:
    """Atomically increment token_version so previously issued access tokens fail closed."""
    db.query(User).filter(User.id == user.id).update(
        {User.token_version: User.token_version + 1},
        synchronize_session="fetch",
    )
    if commit:
        db.commit()
    db.refresh(user)
    return user


def update_user_security_state(
    db: Session,
    user: User,
    *,
    role: str | None = None,
    is_active: bool | None = None,
    commit: bool = True,
) -> User:
    """Change role/active flag and revoke outstanding tokens in one transaction."""
    if role is not None:
        user.role = role
    if is_active is not None:
        user.is_active = is_active
    return bump_token_version(db, user, commit=commit)
