"""
模拟送达服务

编排模拟送达的完整流程。
单事务保证原子性：packages/goods/vehicles/drivers/orders 状态更新全部成功或全部回滚。
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from models.package import Package
from models.goods import Goods
from models.order import Order
from models.vehicle import Vehicle
from models.driver import Driver
from models.node_dispatch import NodeDispatch
from utils.response import success_response, error_response


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
            
            # 2. 处理每个包裹
            for package in packages:
                # 检查包裹状态（必须 in_transit）
                if package.status != "in_transit":
                    return error_response(
                        code=40001,
                        message=f"包裹 {package.package_code} 状态不是 in_transit，无法送达"
                    )
                
                # 3. 更新包裹状态：in_transit → delivered
                package.status = "delivered"
                delivered_package_codes.append(package.package_code)
                
                # 4. 更新货物状态（根据是否送达目的地）
                goods_items = package.goods_items  # JSON: [{"goods_code": "G001", "order_code": "O001"}]
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
                    
                    # 判断是否送达目的地
                    if goods.node_id == order.destination_node_id:
                        # 送达目的地 → delivered
                        goods.status = "delivered"
                    else:
                        # 中间节点 → pending_pack
                        goods.status = "pending_pack"
                    
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
                        vehicle.status = "idle"
                        
                        # 6. 检查司机状态（车辆 idle 后 driver → idle）
                        # 查询该车辆的司机（从 node_dispatches 中找）
                        dispatch = db.query(NodeDispatch).filter(
                            NodeDispatch.vehicle_id == vehicle_id
                        ).order_by(NodeDispatch.id.desc()).first()
                        if dispatch and dispatch.driver_id:
                            driver = db.query(Driver).filter(Driver.id == dispatch.driver_id).first()
                            if driver and driver.status == "busy":
                                driver.status = "idle"
            
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
                    order.status = "completed"
                    delivered_order_codes.append(order.order_code)
            
            # 8. 返回结果
            return success_response(data={
                "delivered_package_codes": delivered_package_codes,
                "status_changed_goods_count": status_changed_goods_count,
                "updated_order_count": len(delivered_order_codes),
                "delivered_order_codes": delivered_order_codes
            })
            
        except Exception as e:
            db.rollback()
            return error_response(code=40001, message=f"模拟送达失败：{str(e)}")
