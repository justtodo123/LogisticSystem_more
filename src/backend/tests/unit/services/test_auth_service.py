"""
服务单元测试：AuthService（认证服务）

测试目标：
- AuthService.authenticate_user 方法的正常流程和异常流程
- 验证密码哈希、Token生成、用户认证逻辑
"""
import pytest
from datetime import datetime, timedelta, timezone
from jwt.exceptions import PyJWTError

from services.auth_service import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_token,
    authenticate_user,
    get_user_by_username,
)
from models.user import User


class TestGetPasswordHash:
    """测试密码哈希"""

    @pytest.mark.unit
    def test_get_password_hash(self):
        """测试密码哈希生成"""
        password = "123456"
        hashed = get_password_hash(password)
        
        # 验证哈希值不为空
        assert hashed is not None
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        
        # 验证哈希值可以用于验证密码
        assert verify_password(password, hashed) is True
        assert verify_password("wrong", hashed) is False


class TestVerifyPassword:
    """测试密码验证"""

    @pytest.mark.unit
    def test_verify_password_correct(self):
        """测试正确密码验证"""
        password = "123456"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True

    @pytest.mark.unit
    def test_verify_password_wrong(self):
        """测试错误密码验证"""
        password = "123456"
        hashed = get_password_hash(password)
        
        assert verify_password("wrong", hashed) is False


class TestCreateAccessToken:
    """测试Token生成"""

    @pytest.mark.unit
    def test_create_access_token(self, db_session):
        """测试Token生成"""
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
        
        # 生成Token
        token = create_access_token(
            username=user.username,
            role=user.role,
        )
        
        # 验证Token不为空
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # 验证Token可以解码
        decoded = decode_token(token)
        assert decoded["sub"] == "testuser"
        assert decoded["role"] == "dispatcher"

    @pytest.mark.unit
    def test_create_access_token_expired(self, db_session):
        """测试过期Token"""
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
        
        # 生成过期Token（过期时间为过去）
        token = create_access_token(
            username=user.username,
            role=user.role,
        )
        
        # 验证Token解码会失败
        with pytest.raises(PyJWTError):
            decode_token(token)


class TestAuthenticateUser:
    """测试用户认证"""

    @pytest.mark.unit
    def test_authenticate_user_success(self, db_session):
        """测试成功认证"""
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
        
        # 认证用户
        authenticated_user = authenticate_user("testuser", "123456", db_session)
        
        # 验证认证成功
        assert authenticated_user is not None
        assert authenticated_user.username == "testuser"
        assert authenticated_user.role == "dispatcher"

    @pytest.mark.unit
    def test_authenticate_user_wrong_password(self, db_session):
        """测试错误密码认证"""
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
        
        # 认证用户（错误密码）
        authenticated_user = authenticate_user("testuser", "wrong", db_session)
        
        # 验证认证失败
        assert authenticated_user is None

    @pytest.mark.unit
    def test_authenticate_user_not_found(self, db_session):
        """测试用户不存在"""
        # 认证用户（不存在的用户）
        authenticated_user = authenticate_user("nonexist", "123456", db_session)
        
        # 验证认证失败
        assert authenticated_user is None


class TestGetUserByUsername:
    """测试根据用户名获取用户"""

    @pytest.mark.unit
    def test_get_user_by_username_success(self, db_session):
        """测试成功获取用户"""
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
        
        # 获取用户
        found_user = get_user_by_username("testuser", db_session)
        
        # 验证获取成功
        assert found_user is not None
        assert found_user.username == "testuser"
        assert found_user.role == "dispatcher"

    @pytest.mark.unit
    def test_get_user_by_username_not_found(self, db_session):
        """测试用户不存在"""
        # 获取用户（不存在的用户）
        found_user = get_user_by_username("nonexist", db_session)
        
        # 验证获取失败
        assert found_user is None
