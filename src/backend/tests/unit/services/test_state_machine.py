"""
服务单元测试：state_machine（状态机服务）

测试目标：
- 全实体状态转换合法/非法参数化测试（策略1）
- update_batch_status() 的状态转换合法性校验
- update_orders_after_f007() 订单状态更新
- update_goods_after_f021() 货物状态更新
- mark_exception_statuses() 标记异常状态
- reset_goods_for_replan() 重置货物状态
- mark_old_entities_exception() 标记旧实体为异常
- mark_vehicle_exception() 标记车辆关联实体为异常
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers
from models.base import Base
from models.dispatch_batch import DispatchBatch
from services.state_machine import (
    update_batch_status,
    _validate,
    ORDER_TRANSITIONS,
    GOODS_TRANSITIONS,
    PACKAGE_TRANSITIONS,
    BATCH_TRANSITIONS,
    SCHEDULE_TRANSITIONS,
    VEHICLE_TRANSITIONS,
    DRIVER_TRANSITIONS,
)


# ── 测试辅助函数 ──────────────────────────────────────────

def _create_test_node(db, code="N001", name="测试节点", node_type="sorting_center"):
    """创建测试 Node（许多 ORM 模型依赖 FK 到 nodes）"""
    from models.node import Node
    node = Node(
        node_code=code,
        name=name,
        location="武汉市洪山区",
        latitude=30.5,
        longitude=114.3,
        node_type=node_type,
    )
    db.add(node)
    db.flush()
    return node


def _create_test_order(db, code="O001", status="pending", dest_node=None):
    """创建测试 Order（依赖 dest_node_id 外键）"""
    from models.order import Order
    if dest_node is None:
        dest_node = _create_test_node(db, code="N_DEST")
    order = Order(
        order_code=code,
        destination_node_id=dest_node.id,
        time_window="08:00-18:00",
        status=status,
    )
    db.add(order)
    db.flush()
    return order


def _create_test_schedule(db, code="GS001", order_codes=None):
    """创建测试 GlobalSchedule（依赖 goods_schedules NOT NULL）"""
    from models.global_schedule import GlobalSchedule
    if order_codes is None:
        order_codes = ["O001"]
    schedule = GlobalSchedule(
        schedule_code=code,
        order_codes=order_codes,
        goods_schedules=[{"goods_code": "G001", "order_code": order_codes[0], "path": ["SC001", "SO001", "SO027"]}],
        total_distance=100.0,
        total_time=2.5,
        total_goods=1,
        score=50.0,
    )
    db.add(schedule)
    db.flush()
    return schedule


def _create_test_goods(db, code="G001", status="pending_pack", order_id=None, node=None):
    """创建测试 Goods（依赖 node_id 和 order_id 外键）"""
    from models.goods import Goods
    if node is None:
        node = _create_test_node(db, code="N_G001")
    if order_id is None:
        order = _create_test_order(db, code="O_G001")
        order_id = order.id
    goods = Goods(
        goods_code=code,
        goods_name="测试货物",
        goods_type="普通货物",
        weight=10.0,
        volume=1.0,
        node_id=node.id,
        order_id=order_id,
        status=status,
    )
    db.add(goods)
    db.flush()
    return goods


# ── 测试类 ─────────────────────────────────────────────────

class TestUpdateBatchStatus:
    """测试 update_batch_status() 状态转换合法性校验"""

    @pytest.fixture(autouse=True)
    def setup(self, request):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.db = Session()
        request.addfinalizer(lambda: (self.db.close(), Base.metadata.drop_all(engine)))
        self.batch = DispatchBatch(
            batch_code="BATCH001",
            global_schedule_id=1,
            status="pending",
        )
        self.db.add(self.batch)
        self.db.flush()

    def test_valid_pending_to_l0_l1_done(self):
        update_batch_status(self.db, self.batch, "l0_l1_done")
        assert self.batch.status == "l0_l1_done"

    def test_valid_pending_to_failed(self):
        update_batch_status(self.db, self.batch, "failed")
        assert self.batch.status == "failed"

    def test_valid_pending_to_completed(self):
        """demo_mode 直通场景：pending → completed"""
        update_batch_status(self.db, self.batch, "completed")
        assert self.batch.status == "completed"

    def test_valid_l0_l1_done_to_completed(self):
        self.batch.status = "l0_l1_done"
        self.db.flush()
        update_batch_status(self.db, self.batch, "completed")
        assert self.batch.status == "completed"

    def test_valid_l0_l1_done_to_failed(self):
        self.batch.status = "l0_l1_done"
        self.db.flush()
        update_batch_status(self.db, self.batch, "failed")
        assert self.batch.status == "failed"

    def test_idempotent_l0_l1_done(self):
        """同状态幂等：l0_l1_done → l0_l1_done 不报错"""
        self.batch.status = "l0_l1_done"
        self.db.flush()
        update_batch_status(self.db, self.batch, "l0_l1_done")
        assert self.batch.status == "l0_l1_done"

    def test_idempotent_completed(self):
        """同状态幂等：completed → completed 不报错"""
        self.batch.status = "completed"
        self.db.flush()
        update_batch_status(self.db, self.batch, "completed")
        assert self.batch.status == "completed"

    def test_invalid_completed_to_pending(self):
        self.batch.status = "completed"
        self.db.flush()
        with pytest.raises(ValueError, match="非法批次状态转换"):
            update_batch_status(self.db, self.batch, "pending")

    def test_invalid_completed_to_l0_l1_done(self):
        self.batch.status = "completed"
        self.db.flush()
        with pytest.raises(ValueError, match="非法批次状态转换"):
            update_batch_status(self.db, self.batch, "l0_l1_done")

    def test_invalid_failed_to_pending(self):
        self.batch.status = "failed"
        self.db.flush()
        with pytest.raises(ValueError, match="非法批次状态转换"):
            update_batch_status(self.db, self.batch, "pending")

    def test_invalid_failed_to_completed(self):
        self.batch.status = "failed"
        self.db.flush()
        with pytest.raises(ValueError, match="非法批次状态转换"):
            update_batch_status(self.db, self.batch, "completed")

    def test_force_update_bypasses_validation(self):
        self.batch.status = "completed"
        self.db.flush()
        update_batch_status(self.db, self.batch, "pending", force=True)
        assert self.batch.status == "pending"


class TestUpdateOrdersAfterF007:
    """测试 update_orders_after_f007() 订单状态更新"""

    @pytest.fixture(autouse=True)
    def setup(self, request):
        from models.order import Order
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.db = Session()
        request.addfinalizer(lambda: (self.db.close(), Base.metadata.drop_all(engine)))
        self.node = _create_test_node(self.db)

    def test_pending_to_delivering(self):
        from models.order import Order
        from services.state_machine import update_orders_after_f007
        order = Order(order_code="O001", destination_node_id=self.node.id, time_window="08:00-18:00", status="pending")
        self.db.add(order)
        self.db.flush()
        update_orders_after_f007(self.db, ["O001"])
        assert order.status == "delivering"

    def test_exception_to_delivering(self):
        from models.order import Order
        from services.state_machine import update_orders_after_f007
        order = Order(order_code="O002", destination_node_id=self.node.id, time_window="08:00-18:00", status="exception")
        self.db.add(order)
        self.db.flush()
        update_orders_after_f007(self.db, ["O002"])
        assert order.status == "delivering"

    def test_completed_no_change(self):
        from models.order import Order
        from services.state_machine import update_orders_after_f007
        order = Order(order_code="O003", destination_node_id=self.node.id, time_window="08:00-18:00", status="completed")
        self.db.add(order)
        self.db.flush()
        update_orders_after_f007(self.db, ["O003"])
        assert order.status == "completed"


class TestUpdateGoodsAfterF021:
    """测试 update_goods_after_f021() 货物状态更新"""

    @pytest.fixture(autouse=True)
    def setup(self, request):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.db = Session()
        request.addfinalizer(lambda: (self.db.close(), Base.metadata.drop_all(engine)))
        self.node = _create_test_node(self.db)
        self.order = _create_test_order(self.db, code="O001", dest_node=self.node)
        self.schedule = _create_test_schedule(self.db, code="GS001", order_codes=["O001"])

    def test_pending_pack_to_packed(self):
        from models.goods import Goods
        from services.state_machine import update_goods_after_f021
        goods = Goods(goods_code="G001", goods_name="测试", goods_type="普通", weight=10.0, volume=1.0,
                       node_id=self.node.id, order_id=self.order.id, status="pending_pack")
        self.db.add(goods)
        self.db.flush()
        update_goods_after_f021(self.db, self.schedule.id, is_replan=False)
        assert goods.status == "packed"

    def test_exception_to_packed(self):
        from models.goods import Goods
        from services.state_machine import update_goods_after_f021
        goods = Goods(goods_code="G002", goods_name="测试", goods_type="普通", weight=10.0, volume=1.0,
                       node_id=self.node.id, order_id=self.order.id, status="exception")
        self.db.add(goods)
        self.db.flush()
        update_goods_after_f021(self.db, self.schedule.id, is_replan=True)
        assert goods.status == "packed"


class TestMarkExceptionStatuses:
    """测试 mark_exception_statuses() 异常状态标记"""

    @pytest.fixture(autouse=True)
    def setup(self, request):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.db = Session()
        request.addfinalizer(lambda: (self.db.close(), Base.metadata.drop_all(engine)))
        self.node = _create_test_node(self.db)
        self.order = _create_test_order(self.db, code="O001", dest_node=self.node, status="delivering")
        self.schedule = _create_test_schedule(self.db, code="GS002", order_codes=["O001"])

    def test_mark_orders_exception(self):
        from services.state_machine import mark_exception_statuses
        mark_exception_statuses(self.db, "GS002")
        assert self.order.status == "exception"

    def test_mark_goods_exception(self):
        from services.state_machine import mark_exception_statuses
        goods = _create_test_goods(self.db, code="G001", status="packed", order_id=self.order.id, node=self.node)
        mark_exception_statuses(self.db, "GS002")
        assert goods.status == "exception"


class TestResetGoodsForReplan:
    """测试 reset_goods_for_replan() 重规划重置"""

    @pytest.fixture(autouse=True)
    def setup(self, request):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.db = Session()
        request.addfinalizer(lambda: (self.db.close(), Base.metadata.drop_all(engine)))
        self.node = _create_test_node(self.db)
        self.order = _create_test_order(self.db, code="O001", dest_node=self.node, status="delivering")

    def test_reset_packed_goods(self):
        from services.state_machine import reset_goods_for_replan
        goods = _create_test_goods(self.db, code="G001", status="packed", order_id=self.order.id, node=self.node)
        reset_goods_for_replan(self.db, ["O001"])
        assert goods.status == "pending_pack"

    def test_reset_delivered_goods(self):
        from services.state_machine import reset_goods_for_replan
        goods = _create_test_goods(self.db, code="G002", status="delivered", order_id=self.order.id, node=self.node)
        reset_goods_for_replan(self.db, ["O001"])
        assert goods.status == "pending_pack"


# ══════════════════════════════════════════════════════════════════
# 策略1：全实体状态转换参数化测试
# ══════════════════════════════════════════════════════════════════

# 所有合法转换（current_status, target_status, entity_name）
ALL_VALID_TRANSITIONS = [
    # ── Order ──
    ("pending", "delivering", "订单"),
    ("pending", "exception", "订单"),
    ("delivering", "completed", "订单"),
    ("delivering", "exception", "订单"),
    ("exception", "delivering", "订单"),
    # ── Goods ──
    ("pending_pack", "packed", "货物"),
    ("pending_pack", "exception", "货物"),
    ("packed", "in_transit", "货物"),
    ("packed", "exception", "货物"),
    ("in_transit", "pending_pack", "货物"),
    ("in_transit", "delivered", "货物"),
    ("in_transit", "exception", "货物"),
    ("exception", "pending_pack", "货物"),
    ("exception", "packed", "货物"),
    ("exception", "in_transit", "货物"),
    # ── Package ──
    ("pending_pack", "packed", "包裹"),
    ("pending_pack", "exception", "包裹"),
    ("packed", "in_transit", "包裹"),
    ("packed", "exception", "包裹"),
    ("in_transit", "delivered", "包裹"),
    ("in_transit", "exception", "包裹"),
    ("delivered", "exception", "包裹"),   # Bug1 修复后
    ("exception", "pending_pack", "包裹"),
    # ── Batch ──
    ("pending", "l0_l1_done", "批次"),
    ("pending", "completed", "批次"),
    ("pending", "failed", "批次"),
    ("l0_l1_done", "completed", "批次"),
    ("l0_l1_done", "failed", "批次"),
    # ── Schedule ──
    ("draft", "active", "全局调度方案"),
    # ── Vehicle ──
    ("idle", "delivering", "车辆"),
    ("idle", "maintenance", "车辆"),
    ("idle", "disabled", "车辆"),
    ("delivering", "idle", "车辆"),
    ("delivering", "disabled", "车辆"),
    ("maintenance", "idle", "车辆"),
    # ── Driver ──
    ("idle", "busy", "司机"),
    ("busy", "idle", "司机"),
]

# 关键非法转换（应触发 ValueError）
ALL_INVALID_TRANSITIONS = [
    # ── Order ──
    ("completed", "delivering", "订单"),
    ("completed", "exception", "订单"),
    ("delivering", "pending", "订单"),
    # ── Goods ──
    ("delivered", "in_transit", "货物"),
    ("delivered", "pending_pack", "货物"),
    ("packed", "delivered", "货物"),       # 必须经 in_transit
    # ── Package ──
    ("delivered", "in_transit", "包裹"),   # 不可逆
    ("delivered", "packed", "包裹"),        # 不可逆
    ("packed", "delivered", "包裹"),        # 必须经 in_transit
    ("completed", "delivering", "批次"),    # 该实体无 completed
    # ── Batch ──
    ("completed", "pending", "批次"),
    ("failed", "pending", "批次"),
    ("failed", "l0_l1_done", "批次"),
    # ── Schedule ──
    ("active", "draft", "全局调度方案"),
    # ── Vehicle ──
    ("disabled", "idle", "车辆"),
    ("disabled", "delivering", "车辆"),
    # ── Driver ──
    ("busy", "delivering", "司机"),
]

# 状态名 → TRANSITIONS 字典映射
ENTITY_LOOKUP = {
    "订单":     ORDER_TRANSITIONS,
    "货物":     GOODS_TRANSITIONS,
    "包裹":     PACKAGE_TRANSITIONS,
    "批次":     BATCH_TRANSITIONS,
    "全局调度方案": SCHEDULE_TRANSITIONS,
    "车辆":     VEHICLE_TRANSITIONS,
    "司机":     DRIVER_TRANSITIONS,
}


class TestAllValidTransitions:
    """参数化测试：所有合法状态转换（不抛异常）"""

    @pytest.mark.parametrize("current,target,entity", ALL_VALID_TRANSITIONS)
    def test_valid_transition_does_not_raise(self, current, target, entity):
        """每条合法转换应被 _validate 接受"""
        transitions = ENTITY_LOOKUP[entity]
        try:
            _validate(transitions, current, target, entity)
        except ValueError as e:
            pytest.fail(f"合法转换 {current}→{target} ({entity}) 意外失败: {e}")

    @pytest.mark.parametrize("current,target,entity", ALL_VALID_TRANSITIONS)
    def test_idempotent_same_state(self, current, target, entity):
        """同状态幂等：current == target 时 _validate 应直接返回"""
        # 选一个合法目标做幂等测试（用 current 自身）
        transitions = ENTITY_LOOKUP[entity]
        _validate(transitions, current, current, entity)  # 不应抛异常


class TestAllInvalidTransitions:
    """参数化测试：关键非法状态转换（应抛 ValueError）"""

    @pytest.mark.parametrize("current,target,entity", ALL_INVALID_TRANSITIONS)
    def test_invalid_transition_raises(self, current, target, entity):
        """每条非法转换应触发 ValueError"""
        transitions = ENTITY_LOOKUP[entity]
        with pytest.raises(ValueError, match=f"非法{entity}状态转换"):
            _validate(transitions, current, target, entity)


class TestTransitionMapCompleteness:
    """验证 TRANSITIONS 字典的内部一致性"""

    def test_all_entities_have_transitions(self):
        """每个实体都有对应的转换映射"""
        for entity, transitions in ENTITY_LOOKUP.items():
            assert isinstance(transitions, dict), f"{entity} 转换映射不是 dict"
            assert len(transitions) > 0, f"{entity} 转换映射为空"

    def test_no_self_loop_needed_in_allowed_list(self):
        """同状态转换由 _validate 幂等处理，不需要显式列出 current→current"""
        for entity, transitions in ENTITY_LOOKUP.items():
            for current, allowed in transitions.items():
                assert current not in allowed, \
                    f"{entity}.{current} 的允许列表中不应包含自身（幂等由 _validate 处理）"

    def test_package_delivered_can_go_to_exception(self):
        """Bug1 回归：delivered → exception 必须在 PACKAGE_TRANSITIONS 中"""
        assert "exception" in PACKAGE_TRANSITIONS["delivered"], \
            "BUG回归: PACKAGE_TRANSITIONS[delivered] 缺少 'exception' 目标"
