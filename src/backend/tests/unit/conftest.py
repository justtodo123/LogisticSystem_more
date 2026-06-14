"""
单元测试固件（Unit Test Fixtures）

单元测试特点：
- 不依赖外部资源（数据库、网络）
- 使用 mock 隔离依赖
- 快速运行
"""
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture(scope="function")
def mock_db_session():
    """模拟数据库会话"""
    session = MagicMock()
    return session


@pytest.fixture(scope="function")
def mock_redis():
    """模拟Redis连接"""
    redis_mock = MagicMock()
    return redis_mock
