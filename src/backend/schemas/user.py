from pydantic import BaseModel


class UserLoginRequest(BaseModel):
    """登录请求模型"""
    username: str
    password: str


class UserLoginResponse(BaseModel):
    """登录响应模型"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    role: str
    display_name: str


class UserResponse(BaseModel):
    """用户响应模型"""
    username: str
    role: str
    display_name: str | None = None
    is_active: bool = True
    permissions: list[str] = []

    class Config:
        from_attributes = True
