"""
NodeService 单元测试

测试节点服务 (services/node_service.py) 的所有方法：
- create_storage_center: 创建存储中心
- update_storage_center: 更新存储中心
- delete_storage_center: 删除存储中心
- create_sorting_center: 创建分拣中心
- update_sorting_center: 更新分拣中心
- delete_sorting_center: 删除分拣中心
- get_nodes: 获取节点列表
- get_node: 获取节点详情
"""
import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from datetime import datetime

from services.node_service import NodeService
from models.node import Node
from models.storage_center import StorageCenter
from models.sorting_center import SortingCenter
from core.error_codes import (
    CODE_SUCCESS, CODE_INTERNAL_ERROR, CODE_CONFLICT,
    CODE_NODE_NOT_FOUND, CODE_STORAGE_CENTER_NOT_FOUND,
    CODE_SORTING_CENTER_NOT_FOUND
)


@pytest.fixture
def mock_db():
    """Mock数据库会话"""
    db = MagicMock(spec=Session)
    return db


@pytest.fixture
def sample_storage_center_data():
    """示例存储中心创建数据"""
    return {
        "node_code": "SC001",
        "name": "测试存储中心",
        "location": "测试位置",
        "latitude": 30.5,
        "longitude": 114.3,
        "capacity": 10000.0,
        "inventory": 0
    }


@pytest.fixture
def sample_sorting_center_data():
    """示例分拣中心创建数据"""
    return {
        "node_code": "SO001",
        "name": "测试0级分拣中心",
        "location": "测试位置",
        "latitude": 30.6,
        "longitude": 114.4,
        "level": 0,
        "capacity": 5000.0,
        "max_storage_time": 24
    }


@pytest.fixture
def sample_node():
    """示例节点"""
    node = MagicMock(spec=Node)
    node.id = 1
    node.node_code = "SC001"
    node.name = "测试存储中心"
    node.location = "测试位置"
    node.latitude = 30.5
    node.longitude = 114.3
    node.node_type = "storage_center"
    node.created_at = datetime.now()
    node.updated_at = datetime.now()
    return node


