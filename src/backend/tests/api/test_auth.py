"""
API测试：认证模块（auth.py）

测试目标：
- POST /api/auth/login：登录接口
- GET /api/auth/me：获取当前用户信息
- POST /api/auth/logout：登出接口

验证内容：
- HTTP状态码
- 响应数据结构（code, message, data, meta）
- 业务逻辑正确性
"""
import pytest
from fastapi.testclient import TestClient
from models.user import User
from services.auth_service import get_password_hash


class TestLogin:
    """测试登录接口"""

    @pytest.mark.api
    def test_login_success(self, client, db_session):
        """测试成功登录"""
        # 创建测试用户
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        # 发送登录请求
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )

        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["message"] == "success"
        assert "data" in body
        assert "access_token" in body["data"]
        assert "role" in body["data"]
        assert body["data"]["role"] == "dispatcher"
        assert "expires_in" in body["data"]
        assert body["meta"]["degraded"] is False

    @pytest.mark.api
    def test_login_wrong_password(self, client, db_session):
        """测试错误密码登录"""
        # 创建测试用户
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        # 发送登录请求（错误密码）
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "wrong"},
        )

        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0  # 业务错误
        assert "密码" in body["message"] or "错误" in body["message"]

    @pytest.mark.api
    def test_login_user_not_found(self, client):
        """测试用户不存在"""
        response = client.post(
            "/api/auth/login",
            json={"username": "nonexist", "password": "123456"},
        )

        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
        assert "用户" in body["message"] or "不存在" in body["message"]

    @pytest.mark.api
    def test_login_missing_params(self, client):
        """测试缺少参数"""
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser"},  # 缺少password
        )

        # 验证响应（参数校验失败返回422，使用统一响应格式）
        assert response.status_code == 422
        body = response.json()
        assert "code" in body
        assert body["code"] == 40000
        assert "data" in body
        assert "detail" in body["data"]


class TestGetMe:
    """测试获取当前用户信息接口"""

    @pytest.mark.api
    def test_get_me_success(self, client, db_session):
        """测试成功获取用户信息"""
        # 创建测试用户
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 获取用户信息
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert "data" in body
        assert body["data"]["username"] == "testuser"
        assert body["data"]["role"] == "dispatcher"

    @pytest.mark.api
    def test_get_me_no_token(self, client):
        """测试未提供Token"""
        response = client.get("/api/auth/me")

        # 验证响应（FastAPI HTTPBearer返回401）
        assert response.status_code == 401
        body = response.json()
        assert body["code"] == 40100  # 未登录或Token无效


class TestLogout:
    """测试登出接口"""

    @pytest.mark.api
    def test_logout_success(self, client, db_session):
        """测试成功登出"""
        # 创建测试用户
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 登出
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert "success" in body["message"].lower() or "成功" in body["message"]
