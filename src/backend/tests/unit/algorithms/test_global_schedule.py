"""
算法单元测试：F007 全局调度（global_schedule）

测试目标：
- global_schedule 函数的正常流程和异常流程
- 验证输出结构、约束满足、边界条件
"""
import pytest
from algorithms.global_schedule import global_schedule


class TestGlobalScheduleNormal:
    """正常情况：生成路径"""

    @pytest.mark.unit
    def test_normal_schedule_generates_paths(self, db_session, test_nodes, test_orders, test_goods):
        """
        测试正常调度流程：
        - 3 个 pending 订单、3 个货物
        - 算法应成功为每个货物规划 L0→L1→L2 路径
        - 输出结果包含正确的字段
        """
        # 执行 F007
        result = global_schedule(
            order_codes=None,  # 处理所有 pending 订单
            algorithm="traditional",
            db=db_session,
        )

        # ── 验证返回结构 ──
        assert "schedule_code" in result
        assert result["schedule_code"].startswith("GS")
        assert "order_codes" in result
        assert "total_distance" in result
        assert "total_time" in result
        assert "total_goods" in result
        assert "score" in result
        assert "goods_schedules" in result

        # ── 验证 goods_schedules ──
        goods_schedules = result["goods_schedules"]
        assert len(goods_schedules) == 18  # 9个订单 × 每单2个货物

        for gs in goods_schedules:
            assert "goods_code" in gs
            assert "order_code" in gs
            assert "path" in gs
            assert len(gs["path"]) == 3  # L0 → L1 → L2

            # 路径第一个节点应为 L0（存储中心）
            path = gs["path"]
            assert path[0].startswith("SC")

            # 路径第二个节点应为 L1（1级分拣中心）
            assert path[1].startswith("SO")

            # 路径第三个节点应为 L2（0级分拣中心，目的地）
            assert path[2].startswith("SO")

        # ── 验证同订单汇聚 ──
        # G001 属于 O001（目的地 SO010）
        # G002 属于 O002（目的地 SO011）
        # 同一订单的货物应走相同的 L1
        o001_goods = [gs for gs in goods_schedules if gs["order_code"] == "O001"]
        if len(o001_goods) > 1:
            l1_codes = [gs["path"][1] for gs in o001_goods]
            assert len(set(l1_codes)) == 1, "同一订单的货物必须汇聚到相同 L1"

        # ── 验证数值合理性 ──
        assert result["total_distance"] > 0
        assert result["total_time"] > 0
        assert result["total_goods"] == 18
        assert result["score"] > 0

        # ── 验证 order_codes ──
        assert len(result["order_codes"]) == 9
        for code in ["O001", "O002", "O003", "O004", "O005", "O006", "O007", "O008", "O009"]:
            assert code in result["order_codes"]


class TestGlobalScheduleHardConstraint:
    """硬约束触发：无法调度"""

    @pytest.mark.unit
    def test_no_l1_available_raises_error(self, db_session):
        """
        测试没有 L1 节点时抛出 ValueError
        """
        from models.node import Node
        from models.order import Order
        from models.sorting_center import SortingCenter
        from models.goods import Goods

        # 创建 L0 节点
        l0 = Node(
            node_code="SC_NO_L1",
            name="无L1存储中心",
            location="测试",
            latitude=30.5,
            longitude=114.3,
            node_type="storage_center",
        )
        db_session.add(l0)
        db_session.flush()

        from models.storage_center import StorageCenter
        sc = StorageCenter(node_id=l0.id, capacity=100.0, inventory=0)
        db_session.add(sc)

        # 创建 L2 节点
        l2 = Node(
            node_code="SO_DEST",
            name="目的地",
            location="测试",
            latitude=30.6,
            longitude=114.4,
            node_type="sorting_center",
        )
        db_session.add(l2)
        db_session.flush()
        sc2 = SortingCenter(node_id=l2.id, level=0)
        db_session.add(sc2)

        # 创建订单
        order = Order(
            order_code="O_NO_L1",
            destination_node_id=l2.id,
            time_window="全天",
            status="pending",
        )
        db_session.add(order)
        db_session.flush()

        # 创建货物
        goods = Goods(
            goods_code="G_NO_L1",
            goods_name="测试货物",
            goods_type="普通",
            weight=5.0,
            volume=0.2,
            node_id=l0.id,
            order_id=order.id,
            status="pending_pack",
        )
        db_session.add(goods)
        db_session.commit()
        db_session.refresh(order)

        # 执行调度 — 没有 L1 节点应抛出 ValueError
        with pytest.raises(ValueError, match="没有找到 1 级分拣中心"):
            global_schedule(order_codes=None, algorithm="traditional", db=db_session)

    @pytest.mark.unit
    def test_l1_capacity_exceeded_raises_error(self, db_session, test_nodes, test_orders, test_goods):
        """
        测试 L1 容量不足以容纳所有包裹时抛出 ValueError
        所有 L1 容量设为 0，使算法无法为任何货物找到可用 L1
        """
        from models.sorting_center import SortingCenter
        # 把所有 L1 的容量都改为 0
        for node_code in ["SO001", "SO002"]:
            sc = db_session.query(SortingCenter).filter(
                SortingCenter.node_id == test_nodes[node_code].id
            ).first()
            sc.capacity = 0
        db_session.commit()

        # 执行调度 — 没有可用 L1，应该失败
        with pytest.raises(ValueError, match="无法为货物.*找到满足所有硬约束的 L1"):
            global_schedule(order_codes=None, algorithm="traditional", db=db_session)


