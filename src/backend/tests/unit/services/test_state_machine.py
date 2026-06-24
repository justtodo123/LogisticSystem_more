"""
服务单元测试：state_machine（状态机服务）

测试目标：
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
