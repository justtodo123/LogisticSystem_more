"""简化测试：直接测试状态重置逻辑"""
import sys
import asyncio
sys.path.insert(0, r"D:\Git Demo\LogisticSystem\src\backend")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.order import Order
from models.goods import Goods
from models.package import Package
from models.global_schedule import GlobalSchedule
from schemas.exception_event import CreateExceptionEventRequest
from services.exception_service import ExceptionService

# 创建数据库会话
engine = create_engine('sqlite:///D:/Git Demo/LogisticSystem/src/backend/data/logistics.db')
Session = sessionmaker(bind=engine)
db = Session()

try:
    # 1. 准备测试数据
    order = Order(
        order_code="O_TEST_SIMPLE_001",
        destination_node_id=1,
        time_window="09:00-18:00",
        status="delivering"  # 模拟已调度
    )
    db.add(order)
    db.flush()

    goods = Goods(
        goods_code="G_TEST_SIMPLE_001",
        goods_name="测试货物",
        goods_type="normal",
        weight=10.0,
        volume=1.0,
        node_id=1,
        order_id=order.id,
        status="packed"  # 模拟已打包
    )
    db.add(goods)
    db.flush()

    schedule = GlobalSchedule(
        schedule_code="GS_TEST_SIMPLE_001",
        order_codes=["O_TEST_SIMPLE_001"],
        goods_schedules=[{"goods_code": "G_TEST_SIMPLE_001", "order_code": "O_TEST_SIMPLE_001", "path": ["SC001", "SO001", "SO027"]}],
        total_distance=100.0,
        total_time=120.0,
        total_goods=1,
        score=100.0,
        algorithm_type="traditional",
        version=1,
        is_replan=False
    )
    db.add(schedule)
    db.flush()

    package = Package(
        package_code="PKG_TEST_SIMPLE_001",
        weight=10.0,
        volume=1.0,
        status="packed",
        from_node_id=1,
        to_node_id=2,
        goods_items=[{"goods_code": "G_TEST_SIMPLE_001", "order_code": "O_TEST_SIMPLE_001"}],
        schedule_id=schedule.id
    )
    db.add(package)
    db.commit()

    print("1. 测试数据已创建")
    print(f"   订单状态: {order.status}")
    print(f"   货物状态: {goods.status}")
    print(f"   包裹状态: {package.status}")

    # 2. 测试创建异常事件（应该重置状态）
    data = CreateExceptionEventRequest(
        exception_type="node",
        exception_subtype="capacity_limit",
        target_type="node",
        target_code="SC001",
        severity="medium",
        recommended_action="redispatch",
        related_schedule_code="GS_TEST_SIMPLE_001",
        description="测试状态重置"
    )

    result = asyncio.run(ExceptionService.create_exception_event(db=db, data=data))
    print(f"\n2. 服务层响应: {result}")

    # 3. 检查状态
    db.refresh(order)
    db.refresh(goods)
    db.refresh(package)

    print(f"\n3. 状态检查结果:")
    print(f"   订单状态: {order.status}")
    print(f"   货物状态: {goods.status}")
    print(f"   包裹状态: {package.status}")

    # 4. 验证
    assert order.status == "exception", f"订单状态应为 exception，实际为 {order.status}"
    assert goods.status == "exception", f"货物状态应为 exception，实际为 {goods.status}"
    assert package.status == "exception", f"包裹状态应为 exception，实际为 {package.status}"

    print("\n✅ 所有断言通过！状态重置逻辑正常工作")

    # 5. 清理测试数据
    db.delete(package)
    db.delete(schedule)
    db.delete(goods)
    db.delete(order)
    db.commit()
    print("✅ 测试数据已清理")

except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()

finally:
    db.close()
