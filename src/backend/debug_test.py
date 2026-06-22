"""调试脚本：直接测试状态重置逻辑"""
import sys
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
    # 1. 检查测试数据是否存在
    order = db.query(Order).filter(Order.order_code == "O_TEST_RESET_002").first()
    print(f"1. 订单存在: {order is not None}")
    if order:
        print(f"   订单状态: {order.status}")
    
    goods = db.query(Goods).filter(Goods.goods_code == "G_TEST_RESET_002").first()
    print(f"2. 货物存在: {goods is not None}")
    if goods:
        print(f"   货物状态: {goods.status}")
    
    package = db.query(Package).filter(Package.package_code == "PKG_TEST_RESET_002").first()
    print(f"3. 包裹存在: {package is not None}")
    if package:
        print(f"   包裹状态: {package.status}")
    
    schedule = db.query(GlobalSchedule).filter(GlobalSchedule.schedule_code == "GS_TEST_RESET_002").first()
    print(f"4. 调度方案存在: {schedule is not None}")
    if schedule:
        print(f"   调度方案ID: {schedule.id}")
        print(f"   订单列表: {schedule.order_codes}")
    
    # 2. 测试创建异常事件
    if schedule and order and order.status == "delivering":
        print(f"\n5. 开始测试状态重置...")
        data = CreateExceptionEventRequest(
            exception_type="node",
            exception_subtype="capacity_limit",
            target_type="node",
            target_code="SC001",
            severity="medium",
            recommended_action="redispatch",
            related_schedule_code="GS_TEST_RESET_002",
            description="测试状态重置"
        )
        
        import asyncio
        result = asyncio.run(ExceptionService.create_exception_event(db=db, data=data))
        print(f"   服务层响应: {result}")
        
        # 3. 检查状态
        db.refresh(order)
        db.refresh(goods)
        db.refresh(package)
        print(f"\n6. 状态检查结果:")
        print(f"   订单状态: {order.status}")
        print(f"   货物状态: {goods.status}")
        print(f"   包裹状态: {package.status}")
    else:
        print(f"\n跳过测试：调度方案或订单不存在，或订单状态不是delivering")
        
finally:
    db.close()
