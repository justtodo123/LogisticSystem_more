"""
算法单元测试：F021 打包（packaging）

测试目标：
- packaging 函数的正常流程和异常流程
- 验证输出结构、打包逻辑、边界条件
"""
import pytest
from algorithms.packaging import packaging
from models.package import Package
from models.goods import Goods
import json


class TestPackagingNormal:
    """正常情况：生成包裹"""

    @pytest.mark.unit
    def test_packaging_generates_packages(self, db_session, test_nodes, test_orders, test_goods):
        """
        测试正常打包流程：
        - 输入 goods_schedules（来自F007输出）
        - 算法应成功生成 packages
        - 输出结果包含正确的字段
        """
        # 构造 goods_schedules 输入（模拟F007输出）
        goods_schedules = [
            {
                "goods_code": "G001",
                "order_code": "O001",
                "path": ["SC001", "SO001", "SO010"],
            },
            {
                "goods_code": "G002",
                "order_code": "O002",
                "path": ["SC001", "SO001", "SO011"],
            },
            {
                "goods_code": "G003",
                "order_code": "O003",
                "path": ["SC002", "SO002", "SO012"],
            },
        ]
        
        # 执行 F021
        result = packaging(
            goods_schedules=goods_schedules,
            db=db_session,
        )
        
        # ── 验证返回结构 ──
        assert isinstance(result, list)
        assert len(result) > 0
        
        # 验证每个包裹的字段
        for pkg in result:
            assert "package_code" in pkg
            assert "from_node_code" in pkg
            assert "to_node_code" in pkg
            assert "weight" in pkg
            assert "volume" in pkg
            assert "goods_items" in pkg
            assert "level" in pkg
            
            # 验证 goods_items 结构
            assert isinstance(pkg["goods_items"], list)
            for item in pkg["goods_items"]:
                assert "goods_code" in item
                assert "order_code" in item
        
        # ── 验证包裹数量 ──
        # 应该生成 L0→L1 和 L1→L2 的包裹
        # G001: SC001→SO001 (L0→L1), SO001→SO010 (L1→L2)
        # G002: SC001→SO001 (L0→L1), SO001→SO011 (L1→L2)
        # G003: SC002→SO002 (L0→L1), SO002→SO012 (L1→L2)
        # 所以总共应该有多于3个包裹（因为L0→L1和L1→L2是分开的）
        assert len(result) >= 3

    @pytest.mark.unit
    def test_packaging_l0_l1_merge(self, db_session, test_nodes, test_orders, test_goods):
        """
        测试 L0→L1 按 from/to 节点对合并：
        - G001 和 G002 都是从 SC001 到 SO001
        - 应该被打在同一个 L0→L1 包裹中
        """
        # 构造 goods_schedules 输入
        goods_schedules = [
            {
                "goods_code": "G001",
                "order_code": "O001",
                "path": ["SC001", "SO001", "SO010"],
            },
            {
                "goods_code": "G002",
                "order_code": "O002",
                "path": ["SC001", "SO001", "SO011"],
            },
        ]
        
        # 执行 F021
        result = packaging(
            goods_schedules=goods_schedules,
            db=db_session,
        )
        
        # 查找 L0→L1 的包裹（level=0）
        l0_l1_packages = [pkg for pkg in result if pkg["level"] == 0]
        
        # 应该至少有一个 L0→L1 包裹包含 G001 和 G002
        found_merged = False
        for pkg in l0_l1_packages:
            goods_codes = [item["goods_code"] for item in pkg["goods_items"]]
            if "G001" in goods_codes and "G002" in goods_codes:
                found_merged = True
                break
        
        assert found_merged, "G001 和 G002 应该从 SC001 到 SO001，被打在同一个 L0→L1 包裹中"

    @pytest.mark.unit
    def test_packaging_l1_l2_by_order(self, db_session, test_nodes, test_orders, test_goods):
        """
        测试 L1→L2 按同订单合并：
        - 同一订单的货物必须打成一个包裹
        """
        # 给 O001 添加第二个货物，使 O001 有两个货物
        from models.goods import Goods
        goods2 = Goods(
            goods_code="G001_B",
            goods_name="测试货物A2",
            goods_type="普通",
            weight=3.0,
            volume=0.1,
            node_id=test_nodes["SC001"].id,
            order_id=test_orders["O001"].id,
            status="pending_pack",
        )
        db_session.add(goods2)
        db_session.commit()
        db_session.refresh(test_orders["O001"])
        
        # 构造 goods_schedules 输入（G001 和 G001_B 都属于 O001）
        goods_schedules = [
            {
                "goods_code": "G001",
                "order_code": "O001",
                "path": ["SC001", "SO001", "SO010"],
            },
            {
                "goods_code": "G001_B",
                "order_code": "O001",
                "path": ["SC001", "SO001", "SO010"],
            },
            {
                "goods_code": "G002",
                "order_code": "O002",
                "path": ["SC001", "SO001", "SO011"],
            },
        ]
        
        # 执行 F021
        result = packaging(
            goods_schedules=goods_schedules,
            db=db_session,
        )
        
        # 查找 L1→L2 的包裹（level=1）
        l1_l2_packages = [pkg for pkg in result if pkg["level"] == 1]
        
        # O001 的两个货物应该被打在同一个 L1→L2 包裹中
        found_merged = False
        for pkg in l1_l2_packages:
            goods_codes = [item["goods_code"] for item in pkg["goods_items"]]
            if "G001" in goods_codes and "G001_B" in goods_codes:
                found_merged = True
                break
        
        assert found_merged, "同一订单 O001 的货物应该被打在同一个 L1→L2 包裹中"


class TestPackagingEdgeCases:
    """边界条件测试"""

    @pytest.mark.unit
    def test_packaging_empty_input(self, db_session):
        """
        测试空输入：
        - goods_schedules 为空列表
        - 应该返回空列表或抛出异常
        """
        result = packaging(
            goods_schedules=[],
            db=db_session,
        )
        
        # 验证返回空列表
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.unit
    def test_packaging_invalid_goods_code(self, db_session):
        """
        测试无效的货物编号：
        - goods_schedules 包含不存在的 goods_code
        - 应该抛出异常或返回错误
        """
        goods_schedules = [
            {
                "goods_code": "G_NONEXIST",
                "order_code": "O001",
                "path": ["SC001", "SO001", "SO010"],
            },
        ]
        
        # 可能会抛出异常（因为找不到货物）
        with pytest.raises(Exception):
            packaging(
                goods_schedules=goods_schedules,
                db=db_session,
            )
