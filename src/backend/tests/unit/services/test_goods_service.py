"""
GoodsService 单元测试

测试货物服务 (services/goods_service.py) 的所有方法：
- get_goods: 获取货物列表
- get_good: 获取货物详情
- update_good: 更新货物
"""
import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from datetime import datetime

from services.goods_service import GoodsService
from models.goods import Goods
from models.order import Order
from models.node import Node
from schemas.goods import GoodsUpdate
from core.error_codes import (
    CODE_SUCCESS, CODE_INTERNAL_ERROR,
    CODE_GOODS_NOT_FOUND, CODE_NODE_NOT_FOUND
)


@pytest.fixture
def mock_db():
    """Mock数据库会话"""
    db = MagicMock(spec=Session)
    return db


@pytest.fixture
def sample_goods():
    """示例货物"""
    goods = MagicMock(spec=Goods)
    goods.id = 1
    goods.goods_code = "G1700000000000_0"
    goods.goods_name = "测试货物"
    goods.goods_type = "electronics"
    goods.weight = 10.0
    goods.volume = 0.5
    goods.status = "pending_pack"
    goods.order_id = 1
    goods.node_id = 1
    goods.created_at = datetime.now()
    goods.updated_at = datetime.now()
    return goods


class TestGoodsServiceGetGoods:
    """测试获取货物列表"""

    @pytest.mark.asyncio
    async def test_get_goods_success(self, mock_db, sample_goods):
        """测试成功获取货物列表"""
        # 模拟数据库查询
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.offset.return_value.limit.return_value.all.return_value = [sample_goods]
        
        # 模拟关联对象
        sample_goods.order = MagicMock()
        sample_goods.order.order_code = "O1700000000000"
        sample_goods.node = MagicMock()
        sample_goods.node.node_code = "SC001"
        sample_goods.node.name = "存储中心"
        
        # 执行
        result = await GoodsService.get_goods(1, 20, None, None, None, mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert "items" in result["data"]
        assert result["data"]["total"] == 1

    @pytest.mark.asyncio
    async def test_get_goods_with_status_filter(self, mock_db):
        """测试按状态筛选货物"""
        # 模拟数据库查询
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.offset.return_value.limit.return_value.all.return_value = []
        
        # 执行
        result = await GoodsService.get_goods(1, 20, "pending_pack", None, None, mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert result["data"]["total"] == 0

    @pytest.mark.asyncio
    async def test_get_goods_with_node_filter(self, mock_db):
        """测试按节点筛选货物"""
        # 模拟数据库查询
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.offset.return_value.limit.return_value.all.return_value = []
        
        # 模拟节点查询
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock(id=1)
        
        # 执行
        result = await GoodsService.get_goods(1, 20, None, "SC001", None, mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert result["data"]["total"] == 0


class TestGoodsServiceGetGood:
    """测试获取货物详情"""

    @pytest.mark.asyncio
    async def test_get_good_success(self, mock_db, sample_goods):
        """测试成功获取货物详情"""
        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_goods,  # 查询货物
            MagicMock(order_code="O1700000000000"),  # 查询订单
            MagicMock(node_code="SC001", name="存储中心"),  # 查询节点
        ]
        
        # 执行
        result = await GoodsService.get_good("G1700000000000_0", mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert result["data"]["goods_code"] == "G1700000000000_0"

    @pytest.mark.asyncio
    async def test_get_good_not_found(self, mock_db):
        """测试货物不存在"""
        # 模拟数据库查询返回None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 执行
        result = await GoodsService.get_good("INVALID", mock_db)
        
        # 验证
        assert result["code"] == CODE_GOODS_NOT_FOUND
        assert "货物不存在" in result["message"]


class TestGoodsServiceUpdateGood:
    """测试更新货物"""

    @pytest.mark.asyncio
    async def test_update_good_success(self, mock_db, sample_goods):
        """测试成功更新货物"""
        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_goods,  # 查询货物
            MagicMock(node_code="SC002", name="新节点"),  # 查询新节点
            MagicMock(order_code="O1700000000000"),  # 查询订单
            MagicMock(node_code="SC002", name="新节点"),  # 再次查询节点
        ]
        
        # 创建更新数据
        goods_update = GoodsUpdate(goods_name="更新后的货物", node_code="SC002")
        
        # 执行
        result = await GoodsService.update_good("G1700000000000_0", goods_update, mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert result["data"]["goods_name"] == "更新后的货物"

    @pytest.mark.asyncio
    async def test_update_good_not_found(self, mock_db):
        """测试货物不存在"""
        # 模拟数据库查询返回None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 创建更新数据
        goods_update = GoodsUpdate(goods_name="更新后的货物")
        
        # 执行
        result = await GoodsService.update_good("INVALID", goods_update, mock_db)
        
        # 验证
        assert result["code"] == CODE_GOODS_NOT_FOUND
        assert "货物不存在" in result["message"]

    @pytest.mark.asyncio
    async def test_update_good_node_not_found(self, mock_db, sample_goods):
        """测试节点不存在"""
        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_goods,  # 查询货物
            None,  # 查询节点返回None
        ]
        
        # 创建更新数据
        goods_update = GoodsUpdate(node_code="INVALID")
        
        # 执行
        result = await GoodsService.update_good("G1700000000000_0", goods_update, mock_db)
        
        # 验证
        assert result["code"] == CODE_NODE_NOT_FOUND
        assert "节点不存在" in result["message"]
