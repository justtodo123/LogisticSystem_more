"""
OrderService 单元测试

测试订单服务 (services/order_service.py) 的所有方法：
- create_order: 创建订单
- get_orders: 获取订单列表
- get_order: 获取订单详情
- update_order: 更新订单
- delete_order: 删除订单
- import_orders: 批量导入订单
"""
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from datetime import datetime

from services.order_service import OrderService
from models.order import Order
from models.goods import Goods
from models.node import Node
from models.sorting_center import SortingCenter
from schemas.order import OrderCreate, OrderUpdate, GoodsCreate
from core.error_codes import (
    CODE_SUCCESS, CODE_PARAM_ERROR, CODE_INTERNAL_ERROR,
    CODE_ORDER_NOT_FOUND, CODE_ORDER_STATUS_NOT_ALLOWED, CODE_NODE_NOT_FOUND
)


@pytest.fixture
def mock_db():
    """Mock数据库会话"""
    db = MagicMock(spec=Session)
    return db


@pytest.fixture
def sample_node():
    """示例节点（0级分拣中心）"""
    node = MagicMock(spec=Node)
    node.id = 1
    node.node_code = "SO001"
    node.name = "测试0级分拣中心"
    node.node_type = "sorting_center"
    return node


@pytest.fixture
def sample_storage_center():
    """示例存储中心"""
    node = MagicMock(spec=Node)
    node.id = 2
    node.node_code = "SC001"
    node.name = "测试存储中心"
    node.node_type = "storage_center"
    return node


@pytest.fixture
def sample_order():
    """示例订单"""
    order = MagicMock(spec=Order)
    order.id = 1
    order.order_code = "O1700000000000"
    order.destination_node_id = 1
    order.time_window = "2026-06-15 10:00-12:00"
    order.status = "pending"
    order.created_at = datetime.now()
    order.updated_at = datetime.now()
    return order