class TestGlobalScheduleGreedySelection:
    """贪心选择：选择第一个满足条件的 L1（评分最低）"""

    @pytest.mark.unit
    def test_greedy_selects_lowest_score_l1(self, db_session, test_nodes, test_orders, test_goods):
        """
        测试贪心策略选择评分最低的 L1：
        - SO001 离 SC001 更近（武汉 → 武汉），评分应更低
        - SO002 离 SC001 更远（武汉 → 长沙），评分应更高
        - 来自 SC001 的货物 G001、G002 应优先选择 SO001
        """
        result = global_schedule(
            order_codes=None,
            algorithm="traditional",
            db=db_session,
        )

        goods_schedules = result["goods_schedules"]

        # 来自 SC001（武汉）的货物应选择 SO001（武汉L1），因为更近
        sc001_goods = [gs for gs in goods_schedules if gs["path"][0] == "SC001"]
        for gs in sc001_goods:
            # SO001 距离 SC001 更近，评分更低，应被贪心选中
            assert gs["path"][1] == "SO001", (
                f"货物 {gs['goods_code']} 来自 SC001，应选择最近的 L1 SO001，"
                f"但实际选择了 {gs['path'][1]}"
            )

        # 来自 SC002（长沙）的货物应选择 SO002（长沙L1），因为更近
        sc002_goods = [gs for gs in goods_schedules if gs["path"][0] == "SC002"]
        for gs in sc002_goods:
            assert gs["path"][1] == "SO002", (
                f"货物 {gs['goods_code']} 来自 SC002，应选择最近的 L1 SO002，"
                f"但实际选择了 {gs['path'][1]}"
            )

    @pytest.mark.unit
    def test_same_order_same_l1_enforcement(self, db_session, test_nodes, test_orders, test_goods):
        """
        测试同订单汇聚约束：
        同一订单的货物必须去相同的 L1（即使有更近的备选 L1）
        当第一票货物选了 L1 后，同订单其他货物也被强制走相同的 L1
        """
        # 给 O001 添加第二个货物，放在更靠近 SO002 的位置
        from models.goods import Goods
        goods2 = Goods(
            goods_code="G001_B",
            goods_name="测试货物A2",
            goods_type="普通",
            weight=3.0,
            volume=0.1,
            node_id=test_nodes["SC002"].id,  # 放在长沙 SC002，离 SO002 更近
            order_id=test_orders["O001"].id,
            status="pending_pack",
        )
        db_session.add(goods2)
        db_session.commit()
        db_session.refresh(test_orders["O001"])

        result = global_schedule(
            order_codes=None,
            algorithm="traditional",
            db=db_session,
        )

        goods_schedules = result["goods_schedules"]

        # O001 有两个货物，但都在 SC001（遍历顺序先 G001）
        o001_goods = [gs for gs in goods_schedules if gs["order_code"] == "O001"]
        # 同订单货物必须走相同的 L1
        if len(o001_goods) >= 2:
            l1_set = set(gs["path"][1] for gs in o001_goods)
            assert len(l1_set) == 1, (
                f"同一订单 O001 的货物应汇聚到相同 L1，但实际使用了 {l1_set}"
            )

    @pytest.mark.unit
    def test_invalid_algorithm_raises_error(self, db_session):
        """测试非法 algorithm 参数抛出 ValueError"""
        with pytest.raises(ValueError, match="阶段3仅支持 traditional 算法"):
            global_schedule(order_codes=[], algorithm="deepseek", db=db_session)

    @pytest.mark.unit
    def test_no_pending_orders_raises_error(self, db_session):
        """测试没有 pending 订单时抛出 ValueError"""
        # 数据库中没有任何 pending 订单
        with pytest.raises(ValueError, match="没有找到符合条件的订单"):
            global_schedule(order_codes=None, algorithm="traditional", db=db_session)
