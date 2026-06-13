"""
test_packaging.py — F021 打包算法单元测试

测试用例：
1. L0→L1 按节点对打包
2. L1→L2 按订单打包
"""
import pytest
from algorithms.packaging import packaging


# ── 辅助：构造 F007 输出的模拟数据 ──


def make_schedule_result():
    """构造一个标准的 F007 输出作为 F021 输入"""
    return {
        "schedule_code": "GS20260613001",
        "order_codes": ["O001", "O002", "O003"],
        "total_distance": 100.0,
        "total_time": 5.0,
        "total_goods": 3,
        "score": 55.0,
        "goods_schedules": [
            {
                "goods_code": "G001",
                "order_code": "O001",
                "path": ["SC001", "SO001", "SO010"],  # L0→L1→L2
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
        ],
    }


def make_schedule_result_same_l0_l1():
    """
    多个货物共享相同的 L0→L1 节点对
    用于测试 L0→L1 按节点对打包的合并行为
    """
    return {
        "schedule_code": "GS20260613002",
        "order_codes": ["O001"],
        "total_distance": 50.0,
        "total_time": 2.0,
        "total_goods": 2,
        "score": 25.0,
        "goods_schedules": [
            {
                "goods_code": "G001",
                "order_code": "O001",
                "path": ["SC001", "SO001", "SO010"],
            },
            {
                "goods_code": "G002",
                "order_code": "O001",
                "path": ["SC001", "SO001", "SO010"],
            },
        ],
    }


def make_schedule_result_multi_order_l1_l2():
    """
    同一订单多个货物 → L1→L2 合并为一个包裹
    """
    return {
        "schedule_code": "GS20260613003",
        "order_codes": ["O001"],
        "total_distance": 50.0,
        "total_time": 2.0,
        "total_goods": 3,
        "score": 25.0,
        "goods_schedules": [
            {
                "goods_code": "G001",
                "order_code": "O001",
                "path": ["SC001", "SO001", "SO010"],
            },
            {
                "goods_code": "G002",
                "order_code": "O001",
                "path": ["SC001", "SO001", "SO010"],
            },
            {
                "goods_code": "G003",
                "order_code": "O001",
                "path": ["SC001", "SO001", "SO010"],
            },
        ],
    }


# ── 辅助：通过 node_id 获取 node_code ──


def get_node_code(db_session, node_id):
    """通过 node_id 查询 node_code"""
    from models.node import Node
    node = db_session.query(Node).filter(Node.id == node_id).first()
    return node.node_code if node else None


class TestPackagingL0ToL1:
    """L0→L1 按节点对打包"""

    @pytest.mark.unit
    def test_l0_l1_packaging_by_node_pair(self, db_session, test_nodes, test_orders, test_goods):
        """
        测试 L0→L1 包裹按 (from_node_code, to_node_code) 节点对分组：
        - SC001→SO001: 包含 G001 (O001) 和 G002 (O002) → 1 个包裹
        - SC002→SO002: 包含 G003 (O003) → 1 个包裹
        - L1→L2 按订单分组：
          - O001 → SO001→SO010 → 1 个包裹 (G001)
          - O002 → SO001→SO011 → 1 个包裹 (G002)
          - O003 → SO002→SO012 → 1 个包裹 (G003)
        总计：2 (L0→L1) + 3 (L1→L2) = 5 个包裹
        """
        schedule_result = make_schedule_result()
        packages = packaging(schedule_result, schedule_id=None, db=db_session)

        # ── 验证包裹总数 ──
        assert len(packages) == 5, f"期望 5 个包裹，实际 {len(packages)} 个"

        # ── 通过 from_node_id/to_node_id 获取节点编码 ──
        # 构建 node_id → node_code 映射
        node_id_to_code = {n.id: n.node_code for n in test_nodes.values()}

        # ── 验证 L0→L1 包裹 ──
        l0_l1_packages = [
            pkg for pkg in packages
            if node_id_to_code.get(pkg.from_node_id, "").startswith("SC")
            and node_id_to_code.get(pkg.to_node_id, "") in ("SO001", "SO002")
        ]
        # 确认 L0→L1 包裹的节点对分组
        assert len(l0_l1_packages) == 2

        # SC001→SO001 的包裹应包含 G001 和 G002
        sc001_so001_pkg = [
            pkg for pkg in l0_l1_packages
            if node_id_to_code.get(pkg.from_node_id) == "SC001"
            and node_id_to_code.get(pkg.to_node_id) == "SO001"
        ]
        assert len(sc001_so001_pkg) == 1
        pkg = sc001_so001_pkg[0]
        goods_codes_in_pkg = [item["goods_code"] for item in pkg.goods_items]
        assert "G001" in goods_codes_in_pkg
        assert "G002" in goods_codes_in_pkg
        assert len(goods_codes_in_pkg) == 2

        # SC002→SO002 的包裹应只包含 G003
        sc002_so002_pkg = [
            pkg for pkg in l0_l1_packages
            if node_id_to_code.get(pkg.from_node_id) == "SC002"
            and node_id_to_code.get(pkg.to_node_id) == "SO002"
        ]
        assert len(sc002_so002_pkg) == 1
        goods_codes = [item["goods_code"] for item in sc002_so002_pkg[0].goods_items]
        assert goods_codes == ["G003"]

        # ── 验证 L1→L2 包裹 ──
        l1_l2_packages = [
            pkg for pkg in packages
            if node_id_to_code.get(pkg.from_node_id, "") in ("SO001", "SO002")
            and node_id_to_code.get(pkg.to_node_id, "") in ("SO010", "SO011", "SO012")
        ]
        assert len(l1_l2_packages) == 3

    @pytest.mark.unit
    def test_l0_l1_packaging_merges_same_node_pair(self, db_session, test_nodes, test_orders, test_goods):
        """
        同一 L0→L1 节点对的多个货物合并为一个包裹
        场景：G001 和 G002 都走 SC001→SO001，应打包为 1 个 L0→L1 包裹
        """
        schedule_result = make_schedule_result_same_l0_l1()
        packages = packaging(schedule_result, schedule_id=None, db=db_session)

        node_id_to_code = {n.id: n.node_code for n in test_nodes.values()}

        # L0→L1 应只有 1 个包裹（合并了同节点对的货物）
        l0_l1_packages = [
            pkg for pkg in packages
            if node_id_to_code.get(pkg.from_node_id) == "SC001"
            and node_id_to_code.get(pkg.to_node_id) == "SO001"
        ]
        assert len(l0_l1_packages) == 1, (
            f"相同 SC001→SO001 节点对应合并为 1 个包裹，实际 {len(l0_l1_packages)} 个"
        )
        goods_codes = [item["goods_code"] for item in l0_l1_packages[0].goods_items]
        assert len(goods_codes) == 2

        # L1→L2 应有 1 个包裹（O001 的货物合并）
        l1_l2_packages = [
            pkg for pkg in packages
            if node_id_to_code.get(pkg.from_node_id) == "SO001"
            and node_id_to_code.get(pkg.to_node_id) == "SO010"
        ]
        assert len(l1_l2_packages) == 1

    @pytest.mark.unit
    def test_package_has_correct_fields(self, db_session, test_nodes, test_orders, test_goods):
        """验证生成的 Package 对象包含正确的字段"""
        schedule_result = make_schedule_result()
        packages = packaging(schedule_result, schedule_id=None, db=db_session)

        for pkg in packages:
            assert pkg.package_code.startswith("PKG")
            assert pkg.status == "pending_pack"
            assert pkg.weight > 0
            assert pkg.volume > 0
            assert pkg.from_node_id is not None
            assert pkg.to_node_id is not None
            assert pkg.goods_items is not None
            assert len(pkg.goods_items) > 0
            assert pkg.from_longitude is not None
            assert pkg.from_latitude is not None
            assert pkg.to_longitude is not None
            assert pkg.to_latitude is not None


class TestPackagingL1ToL2:
    """L1→L2 按订单打包"""

    @pytest.mark.unit
    def test_l1_l2_packaging_by_order(self, db_session, test_nodes, test_orders, test_goods):
        """
        测试 L1→L2 按 order_code 分组打包：
        同一订单的货物合并为一个 L1→L2 包裹
        """
        schedule_result = make_schedule_result()
        packages = packaging(schedule_result, schedule_id=None, db=db_session)

        node_id_to_code = {n.id: n.node_code for n in test_nodes.values()}

        # ── 找到 O001 的 L1→L2 包裹 ──
        o001_l1_l2 = [
            pkg for pkg in packages
            if node_id_to_code.get(pkg.from_node_id) == "SO001"
            and node_id_to_code.get(pkg.to_node_id) == "SO010"
        ]
        assert len(o001_l1_l2) == 1
        pkg = o001_l1_l2[0]
        # 验证 goods_items 中包含正确的 order_code
        for item in pkg.goods_items:
            assert item["order_code"] == "O001"

        # ── 找到 O002 的 L1→L2 包裹 ──
        o002_l1_l2 = [
            pkg for pkg in packages
            if node_id_to_code.get(pkg.from_node_id) == "SO001"
            and node_id_to_code.get(pkg.to_node_id) == "SO011"
        ]
        assert len(o002_l1_l2) == 1
        for item in o002_l1_l2[0].goods_items:
            assert item["order_code"] == "O002"

        # ── 找到 O003 的 L1→L2 包裹 ──
        o003_l1_l2 = [
            pkg for pkg in packages
            if node_id_to_code.get(pkg.from_node_id) == "SO002"
            and node_id_to_code.get(pkg.to_node_id) == "SO012"
        ]
        assert len(o003_l1_l2) == 1
        for item in o003_l1_l2[0].goods_items:
            assert item["order_code"] == "O003"

    @pytest.mark.unit
    def test_multi_goods_same_order_merged(self, db_session, test_nodes, test_orders, test_goods):
        """
        同一订单多个货物合并为一个 L1→L2 包裹
        场景：O001 有 3 个货物，应合并为 1 个 L1→L2 包裹
        """
        schedule_result = make_schedule_result_multi_order_l1_l2()
        packages = packaging(schedule_result, schedule_id=None, db=db_session)

        node_id_to_code = {n.id: n.node_code for n in test_nodes.values()}

        # 按订单分组验证
        l1_l2_packages = [
            pkg for pkg in packages
            if node_id_to_code.get(pkg.from_node_id) == "SO001"
            and node_id_to_code.get(pkg.to_node_id) == "SO010"
        ]
        assert len(l1_l2_packages) == 1, (
            f"同一订单 O001 的 3 个货物应合并为 1 个 L1→L2 包裹，实际 {len(l1_l2_packages)} 个"
        )
        pkg = l1_l2_packages[0]
        assert len(pkg.goods_items) == 3, f"包裹应包含 3 个货物，实际 {len(pkg.goods_items)} 个"


class TestPackagingEdgeCases:
    """边界情况测试"""

    @pytest.mark.unit
    def test_empty_goods_schedules_raises_error(self, db_session):
        """空 goods_schedules 抛出 ValueError"""
        schedule_result = {
            "schedule_code": "GS_EMPTY",
            "goods_schedules": [],
        }
        with pytest.raises(ValueError, match="goods_schedules 为空"):
            packaging(schedule_result, schedule_id=None, db=db_session)

    @pytest.mark.unit
    def test_package_code_uniqueness(self, db_session, test_nodes, test_orders, test_goods):
        """验证同一批次内 package_code 不重复"""
        schedule_result = make_schedule_result()
        packages = packaging(schedule_result, schedule_id=None, db=db_session)

        codes = [pkg.package_code for pkg in packages]
        assert len(codes) == len(set(codes)), (
            f"package_code 不应重复，共 {len(codes)} 个包裹，唯一值 {len(set(codes))} 个"
        )

    @pytest.mark.unit
    def test_package_schedule_id_assignment(self, db_session, test_nodes, test_orders, test_goods):
        """验证 schedule_id 正确赋值"""
        schedule_result = make_schedule_result()
        test_schedule_id = 42
        packages = packaging(schedule_result, schedule_id=test_schedule_id, db=db_session)

        for pkg in packages:
            assert pkg.schedule_id == test_schedule_id, (
                f"包裹 {pkg.package_code} 的 schedule_id 应为 {test_schedule_id}，"
                f"实际 {pkg.schedule_id}"
            )