class TestOrderServiceCreateOrder:
    """测试创建订单"""

    @patch('services.order_service.Order')
    @patch('services.order_service.random')
    @patch('time.time')
    @pytest.mark.asyncio
    async def test_create_order_success(self, mock_time, mock_random, mock_order_class, mock_db, sample_node, sample_storage_center):
        """测试成功创建订单"""
        # 配置mock
        mock_time.time.return_value = 1700000000.0
        mock_random.choice.return_value = sample_storage_center
        
        # 配置mock Order类
        mock_order = MagicMock()
        mock_order.order_code = "O1700000000000"
        mock_order.destination_node_id = sample_node.id
        mock_order.status = "pending"
        mock_order.created_at = datetime(2026, 6, 15, 10, 0, 0)
        mock_order.updated_at = datetime(2026, 6, 15, 10, 0, 0)
        mock_order.id = 1
        mock_order_class.return_value = mock_order
        
        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_node,  # 查询目的地节点
            MagicMock(spec=SortingCenter, level=0),  # 查询sorting_center（第一次，校验level=0）
            sample_storage_center,  # 查询存储中心（未指定storage_center_code时随机分配）
        ]
        
        # 创建请求数据
        order_create = OrderCreate(
            destination_node_code="SO001",
            time_window="2026-06-15 10:00-12:00",
            goods=[
                GoodsCreate(goods_name="测试货物", goods_type="electronics", weight=10.0, volume=0.5)
            ]
        )
        
        # 执行
        result = await OrderService.create_order(order_create, mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert result["message"] == "success"
        assert "order_code" in result["data"]
        assert result["data"]["destination_node_code"] == "SO001"
        assert result["data"]["status"] == "pending"

    @pytest.mark.asyncio
    async def test_create_order_destination_not_found(self, mock_db):
        """测试目的地节点不存在"""
        # 模拟数据库查询返回None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 创建请求数据
        order_create = OrderCreate(
            destination_node_code="INVALID",
            time_window="2026-06-15 10:00-12:00",
            goods=[]
        )
        
        # 执行
        result = await OrderService.create_order(order_create, mock_db)
        
        # 验证
        assert result["code"] == CODE_NODE_NOT_FOUND
        assert "目的地节点不存在" in result["message"]

    @pytest.mark.asyncio
    async def test_create_order_not_sorting_center(self, mock_db):
        """测试目的地不是分拣中心"""
        # 创建非分拣中心节点
        node = MagicMock(spec=Node)
        node.node_type = "storage_center"
        mock_db.query.return_value.filter.return_value.first.return_value = node
        
        # 创建请求数据
        order_create = OrderCreate(
            destination_node_code="SC001",
            time_window="2026-06-15 10:00-12:00",
            goods=[]
        )
        
        # 执行
        result = await OrderService.create_order(order_create, mock_db)
        
        # 验证
        assert result["code"] == CODE_PARAM_ERROR
        assert "必须是分拣中心" in result["message"]

    @pytest.mark.asyncio
    async def test_create_order_not_level0(self, mock_db):
        """测试目的地不是0级分拣中心"""
        # 创建1级分拣中心节点
        node = MagicMock(spec=Node)
        node.node_type = "sorting_center"
        sorting_center = MagicMock()
        sorting_center.level = 1
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [node, sorting_center]
        
        # 创建请求数据
        order_create = OrderCreate(
            destination_node_code="SO001",
            time_window="2026-06-15 10:00-12:00",
            goods=[]
        )
        
        # 执行
        result = await OrderService.create_order(order_create, mock_db)
        
        # 验证
        assert result["code"] == CODE_PARAM_ERROR
        assert "必须是0级分拣中心" in result["message"]


class TestOrderServiceGetOrders:
    """测试获取订单列表"""

    @pytest.mark.asyncio
    async def test_get_orders_success(self, mock_db, sample_order):
        """测试成功获取订单列表"""
        # 模拟数据库查询
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.offset.return_value.limit.return_value.all.return_value = [sample_order]
        
        # 模拟关联对象
        sample_order.destination_node = MagicMock()
        sample_order.destination_node.node_code = "SO001"
        sample_order.destination_node.name = "测试节点"
        sample_order.goods = []
        
        # 执行
        result = await OrderService.get_orders(1, 20, None, mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert "items" in result["data"]
        assert result["data"]["total"] == 1

    @pytest.mark.asyncio
    async def test_get_orders_with_status_filter(self, mock_db):
        """测试按状态筛选订单"""
        # 模拟数据库查询
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.offset.return_value.limit.return_value.all.return_value = []
        
        # 执行
        result = await OrderService.get_orders(1, 20, "pending", mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert result["data"]["total"] == 0


class TestOrderServiceGetOrder:
    """测试获取订单详情"""

    @pytest.mark.asyncio
    async def test_get_order_success(self, mock_db, sample_order):
        """测试成功获取订单详情"""
        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_order,  # 查询订单
            MagicMock(node_code="SO001", name="测试节点"),  # 查询目的地节点
            [],  # 查询货物列表
        ]
        
        # 执行
        result = await OrderService.get_order("O1700000000000", mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert result["data"]["order_code"] == "O1700000000000"

    @pytest.mark.asyncio
    async def test_get_order_not_found(self, mock_db):
        """测试订单不存在"""
        # 模拟数据库查询返回None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 执行
        result = await OrderService.get_order("INVALID", mock_db)
        
        # 验证
        assert result["code"] == CODE_ORDER_NOT_FOUND
        assert "订单不存在" in result["message"]


class TestOrderServiceUpdateOrder:
    """测试更新订单"""

    @pytest.mark.asyncio
    async def test_update_order_success(self, mock_db, sample_order):
        """测试成功更新订单"""
        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_order,  # 查询订单
            MagicMock(node_code="SO002", name="新节点"),  # 查询新目的地节点
            MagicMock(node_code="SO002", name="新节点"),  # 再次查询目的地节点
        ]
        
        # 创建更新数据
        order_update = OrderUpdate(destination_node_code="SO002")
        
        # 执行
        result = await OrderService.update_order("O1700000000000", order_update, mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert result["data"]["destination_node_code"] == "SO002"

    @pytest.mark.asyncio
    async def test_update_order_not_found(self, mock_db):
        """测试订单不存在"""
        # 模拟数据库查询返回None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 创建更新数据
        order_update = OrderUpdate(destination_node_code="SO002")
        
        # 执行
        result = await OrderService.update_order("INVALID", order_update, mock_db)
        
        # 验证
        assert result["code"] == CODE_ORDER_NOT_FOUND
        assert "订单不存在" in result["message"]

    @pytest.mark.asyncio
    async def test_update_order_status_not_allowed(self, mock_db, sample_order):
        """测试订单状态不允许修改"""
        # 设置订单状态为delivering
        sample_order.status = "delivering"
        mock_db.query.return_value.filter.return_value.first.return_value = sample_order
        
        # 创建更新数据
        order_update = OrderUpdate(destination_node_code="SO002")
        
        # 执行
        result = await OrderService.update_order("O1700000000000", order_update, mock_db)
        
        # 验证
        assert result["code"] == CODE_ORDER_STATUS_NOT_ALLOWED
        assert "不允许修改" in result["message"]


class TestOrderServiceDeleteOrder:
    """测试删除订单"""

    @pytest.mark.asyncio
    async def test_delete_order_success(self, mock_db, sample_order):
        """测试成功删除订单"""
        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.return_value = sample_order
        mock_db.query.return_value.filter.return_value.all.return_value = []  # 没有关联货物
        
        # 执行
        result = await OrderService.delete_order("O1700000000000", mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert result["message"] == "success"

    @pytest.mark.asyncio
    async def test_delete_order_not_found(self, mock_db):
        """测试订单不存在"""
        # 模拟数据库查询返回None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 执行
        result = await OrderService.delete_order("INVALID", mock_db)
        
        # 验证
        assert result["code"] == CODE_ORDER_NOT_FOUND
        assert "订单不存在" in result["message"]

    @pytest.mark.asyncio
    async def test_delete_order_status_not_allowed(self, mock_db, sample_order):
        """测试订单状态不允许删除"""
        # 设置订单状态为delivering
        sample_order.status = "delivering"
        mock_db.query.return_value.filter.return_value.first.return_value = sample_order
        
        # 执行
        result = await OrderService.delete_order("O1700000000000", mock_db)
        
        # 验证
        assert result["code"] == CODE_ORDER_STATUS_NOT_ALLOWED
        assert "不允许删除" in result["message"]
