"""
API测试固件（API Test Fixtures）

API测试特点：
- 使用 FastAPI TestClient 或 httpx.AsyncClient
- 覆盖数据库依赖
- 提供认证 Token
"""
import pytest
import jwt
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base


@pytest.fixture(scope="function")
def client(test_db):
    """创建 FastAPI TestClient，覆盖数据库依赖"""
    from main import app
    from config.database import get_db
    
    engine, TestingSessionLocal = test_db
    
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def async_client(test_db):
    """创建 httpx.AsyncClient（用于异步测试）"""
    from main import app
    from config.database import get_db
    from httpx import ASGITransport, AsyncClient
    
    engine, TestingSessionLocal = test_db
    
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async_client = AsyncClient(transport=transport, base_url="http://test")
    
    yield async_client
    
    app.dependency_overrides.clear()


def create_jwt_token(username, role):
    """生成 JWT Token"""
    from config.database import settings
    
    return jwt.encode(
        {
            "sub": username,
            "role": role,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
        settings.JWT_SECRET,
        algorithm="HS256",
    )


@pytest.fixture(scope="function")
def dispatcher_token():
    """dispatcher 角色 Token"""
    return create_jwt_token("dispatcher", "dispatcher")


@pytest.fixture(scope="function")
def manager_token():
    """manager 角色 Token"""
    return create_jwt_token("manager", "manager")
