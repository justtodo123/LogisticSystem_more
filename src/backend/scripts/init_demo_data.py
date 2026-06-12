"""
演示数据初始化脚本
依据架构设计说明书 §2 Q15：按用户→节点→车辆→司机→货物→订单顺序初始化
"""
from sqlalchemy.orm import Session
from datetime import datetime
import bcrypt
import random
import math

from models.user import User
from models.node import Node
from models.storage_center import StorageCenter
from models.sorting_center import SortingCenter
from models.vehicle import Vehicle
from models.driver import Driver
from models.order import Order
from models.goods import Goods


async def init_demo_data(db: Session):
    """初始化演示数据"""
    # 1. 创建用户（dispatcher、manager）
    await _create_users(db)
    
    # 2. 创建存储中心（5个）
    await _create_storage_centers(db)
    
    # 3. 创建1级分拣中心（2个）
    await _create_sorting_centers_l1(db)
    
    # 4. 创建0级分拣中心（50个）
    await _create_sorting_centers_l2(db)
    
    # 5. 创建车辆（70辆）
    await _create_vehicles(db)
    
    # 6. 创建司机（70名）
    await _create_drivers(db)
    
    # 7. 创建订单（50条）+ 货物（每单2-7个）
    await _create_orders_and_goods(db)
    
    print("演示数据初始化完成")


async def _create_users(db: Session):
    """创建用户（dispatcher、manager）"""
    # 创建dispatcher用户
    dispatcher = db.query(User).filter(User.username == "dispatcher").first()
    if not dispatcher:
        password_hash = bcrypt.hashpw("123456".encode(), bcrypt.gensalt()).decode()
        dispatcher = User(
            username="dispatcher",
            password_hash=password_hash,
            role="dispatcher"
        )
        db.add(dispatcher)
    
    # 创建manager用户
    manager = db.query(User).filter(User.username == "manager").first()
    if not manager:
        password_hash = bcrypt.hashpw("123456".encode(), bcrypt.gensalt()).decode()
        manager = User(
            username="manager",
            password_hash=password_hash,
            role="manager"
        )
        db.add(manager)
    
    db.commit()
    print("用户创建完成")


async def _create_storage_centers(db: Session):
    """创建存储中心（5个）"""
    # 5个存储中心分布在城市四周边缘
    centers = [
        ("SC001", "武汉存储中心(东)", 30.5, 114.4, 1000, 0),
        ("SC002", "武汉存储中心(南)", 30.4, 114.3, 1000, 0),
        ("SC003", "武汉存储中心(西)", 30.5, 114.2, 1000, 0),
        ("SC004", "武汉存储中心(北)", 30.6, 114.3, 1000, 0),
        ("SC005", "武汉存储中心(中)", 30.5, 114.3, 1000, 0),
    ]
    
    for code, name, lat, lng, capacity, inventory in centers:
        node = db.query(Node).filter(Node.node_code == code).first()
        if not node:
            node = Node(
                node_code=code,
                name=name,
                location=f"{lat}, {lng}",
                latitude=lat,
                longitude=lng,
                node_type="storage_center"
            )
            db.add(node)
            db.flush()
            
            storage_center = StorageCenter(
                node_id=node.id,
                capacity=capacity,
                inventory=inventory
            )
            db.add(storage_center)
    
    db.commit()
    print("存储中心创建完成")


async def _create_sorting_centers_l1(db: Session):
    """创建1级分拣中心（2个）"""
    # 2个1级分拣中心分布在城市南北两端
    centers = [
        ("L1001", "武汉1级分拣中心(北)", 30.55, 114.3, 0, 500, 24),
        ("L1002", "武汉1级分拣中心(南)", 30.45, 114.3, 0, 500, 24),
    ]
    
    for code, name, lat, lng, level, capacity, max_storage_time in centers:
        node = db.query(Node).filter(Node.node_code == code).first()
        if not node:
            node = Node(
                node_code=code,
                name=name,
                location=f"{lat}, {lng}",
                latitude=lat,
                longitude=lng,
                node_type="sorting_center"
            )
            db.add(node)
            db.flush()
            
            sorting_center = SortingCenter(
                node_id=node.id,
                level=level,
                capacity=capacity,
                max_storage_time=max_storage_time
            )
            db.add(sorting_center)
    
    db.commit()
    print("1级分拣中心创建完成")