class TestNodeServiceCreateStorageCenter:
    """测试创建存储中心"""

    def test_create_storage_center_success(self, mock_db, sample_storage_center_data):
        """测试成功创建存储中心"""
        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.return_value = None  # node_code不存在
        
        # 执行
        result = await NodeService.create_storage_center(sample_storage_center_data, mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert result["message"] == "success"
        assert result["data"]["node_code"] == "SC001"

    def test_create_storage_center_code_exists(self, mock_db, sample_storage_center_data, sample_node):
        """测试存储中心编号已存在"""
        # 模拟数据库查询返回已存在的节点
        mock_db.query.return_value.filter.return_value.first.return_value = sample_node
        
        # 执行
        result = await NodeService.create_storage_center(sample_storage_center_data, mock_db)
        
        # 验证
        assert result["code"] == CODE_CONFLICT
        assert "编号已存在" in result["message"]


class TestNodeServiceUpdateStorageCenter:
    """测试更新存储中心"""

    def test_update_storage_center_success(self, mock_db, sample_node):
        """测试成功更新存储中心"""
        # 模拟数据库查询
        storage_center = MagicMock(spec=StorageCenter)
        storage_center.capacity = 10000.0
        storage_center.inventory = 0
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_node,  # 查询节点
            storage_center,  # 查询storage_center
        ]
        
        # 执行
        result = await NodeService.update_storage_center("SC001", {"name": "更新后的名称"}, mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert result["data"]["name"] == "更新后的名称"

    def test_update_storage_center_not_found(self, mock_db):
        """测试存储中心不存在"""
        # 模拟数据库查询返回None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 执行
        result = await NodeService.update_storage_center("INVALID", {"name": "更新后的名称"}, mock_db)
        
        # 验证
        assert result["code"] == CODE_NODE_NOT_FOUND
        assert "存储中心不存在" in result["message"]


class TestNodeServiceDeleteStorageCenter:
    """测试删除存储中心"""

    def test_delete_storage_center_success(self, mock_db, sample_node):
        """测试成功删除存储中心"""
        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.return_value = sample_node
        
        # 执行
        result = await NodeService.delete_storage_center("SC001", mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert result["message"] == "success"

    def test_delete_storage_center_not_found(self, mock_db):
        """测试存储中心不存在"""
        # 模拟数据库查询返回None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 执行
        result = await NodeService.delete_storage_center("INVALID", mock_db)
        
        # 验证
        assert result["code"] == CODE_NODE_NOT_FOUND
        assert "存储中心不存在" in result["message"]


class TestNodeServiceCreateSortingCenter:
    """测试创建分拣中心"""

    def test_create_sorting_center_success(self, mock_db, sample_sorting_center_data):
        """测试成功创建分拣中心"""
        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.return_value = None  # node_code不存在
        
        # 执行
        result = await NodeService.create_sorting_center(sample_sorting_center_data, mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert result["message"] == "success"
        assert result["data"]["node_code"] == "SO001"

    def test_create_sorting_center_code_exists(self, mock_db, sample_sorting_center_data):
        """测试分拣中心编号已存在"""
        # 模拟数据库查询返回已存在的节点
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()
        
        # 执行
        result = await NodeService.create_sorting_center(sample_sorting_center_data, mock_db)
        
        # 验证
        assert result["code"] == CODE_CONFLICT
        assert "编号已存在" in result["message"]


class TestNodeServiceUpdateSortingCenter:
    """测试更新分拣中心"""

    def test_update_sorting_center_success(self, mock_db):
        """测试成功更新分拣中心"""
        # 模拟数据库查询
        node = MagicMock(spec=Node)
        node.node_code = "SO001"
        node.name = "测试分拣中心"
        node.location = "测试位置"
        node.latitude = 30.6
        node.longitude = 114.4
        node.node_type = "sorting_center"
        
        sorting_center = MagicMock(spec=SortingCenter)
        sorting_center.level = 0
        sorting_center.capacity = 5000.0
        sorting_center.max_storage_time = 24
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            node,  # 查询节点
            sorting_center,  # 查询sorting_center
        ]
        
        # 执行
        result = await NodeService.update_sorting_center("SO001", {"name": "更新后的名称"}, mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert result["data"]["name"] == "更新后的名称"

    def test_update_sorting_center_not_found(self, mock_db):
        """测试分拣中心不存在"""
        # 模拟数据库查询返回None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 执行
        result = await NodeService.update_sorting_center("INVALID", {"name": "更新后的名称"}, mock_db)
        
        # 验证
        assert result["code"] == CODE_NODE_NOT_FOUND
        assert "分拣中心不存在" in result["message"]


class TestNodeServiceDeleteSortingCenter:
    """测试删除分拣中心"""

    def test_delete_sorting_center_success(self, mock_db):
        """测试成功删除分拣中心"""
        # 模拟数据库查询
        node = MagicMock(spec=Node)
        mock_db.query.return_value.filter.return_value.first.return_value = node
        
        # 执行
        result = await NodeService.delete_sorting_center("SO001", mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert result["message"] == "success"

    def test_delete_sorting_center_not_found(self, mock_db):
        """测试分拣中心不存在"""
        # 模拟数据库查询返回None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 执行
        result = await NodeService.delete_sorting_center("INVALID", mock_db)
        
        # 验证
        assert result["code"] == CODE_NODE_NOT_FOUND
        assert "分拣中心不存在" in result["message"]


class TestNodeServiceGetNodes:
    """测试获取节点列表"""

    def test_get_nodes_success(self, mock_db, sample_node):
        """测试成功获取节点列表"""
        # 模拟数据库查询
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.offset.return_value.limit.return_value.all.return_value = [sample_node]
        
        # 模拟storage_center查询
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock(
            capacity=10000.0, inventory=0
        )
        
        # 执行
        result = await NodeService.get_nodes(1, 20, None, None, mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert "items" in result["data"]
        assert result["data"]["total"] == 1

    def test_get_nodes_with_type_filter(self, mock_db):
        """测试按节点类型筛选"""
        # 模拟数据库查询
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.offset.return_value.limit.return_value.all.return_value = []
        
        # 执行
        result = await NodeService.get_nodes(1, 20, "storage_center", None, mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert result["data"]["total"] == 0


class TestNodeServiceGetNode:
    """测试获取节点详情"""

    def test_get_node_success(self, mock_db, sample_node):
        """测试成功获取节点详情"""
        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.return_value = sample_node
        
        # 模拟storage_center查询
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            MagicMock(capacity=10000.0, inventory=0),  # storage_center
            None,  # sorting_center
        ]
        
        # 执行
        result = await NodeService.get_node("SC001", mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert result["data"]["node_code"] == "SC001"

    def test_get_node_not_found(self, mock_db):
        """测试节点不存在"""
        # 模拟数据库查询返回None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 执行
        result = await NodeService.get_node("INVALID", mock_db)
        
        # 验证
        assert result["code"] == CODE_NODE_NOT_FOUND
        assert "节点不存在" in result["message"]
