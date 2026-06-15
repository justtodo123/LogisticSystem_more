"""
DriverService 单元测试

测试司机服务 (services/driver_service.py) 的所有方法：
- create_driver: 创建司机
- get_drivers: 获取司机列表
- get_driver: 获取司机详情
- update_driver: 更新司机
- delete_driver: 删除司机
"""
import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from datetime import datetime

from services.driver_service import DriverService
from models.driver import Driver
from models.node import Node
from schemas.driver import DriverCreate, DriverUpdate
from core.error_codes import (
    CODE_SUCCESS, CODE_INTERNAL_ERROR, CODE_CONFLICT,
    CODE_NODE_NOT_FOUND, CODE_DRIVER_NOT_FOUND,
    CODE_DRIVER_STATUS_NOT_ALLOWED
)


@pytest.fixture
def mock_db():
    """Mock数据库会话"""
    db = MagicMock(spec=Session)
    return db


@pytest.fixture
def sample_node():
    """示例节点"""
    node = MagicMock(spec=Node)
    node.id = 1
    node.node_code = "SC001"
    node.name = "测试存储中心"
    return node


@pytest.fixture
def sample_driver():
    """示例司机"""
    driver = MagicMock(spec=Driver)
    driver.id = 1
    driver.driver_code = "D1700000000000"
    driver.name = "测试司机"
    driver.phone = "13800138000"
    driver.license_type = "C1"
    driver.shift = "day"
    driver.node_id = 1
    driver.status = "idle"
    driver.created_at = datetime.now()
    driver.updated_at = datetime.now()
    return driver


class TestDriverServiceCreateDriver:
    """测试创建司机"""

    @pytest.mark.asyncio
    async def test_create_driver_success(self, mock_db, sample_node):
        """测试成功创建司机"""
        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,  # 司机编号不存在
            sample_node,  # 节点存在
        ]
        
        # 创建请求数据
        driver_create = DriverCreate(
            driver_code="D1700000000000",
            name="测试司机",
            phone="13800138000",
            license_type="C1",
            node_code="SC001"
        )
        
        # 执行
        result = await DriverService.create_driver(driver_create, mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert result["message"] == "success"
        assert result["data"]["driver_code"] == "D1700000000000"

    @pytest.mark.asyncio
    async def test_create_driver_code_exists(self, mock_db, sample_driver):
        """测试司机编号已存在"""
        # 模拟数据库查询返回已存在的司机
        mock_db.query.return_value.filter.return_value.first.return_value = sample_driver
        
        # 创建请求数据
        driver_create = DriverCreate(
            driver_code="D1700000000000",
            name="测试司机",
            phone="13800138000",
            license_type="C1",
            node_code="SC001"
        )
        
        # 执行
        result = await DriverService.create_driver(driver_create, mock_db)
        
        # 验证
        assert result["code"] == CODE_CONFLICT
        assert "司机编号已存在" in result["message"]

    @pytest.mark.asyncio
    async def test_create_driver_node_not_found(self, mock_db):
        """测试节点不存在"""
        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,  # 司机编号不存在
            None,  # 节点不存在
        ]
        
        # 创建请求数据
        driver_create = DriverCreate(
            driver_code="D1700000000000",
            name="测试司机",
            phone="13800138000",
            license_type="C1",
            node_code="INVALID"
        )
        
        # 执行
        result = await DriverService.create_driver(driver_create, mock_db)
        
        # 验证
        assert result["code"] == CODE_NODE_NOT_FOUND
        assert "节点不存在" in result["message"]


class TestDriverServiceGetDrivers:
    """测试获取司机列表"""

    @pytest.mark.asyncio
    async def test_get_drivers_success(self, mock_db, sample_driver):
        """测试成功获取司机列表"""
        # 模拟数据库查询
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.offset.return_value.limit.return_value.all.return_value = [sample_driver]
        
        # 模拟节点查询
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock(
            node_code="SC001", name="存储中心1"
        )
        
        # 执行
        result = await DriverService.get_drivers(1, 20, None, None, mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert "items" in result["data"]
        assert result["data"]["total"] == 1


class TestDriverServiceGetDriver:
    """测试获取司机详情"""

    @pytest.mark.asyncio
    async def test_get_driver_success(self, mock_db, sample_driver):
        """测试成功获取司机详情"""
        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.return_value = sample_driver
        
        # 模拟节点查询
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock(
            node_code="SC001", name="存储中心1"
        )
        
        # 执行
        result = await DriverService.get_driver("D1700000000000", mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert result["data"]["driver_code"] == "D1700000000000"

    @pytest.mark.asyncio
    async def test_get_driver_not_found(self, mock_db):
        """测试司机不存在"""
        # 模拟数据库查询返回None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 执行
        result = await DriverService.get_driver("INVALID", mock_db)
        
        # 验证
        assert result["code"] == CODE_DRIVER_NOT_FOUND
        assert "司机不存在" in result["message"]


class TestDriverServiceUpdateDriver:
    """测试更新司机"""

    @pytest.mark.asyncio
    async def test_update_driver_success(self, mock_db, sample_driver):
        """测试成功更新司机"""
        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_driver,  # 查询司机
            MagicMock(node_code="SC002", name="新节点"),  # 查询新节点
        ]
        
        # 创建更新数据
        driver_update = DriverUpdate(name="更新后的司机")
        
        # 执行
        result = await DriverService.update_driver("D1700000000000", driver_update, mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert result["data"]["name"] == "更新后的司机"

    @pytest.mark.asyncio
    async def test_update_driver_not_found(self, mock_db):
        """测试司机不存在"""
        # 模拟数据库查询返回None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 创建更新数据
        driver_update = DriverUpdate(name="更新后的司机")
        
        # 执行
        result = await DriverService.update_driver("INVALID", driver_update, mock_db)
        
        # 验证
        assert result["code"] == CODE_DRIVER_NOT_FOUND
        assert "司机不存在" in result["message"]


class TestDriverServiceDeleteDriver:
    """测试删除司机"""

    @pytest.mark.asyncio
    async def test_delete_driver_success(self, mock_db, sample_driver):
        """测试成功删除司机"""
        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.return_value = sample_driver
        
        # 执行
        result = await DriverService.delete_driver("D1700000000000", mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert result["message"] == "success"

    @pytest.mark.asyncio
    async def test_delete_driver_not_found(self, mock_db):
        """测试司机不存在"""
        # 模拟数据库查询返回None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 执行
        result = await DriverService.delete_driver("INVALID", mock_db)
        
        # 验证
        assert result["code"] == CODE_DRIVER_NOT_FOUND
        assert "司机不存在" in result["message"]

    @pytest.mark.asyncio
    async def test_delete_driver_status_not_allowed(self, mock_db, sample_driver):
        """测试司机有未完成订单不可删除"""
        # 修改司机状态为busy
        sample_driver.status = "busy"
        mock_db.query.return_value.filter.return_value.first.return_value = sample_driver
        
        # 执行
        result = await DriverService.delete_driver("D1700000000000", mock_db)
        
        # 验证
        assert result["code"] == CODE_DRIVER_STATUS_NOT_ALLOWED
        assert "不可删除" in result["message"]
