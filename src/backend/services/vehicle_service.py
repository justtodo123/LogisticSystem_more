from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from models.vehicle import Vehicle
from models.node import Node
from schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleResponse
from core.error_codes import (CODE_SUCCESS, CODE_INTERNAL_ERROR, CODE_CONFLICT,
                             CODE_NODE_NOT_FOUND, CODE_VEHICLE_NOT_FOUND,
                             CODE_VEHICLE_STATUS_NOT_ALLOWED)
from services.state_machine import transition_vehicle_status


class VehicleService:
    """车辆服务"""

    @staticmethod
    async def create_vehicle(vehicle_create: VehicleCreate, db: Session) -> Dict[str, Any]:
        """创建车辆"""
        try:
            # 1. 校验vehicle_code是否已存在
            existing = db.query(Vehicle).filter(Vehicle.vehicle_code == vehicle_create.vehicle_code).first()
            if existing:
                return {"code": CODE_CONFLICT, "message": "车辆编号已存在", "data": None}

            # 2. 校验node_code是否存在
            node = db.query(Node).filter(Node.node_code == vehicle_create.node_code).first()
            if not node:
                return {"code": CODE_NODE_NOT_FOUND, "message": "节点不存在", "data": None}

            # 3. 校验last_arrived_node_code是否存在
            last_arrived_node = db.query(Node).filter(Node.node_code == vehicle_create.last_arrived_node_code).first()
            if not last_arrived_node:
                return {"code": CODE_NODE_NOT_FOUND, "message": "最后到达节点不存在", "data": None}

            # 4. 创建Vehicle记录
            vehicle = Vehicle(
                vehicle_code=vehicle_create.vehicle_code,
                model=vehicle_create.model,
                capacity=vehicle_create.capacity,
                energy_type=vehicle_create.energy_type,
                vehicle_type=vehicle_create.vehicle_type or "normal",
                capability_tags=vehicle_create.capability_tags,
                last_arrived_node_id=last_arrived_node.id,
                status=vehicle_create.status or "idle",
                node_id=node.id
            )
            db.add(vehicle)
            db.commit()

            # 5. 返回响应
            return {
                "code": CODE_SUCCESS,
                "message": "success",
                "data": {
                    "vehicle_code": vehicle.vehicle_code,
                    "model": vehicle.model,
                    "capacity": float(vehicle.capacity),
                    "energy_type": vehicle.energy_type,
                    "vehicle_type": vehicle.vehicle_type,
                    "capability_tags": vehicle.capability_tags,
                    "last_arrived_node_code": last_arrived_node.node_code,
                    "last_arrived_node_name": last_arrived_node.name,
                    "status": vehicle.status,
                    "node_code": node.node_code,
                    "node_name": node.name,
                    "created_at": vehicle.created_at.isoformat(),
                    "updated_at": vehicle.updated_at.isoformat()
                }
            }
        except Exception as e:
            db.rollback()
            return {"code": CODE_INTERNAL_ERROR, "message": f"创建车辆失败: {str(e)}", "data": None}

    @staticmethod
    async def get_vehicles(page: int, page_size: int, status: str = None, 
                           node_code: str = None, db: Session = None) -> Dict[str, Any]:
        """获取车辆列表"""
        try:
            # 1. 构建查询
            query = db.query(Vehicle)
            if status:
                query = query.filter(Vehicle.status == status)
            if node_code:
                node = db.query(Node).filter(Node.node_code == node_code).first()
                if node:
                    query = query.filter(Vehicle.node_id == node.id)

            # 2. 分页
            total = query.count()
            vehicles = query.offset((page - 1) * page_size).limit(page_size).all()

            # 3. 构建响应
            items = []
            for vehicle in vehicles:
                node = db.query(Node).filter(Node.id == vehicle.node_id).first()
                last_arrived_node = db.query(Node).filter(Node.id == vehicle.last_arrived_node_id).first()
                items.append({
                    "vehicle_code": vehicle.vehicle_code,
                    "model": vehicle.model,
                    "capacity": float(vehicle.capacity),
                    "energy_type": vehicle.energy_type,
                    "vehicle_type": vehicle.vehicle_type,
                    "capability_tags": vehicle.capability_tags,
                    "last_arrived_node_code": last_arrived_node.node_code if last_arrived_node else "",
                    "last_arrived_node_name": last_arrived_node.name if last_arrived_node else "",
                    "status": vehicle.status,
                    "node_code": node.node_code if node else "",
                    "node_name": node.name if node else "",
                    "created_at": vehicle.created_at.isoformat(),
                    "updated_at": vehicle.updated_at.isoformat()
                })

            return {
                "code": CODE_SUCCESS,
                "message": "success",
                "data": {
                    "items": items,
                    "total": total,
                    "page": page,
                    "page_size": page_size
                }
            }
        except Exception as e:
            return {"code": CODE_INTERNAL_ERROR, "message": f"获取车辆列表失败: {str(e)}", "data": None}

    @staticmethod
    async def get_vehicle(vehicle_code: str, db: Session) -> Dict[str, Any]:
        """获取车辆详情"""
        try:
            # 1. 查询Vehicle
            vehicle = db.query(Vehicle).filter(Vehicle.vehicle_code == vehicle_code).first()
            if not vehicle:
                return {"code": CODE_VEHICLE_NOT_FOUND, "message": "车辆不存在", "data": None}

            # 2. 获取节点信息
            node = db.query(Node).filter(Node.id == vehicle.node_id).first()
            last_arrived_node = db.query(Node).filter(Node.id == vehicle.last_arrived_node_id).first()

            # 3. 返回响应
            return {
                "code": CODE_SUCCESS,
                "message": "success",
                "data": {
                    "vehicle_code": vehicle.vehicle_code,
                    "model": vehicle.model,
                    "capacity": float(vehicle.capacity),
                    "energy_type": vehicle.energy_type,
                    "vehicle_type": vehicle.vehicle_type,
                    "capability_tags": vehicle.capability_tags,
                    "last_arrived_node_code": last_arrived_node.node_code if last_arrived_node else "",
                    "last_arrived_node_name": last_arrived_node.name if last_arrived_node else "",
                    "status": vehicle.status,
                    "node_code": node.node_code if node else "",
                    "node_name": node.name if node else "",
                    "created_at": vehicle.created_at.isoformat(),
                    "updated_at": vehicle.updated_at.isoformat()
                }
            }
        except Exception as e:
            return {"code": CODE_INTERNAL_ERROR, "message": f"获取车辆详情失败: {str(e)}", "data": None}

    @staticmethod
    async def update_vehicle(vehicle_code: str, vehicle_update: VehicleUpdate, db: Session) -> Dict[str, Any]:
        """更新车辆"""
        try:
            # 1. 查询Vehicle
            vehicle = db.query(Vehicle).filter(Vehicle.vehicle_code == vehicle_code).first()
            if not vehicle:
                return {"code": CODE_VEHICLE_NOT_FOUND, "message": "车辆不存在", "data": None}

            # 2. 更新字段
            if vehicle_update.model is not None:
                vehicle.model = vehicle_update.model
            if vehicle_update.capacity is not None:
                vehicle.capacity = vehicle_update.capacity
            if vehicle_update.energy_type is not None:
                vehicle.energy_type = vehicle_update.energy_type
            if vehicle_update.vehicle_type is not None:
                vehicle.vehicle_type = vehicle_update.vehicle_type
            if vehicle_update.capability_tags is not None:
                vehicle.capability_tags = vehicle_update.capability_tags
            if vehicle_update.node_code is not None:
                node = db.query(Node).filter(Node.node_code == vehicle_update.node_code).first()
                if not node:
                    return {"code": CODE_NODE_NOT_FOUND, "message": "节点不存在", "data": None}
                vehicle.node_id = node.id
            if vehicle_update.last_arrived_node_code is not None:
                last_arrived_node = db.query(Node).filter(Node.node_code == vehicle_update.last_arrived_node_code).first()
                if not last_arrived_node:
                    return {"code": CODE_NODE_NOT_FOUND, "message": "最后到达节点不存在", "data": None}
                vehicle.last_arrived_node_id = last_arrived_node.id
            if vehicle_update.status is not None:
                try:
                    transition_vehicle_status(db, vehicle, vehicle_update.status)
                except ValueError as e:
                    return {"code": CODE_VEHICLE_STATUS_NOT_ALLOWED, "message": str(e), "data": None}

            vehicle.updated_at = datetime.now()
            db.commit()

            # 3. 返回响应
            node = db.query(Node).filter(Node.id == vehicle.node_id).first()
            last_arrived_node = db.query(Node).filter(Node.id == vehicle.last_arrived_node_id).first()
            return {
                "code": CODE_SUCCESS,
                "message": "success",
                "data": {
                    "vehicle_code": vehicle.vehicle_code,
                    "model": vehicle.model,
                    "capacity": float(vehicle.capacity),
                    "energy_type": vehicle.energy_type,
                    "vehicle_type": vehicle.vehicle_type,
                    "capability_tags": vehicle.capability_tags,
                    "last_arrived_node_code": last_arrived_node.node_code if last_arrived_node else "",
                    "last_arrived_node_name": last_arrived_node.name if last_arrived_node else "",
                    "status": vehicle.status,
                    "node_code": node.node_code if node else "",
                    "node_name": node.name if node else "",
                    "created_at": vehicle.created_at.isoformat(),
                    "updated_at": vehicle.updated_at.isoformat()
                }
            }
        except Exception as e:
            db.rollback()
            return {"code": CODE_INTERNAL_ERROR, "message": f"更新车辆失败: {str(e)}", "data": None}

    @staticmethod
    async def delete_vehicle(vehicle_code: str, db: Session) -> Dict[str, Any]:
        """删除车辆"""
        try:
            # 1. 查询Vehicle
            vehicle = db.query(Vehicle).filter(Vehicle.vehicle_code == vehicle_code).first()
            if not vehicle:
                return {"code": CODE_VEHICLE_NOT_FOUND, "message": "车辆不存在", "data": None}

            # 2. 校验车辆状态（delivering不可删除）
            if vehicle.status == "delivering":
                return {"code": CODE_VEHICLE_STATUS_NOT_ALLOWED, "message": "配送中车辆不可删除", "data": None}

            # 3. 删除车辆
            db.delete(vehicle)
            db.commit()

            return {"code": CODE_SUCCESS, "message": "success", "data": None}
        except Exception as e:
            db.rollback()
            return {"code": CODE_INTERNAL_ERROR, "message": f"删除车辆失败: {str(e)}", "data": None}
