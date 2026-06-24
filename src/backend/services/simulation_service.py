"""
模拟送达服务

编排模拟送达的完整流程。
单事务保证原子性：packages/goods/vehicles/drivers/orders 状态更新全部成功或全部回滚。

功能边界：
- 仅负责状态流转，不负责调度编排
- 不自动触发重新打包（F021）、F005调度、或未分配包裹重调度
- 这些操作由用户通过 /api/schedule/* 接口手动触发
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from models.package import Package
from models.goods import Goods
from models.order import Order
from models.vehicle import Vehicle
from models.driver import Driver
from models.node_dispatch import NodeDispatch
from models.dispatch_batch import DispatchBatch
from utils.response import success_response, error_response
from services.state_machine import (
    update_batch_status,
    transition_package_status,
    transition_vehicle_status,
    transition_driver_status,
    check_and_update_order_status,
)


class SimulationService:
    """模拟送达服务"""

    @staticmethod
    async def deliver_packages(
        vehicle_code: Optional[str],
        package_code: Optional[str],
        db: Session,
    ) -> Dict[str, Any]:
        """
        模拟送达，驱动状态流转
        
        流程：
        1. 根据参数查询要送达的包裹
        2. 检查包裹状态（必须 in_transit）
        3. 更新包裹状态：in_transit → delivered
        4. 更新货物状态（根据是否送达目的地）
        5. 检查车辆状态（所有包裹送达后 vehicle → idle）
        6. 检查司机状态（车辆 idle 后 driver → idle）
        7. 检查订单状态（所有货物送达后 order → completed）
        8. 返回结果
        
        Args:
            vehicle_code: 车辆编号（可选）
            package_code: 包裹编号（可选）
            db: 数据库会话
            
        Returns:
            统一响应格式 dict
        """
        try:
            # 1. 根据参数查询要送达的包裹
            query = db.query(Package).filter(Package.status == "in_transit")
            
            if package_code:
                # 按 package_code 查询
                query = query.filter(Package.package_code == package_code)
            elif vehicle_code:
                # 按 vehicle_code 查询（需要 JOIN node_dispatches 和 vehicles）
                query = query.join(NodeDispatch, Package.dispatch_id == NodeDispatch.id)
                query = query.join(Vehicle, NodeDispatch.vehicle_id == Vehicle.id)
                query = query.filter(Vehicle.vehicle_code == vehicle_code)
            # 都不传：查询所有 in_transit 包裹（已在 filter 中）
            
            packages = query.all()
            
            if not packages:
                return error_response(code=40001, message="没有找到可送达的包裹")
            
            # 准备响应数据
            delivered_package_codes = []
            status_changed_goods_count = 0
            updated_order_ids = set()
            level_info = {"l0_to_l1": 0, "l1_to_l2": 0}  # 层级信息：记录每种层级的送达数量
            
            # 2. 处理每个包裹
            for package in packages:
                # 检查包裹状态（必须 in_transit）
                if package.status != "in_transit":
                    return error_response(
                        code=40001,
                        message=f"包裹 {package.package_code} 状态不是 in_transit，无法送达"
                    )
                
                # 3. 更新包裹状态：in_transit → delivered
                transition_package_status(db, package, "delivered")
                delivered_package_codes.append(package.package_code)
                
                # 4. 更新货物状态（根据是否送达目的地）
                goods_items = package.goods_items  # JSON: [{"goods_code": "G001", "order_code": "O001"}]
                # 解析 JSON（如果是字符串）
                if isinstance(goods_items, str):
                    import json
                    goods_items = json.loads(goods_items)
                for item in goods_items:
                    goods_code = item["goods_code"]
                    order_code = item["order_code"]
                    
                    # 查询货物
                    goods = db.query(Goods).filter(Goods.goods_code == goods_code).first()
                    if not goods:
                        continue
                    
                    # 查询订单
                    order = db.query(Order).filter(Order.order_code == order_code).first()
                    if not order:
                        continue
                    
                    # 更新货物位置：goods.node_id = package.to_node_id
                    goods.node_id = package.to_node_id
                    
                    # P1-3 改造：goods.status 保持 in_transit（不改为 packed）
                    # 仅更新 node_id，状态不变，等待 confirm-arrival 确认
                    # 移除：goods.status = "packed"  # 不直接改为 packed
                    # 移除：批量激活下游包裹的逻辑
                    
                    # 记录层级信息（用于统计）
                    if order.destination_node_id == package.to_node_id:
                        level_info["l1_to_l2"] += 1
                    else:
                        level_info["l0_to_l1"] += 1
                    
                    status_changed_goods_count += 1
                    updated_order_ids.add(order.id)
            
            # 5. 检查车辆状态（所有包裹送达后 vehicle → idle）
            # 收集所有受影响的车辆 ID
            vehicle_ids = set()
            for package in packages:
                if package.dispatch_id:
                    dispatch = db.query(NodeDispatch).filter(NodeDispatch.id == package.dispatch_id).first()
                    if dispatch:
                        vehicle_ids.add(dispatch.vehicle_id)
            
            for vehicle_id in vehicle_ids:
                # 查询该车辆的所有包裹（包括已更新的）
                db.flush()  # 确保能看到最新的包裹状态
                vehicle_packages = db.query(Package).join(
                    NodeDispatch, Package.dispatch_id == NodeDispatch.id
                ).filter(
                    NodeDispatch.vehicle_id == vehicle_id,
                    Package.status == "in_transit"
                ).all()
                
                if not vehicle_packages:
                    # 所有包裹都已送达，车辆变为 idle
                    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
                    if vehicle and vehicle.status == "delivering":
                        transition_vehicle_status(db, vehicle, "idle")
                        
                        # 6. 检查司机状态（车辆 idle 后 driver → idle）
                        # 查询该车辆的司机（从 node_dispatches 中找）
                        dispatch = db.query(NodeDispatch).filter(
                            NodeDispatch.vehicle_id == vehicle_id
                        ).order_by(NodeDispatch.id.desc()).first()
                        if dispatch and dispatch.driver_id:
                            driver = db.query(Driver).filter(Driver.id == dispatch.driver_id).first()
                            if driver and driver.status == "busy":
                                transition_driver_status(db, driver, "idle")
            
            # 7. 检查订单状态（所有货物送达后 order → completed）
            delivered_order_codes = []
            for order_id in updated_order_ids:
                order = db.query(Order).filter(Order.id == order_id).first()
                if not order:
                    continue
                
                # 查询该订单的所有货物
                all_goods = db.query(Goods).filter(Goods.order_id == order_id).all()
                
                # 检查是否所有货物都已 delivered
                all_delivered = all(g.status == "delivered" for g in all_goods)
                
                if all_delivered and order.status == "delivering":
                    check_and_update_order_status(db, order.order_code)
                    delivered_order_codes.append(order.order_code)
            
            # 8. 更新批次状态（第一次送达完成后）
            SimulationService._update_batch_status_after_delivery(db, packages)
            
            # 9. 提交事务（确保所有状态更新被持久化）
            db.commit()
            
            # 10. 返回结果
            return success_response(data={
                "delivered_package_codes": delivered_package_codes,
                "status_changed_goods_count": status_changed_goods_count,
                "updated_order_count": len(delivered_order_codes),
                "delivered_order_codes": delivered_order_codes,
                "level_info": level_info  # 层级信息：l0_to_l1 / l1_to_l2
            })
            
        except Exception as e:
            db.rollback()
            return error_response(code=40001, message=f"模拟送达失败：{str(e)}")

    @staticmethod
    def _update_batch_status_after_delivery(db: Session, packages: List[Package]) -> None:
        """
        更新批次状态为 l0_l1_done（第一次送达完成后）
        
        Args:
            db: 数据库会话
            packages: 已送达的包裹列表
        """
        # 收集所有受影响的批次ID
        batch_ids = set()
        for pkg in packages:
            if pkg.dispatch_id:
                dispatch = db.query(NodeDispatch).filter(NodeDispatch.id == pkg.dispatch_id).first()
                if dispatch and dispatch.dispatch_batch_id:
                    batch_ids.add(dispatch.dispatch_batch_id)
        
        # 更新批次状态
        for batch_id in batch_ids:
            batch = db.query(DispatchBatch).filter(DispatchBatch.id == batch_id).first()
            if batch and batch.status in ['pending', 'l0_l1_done']:
                update_batch_status(db, batch, 'l0_l1_done')
        
        db.flush()


