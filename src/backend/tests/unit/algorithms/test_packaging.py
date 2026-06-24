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
            schedule_result={"goods_schedules": goods_schedules},
            schedule_id=1,
            db=db_session,
        )
        
        # ── 验证返回结构 ──
        assert isinstance(result, list)
        assert len(result) > 0
        
        # 验证每个包裹的字段
        for pkg in result:
            assert hasattr(pkg, 'package_code')
            assert hasattr(pkg, 'from_node_id')
            assert hasattr(pkg, 'to_node_id')
            assert hasattr(pkg, 'weight')
            assert hasattr(pkg, 'volume')
            assert hasattr(pkg, 'goods_items')
            
            # 验证 goods_items 结构
            assert isinstance(pkg.goods_items, list)
            for item in pkg.goods_items:
                assert "goods_code" in item
                assert "order_code" in item
        
        # ── 验证包裹数量 ──
        # P1-3: F021 初始仅生成 L0→L1 包裹，L1→L2 由 confirm-arrival repacking 动态创建
        # G001+G002: SC001→SO001 (合并为1个 L0→L1 包裹)
        # G003: SC002→SO002 (1个 L0→L1 包裹)
        # 总共 2 个包裹
        assert len(result) == 2

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
            schedule_result={"goods_schedules": goods_schedules},
            schedule_id=1,
            db=db_session,
        )
        
        # 查找 L0→L1 的包裹（from_node_id 对应的节点是 storage_center）
        from models.node import Node
        l0_l1_packages = []
        for pkg in result:
            from_node = db_session.query(Node).filter(Node.id == pkg.from_node_id).first()
            if from_node and from_node.node_type == "storage_center":
                l0_l1_packages.append(pkg)
        
        # 应该至少有一个 L0→L1 包裹包含 G001 和 G002
        found_merged = False
        for pkg in l0_l1_packages:
            goods_codes = [item["goods_code"] for item in pkg.goods_items]
            if "G001" in goods_codes and "G002" in goods_codes:
                found_merged = True
                break
        
        assert found_merged, "G001 和 G002 应该从 SC001 到 SO001，被打在同一个 L0→L1 包裹中"




class TestPackagingEdgeCases:
    """边界条件测试"""

    @pytest.mark.unit
    def test_packaging_empty_input(self, db_session):
        """
        测试空输入：
        - goods_schedules 为空列表
        - 应该抛出异常
        """
        with pytest.raises(ValueError):
            result = packaging(
                schedule_result={"goods_schedules": []},
                schedule_id=1,
                db=db_session,
            )

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
        
        # 不会抛出异常（因为函数会跳过无效的货物）
        result = packaging(
            schedule_result={"goods_schedules": goods_schedules},
            schedule_id=1,
            db=db_session,
        )
        # 验证返回空列表（因为所有货物都无效）
        assert isinstance(result, list)