async def _create_sorting_centers_l2(db: Session):
    """创建0级分拣中心（50个）"""
    # 50个0级分拣中心均匀分布在城市中
    centers = []
    for i in range(50):
        angle = 2 * math.pi * i / 50
        radius = random.uniform(0.01, 0.08)
        lat = 30.5 + radius * math.sin(angle)
        lng = 114.3 + radius * math.cos(angle)
        code = f"L2{i+1:03d}"
        name = f"武汉0级分拣中心({i+1})"
        centers.append((code, name, lat, lng, 1, None, None))
    
    for code, name, lat, lng, level, capacity, max_storage_time in centers:
        node = db.query(Node).filter(Node.node_code == code).first()
        if not node:
            node = Node(
                node_code=code,
                name=name,
                location=f"{lat}, {lng}",
                latitude=lat,
                longitude=lng,
                node_type="sorting_center"
            )
            db.add(node)
            db.flush()
            
            sorting_center = SortingCenter(
                node_id=node.id,
                level=level,
                capacity=capacity,
                max_storage_time=max_storage_time
            )
            db.add(sorting_center)
    
    db.commit()
    print("0级分拣中心创建完成")


async def _create_vehicles(db: Session):
    """创建车辆（70辆）"""
    # 7个节点（5个存储中心+2个1级分拣中心）× 10辆车
    node_codes = ["SC001", "SC002", "SC003", "SC004", "SC005", "L1001", "L1002"]
    
    vehicle_count = 0
    for node_code in node_codes:
        node = db.query(Node).filter(Node.node_code == node_code).first()
        if not node:
            continue
        
        for i in range(10):
            vehicle_code = f"VEH{node_code}{i+1:02d}"
            existing = db.query(Vehicle).filter(Vehicle.vehicle_code == vehicle_code).first()
            if not existing:
                vehicle = Vehicle(
                    vehicle_code=vehicle_code,
                    model="东风卡车",
                    capacity=5.0,
                    energy_type="fuel",
                    vehicle_type="normal",
                    capability_tags=None,
                    last_arrived_node_id=node.id,
                    status="idle",
                    node_id=node.id
                )
                db.add(vehicle)
                vehicle_count += 1
    
    db.commit()
    print(f"车辆创建完成，共{vehicle_count}辆")


async def _create_drivers(db: Session):
    """创建司机（70名）"""
    # 7个节点（5个存储中心+2个1级分拣中心）× 10名司机
    node_codes = ["SC001", "SC002", "SC003", "SC004", "SC005", "L1001", "L1002"]
    
    driver_count = 0
    for node_code in node_codes:
        node = db.query(Node).filter(Node.node_code == node_code).first()
        if not node:
            continue
        
        for i in range(10):
            driver_code = f"DRV{node_code}{i+1:02d}"
            existing = db.query(Driver).filter(Driver.driver_code == driver_code).first()
            if not existing:
                driver = Driver(
                    driver_code=driver_code,
                    name=f"司机{node_code}-{i+1}",
                    phone=f"1380000{i+1:04d}",
                    license_type="C1",
                    shift="day",
                    node_id=node.id,
                    status="idle"
                )
                db.add(driver)
                driver_count += 1
    
    db.commit()
    print(f"司机创建完成，共{driver_count}名")


async def _create_orders_and_goods(db: Session):
    """创建订单（50条）+ 货物（每单2-7个）"""
    # 获取所有0级分拣中心作为目的地
    l2_nodes = db.query(Node).join(SortingCenter).filter(SortingCenter.level == 1).all()
    
    order_count = 0
    goods_count = 0
    
    for i in range(50):
        # 随机选择目的地节点
        dest_node = random.choice(l2_nodes)
        
        # 创建订单
        order_code = f"O{i+1:03d}"
        existing = db.query(Order).filter(Order.order_code == order_code).first()
        if not existing:
            order = Order(
                order_code=order_code,
                destination_node_id=dest_node.id,
                time_window="9:00-18:00",
                status="pending"
            )
            db.add(order)
            db.flush()
            order_count += 1
            
            # 创建货物（每单2-7个）
            num_goods = random.randint(2, 7)
            for j in range(num_goods):
                goods_code = f"G{order_code}_{j+1}"
                goods = Goods(
                    goods_code=goods_code,
                    order_id=order.id,
                    goods_name=f"货物{order_code}-{j+1}",
                    goods_type=random.choice(["电子产品", "服装", "食品", "日用品"]),
                    weight=random.uniform(0.5, 10.0),
                    volume=random.uniform(0.1, 2.0),
                    node_id=dest_node.id,
                    status="pending_pack"
                )
                db.add(goods)
                goods_count += 1
    
    db.commit()
    print(f"订单创建完成，共{order_count}个订单，{goods_count}个货物")


if __name__ == "__main__":
    # 命令行入口
    from config.database import SessionLocal
    db = SessionLocal()
    import asyncio
    asyncio.run(init_demo_data(db))
    db.close()
