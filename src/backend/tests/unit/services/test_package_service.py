"""
PackageService 单元测试

测试包裹服务 (services/package_service.py) 的所有方法：
- get_packages: 获取包裹列表
- get_package: 获取包裹详情
- repack_package: 重新打包包裹
"""
import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from datetime import datetime
import json

from services.package_service import PackageService
from models.package import Package
from models.node import Node
from models.goods import Goods
from models.order import Order
from schemas.package import PackageRepack
from core.error_codes import (
    CODE_SUCCESS, CODE_INTERNAL_ERROR,
    CODE_PACKAGE_NOT_FOUND, CODE_PACKAGE_STATUS_NOT_ALLOWED,
    CODE_GOODS_NOT_FOUND, CODE_NODE_NOT_FOUND
)


@pytest.fixture
def mock_db():
    """Mock数据库会话"""
    db = MagicMock(spec=Session)
    return db


@pytest.fixture
def sample_package():
    """示例包裹"""
    package = MagicMock(spec=Package)
    package.id = 1
    package.package_code = "PKG1700000000000"
    package.weight = 15.0
    package.volume = 0.8
    package.status = "pending_pack"
    package.from_node_id = 1
    package.to_node_id = 2
    package.goods_items = json.dumps([
        {"goods_code": "G1700000000000_0", "order_code": "O1700000000000"}
    ])
    package.from_longitude = 114.3
    package.from_latitude = 30.5
    package.to_longitude = 114.4
    package.to_latitude = 30.6
    package.created_at = datetime.now()
    package.updated_at = datetime.now()
    return package


class TestPackageServiceGetPackages:
    """测试获取包裹列表"""

    @pytest.mark.asyncio
    async def test_get_packages_success(self, mock_db, sample_package):
        """测试成功获取包裹列表"""
        # 模拟数据库查询
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.offset.return_value.limit.return_value.all.return_value = [sample_package]
        
        # 模拟节点查询
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            MagicMock(node_code="SC001", name="存储中心1"),
            MagicMock(node_code="SO001", name="分拣中心1"),
        ]
        
        # 执行
        result = await PackageService.get_packages(1, 20, None, None, None, mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert "items" in result["data"]
        assert result["data"]["total"] == 1

    @pytest.mark.asyncio
    async def test_get_packages_with_status_filter(self, mock_db):
        """测试按状态筛选包裹"""
        # 模拟数据库查询
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.offset.return_value.limit.return_value.all.return_value = []
        
        # 执行
        result = await PackageService.get_packages(1, 20, "pending_pack", None, None, mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert result["data"]["total"] == 0


class TestPackageServiceGetPackage:
    """测试获取包裹详情"""

    @pytest.mark.asyncio
    async def test_get_package_success(self, mock_db, sample_package):
        """测试成功获取包裹详情"""
        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_package,  # 查询包裹
            MagicMock(node_code="SC001", name="存储中心1"),  # 查询from节点
            MagicMock(node_code="SO001", name="分拣中心1"),  # 查询to节点
        ]
        
        # 执行
        result = await PackageService.get_package("PKG1700000000000", mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert result["data"]["package_code"] == "PKG1700000000000"

    @pytest.mark.asyncio
    async def test_get_package_not_found(self, mock_db):
        """测试包裹不存在"""
        # 模拟数据库查询返回None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 执行
        result = await PackageService.get_package("INVALID", mock_db)
        
        # 验证
        assert result["code"] == CODE_PACKAGE_NOT_FOUND
        assert "包裹不存在" in result["message"]


class TestPackageServiceRepackPackage:
    """测试重新打包包裹"""

    @pytest.mark.asyncio
    async def test_repack_package_success(self, mock_db, sample_package):
        """测试成功重新打包包裹"""
        from unittest.mock import patch, MagicMock
        from datetime import datetime
        
        # Mock Package构造函数，避免created_at为None
        mock_new_pkg = MagicMock()
        mock_new_pkg.package_code = "PKG_NEW_001"
        mock_new_pkg.weight = 10.0
        mock_new_pkg.volume = 0.5
        mock_new_pkg.status = "pending_pack"
        mock_new_pkg.from_node_id = 1
        mock_new_pkg.to_node_id = 2
        mock_new_pkg.created_at = datetime(2026, 6, 15, 10, 0, 0)
        mock_new_pkg.updated_at = datetime(2026, 6, 15, 10, 0, 0)
        
        with patch('services.package_service.Package', return_value=mock_new_pkg):
            # 模拟数据库查询 - 需要7次first()调用
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                sample_package,  # 1. 查询原包裹
                MagicMock(goods_code="G1700000000000_0", order_id=1, node_id=1, status="pending_pack"),  # 2. 查询货物1
                MagicMock(order_code="O1700000000000"),  # 3. 查询订单(第一次，if判断)
                MagicMock(order_code="O1700000000000"),  # 4. 查询订单(第二次，获取order_code)
                MagicMock(goods_code="G1700000000000_0", weight=10.0, volume=0.5),  # 5. 查询货物(第二次for循环，第164行)
                MagicMock(node_code="SC001", name="存储中心1"),  # 6. 查询from节点(commit后)
                MagicMock(node_code="SO001", name="分拣中心1"),  # 7. 查询to节点(commit后)
            ]
        
            # 创建重新打包请求
            repack = PackageRepack(goods_codes=["G1700000000000_0"])
            
            # 执行
            result = await PackageService.repack_package("PKG1700000000000", repack, mock_db)
            
            # 验证
            assert result["code"] == CODE_SUCCESS
            assert "package_code" in result["data"]

    @pytest.mark.asyncio
    async def test_repack_package_not_found(self, mock_db):
        """测试包裹不存在"""
        # 模拟数据库查询返回None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 创建重新打包请求
        repack = PackageRepack(goods_codes=["G1700000000000_0"])
        
        # 执行
        result = await PackageService.repack_package("INVALID", repack, mock_db)
        
        # 验证
        assert result["code"] == CODE_PACKAGE_NOT_FOUND
        assert "包裹不存在" in result["message"]

    @pytest.mark.asyncio
    async def test_repack_package_status_not_allowed(self, mock_db, sample_package):
        """测试包裹状态不允许repack"""
        # 修改包裹状态为packed
        sample_package.status = "packed"
        mock_db.query.return_value.filter.return_value.first.return_value = sample_package
        
        # 创建重新打包请求
        repack = PackageRepack(goods_codes=["G1700000000000_0"])
        
        # 执行
        result = await PackageService.repack_package("PKG1700000000000", repack, mock_db)
        
        # 验证
        assert result["code"] == CODE_PACKAGE_STATUS_NOT_ALLOWED
        assert "不允许repack" in result["message"]

    @pytest.mark.asyncio
    async def test_repack_package_goods_not_belong(self, mock_db, sample_package):
        """测试货物不属于原包裹"""
        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_package,  # 查询原包裹
        ]
        
        # 创建重新打包请求（货物代码不在原包裹中）
        repack = PackageRepack(goods_codes=["G9999999999999_0"])
        
        # 执行
        result = await PackageService.repack_package("PKG1700000000000", repack, mock_db)
        
        # 验证
        assert result["code"] == CODE_PACKAGE_STATUS_NOT_ALLOWED
        assert "不属于原包裹" in result["message"]
