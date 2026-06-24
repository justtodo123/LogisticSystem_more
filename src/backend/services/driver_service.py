from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from models.driver import Driver
from models.node import Node
from schemas.driver import DriverCreate, DriverUpdate, DriverResponse
from core.error_codes import (CODE_SUCCESS, CODE_INTERNAL_ERROR, CODE_CONFLICT,
                             CODE_NODE_NOT_FOUND, CODE_DRIVER_NOT_FOUND,
                             CODE_DRIVER_STATUS_NOT_ALLOWED)
from services.state_machine import transition_driver_status


class DriverService:
    """司机服务"""

    @staticmethod
    async def create_driver(driver_create: DriverCreate, db: Session) -> Dict[str, Any]:
        """创建司机"""
        try:
            # 1. 校验driver_code是否已存在
            existing = db.query(Driver).filter(Driver.driver_code == driver_create.driver_code).first()
            if existing:
                return {"code": CODE_CONFLICT, "message": "司机编号已存在", "data": None}

            # 2. 校验node_code是否存在
            node = db.query(Node).filter(Node.node_code == driver_create.node_code).first()
            if not node:
                return {"code": CODE_NODE_NOT_FOUND, "message": "节点不存在", "data": None}

            # 3. 创建Driver记录
            driver = Driver(
                driver_code=driver_create.driver_code,
                name=driver_create.name,
                phone=driver_create.phone,
                license_type=driver_create.license_type,
                shift=driver_create.shift,
                node_id=node.id,
                status=driver_create.status or "idle"
            )
            db.add(driver)
            db.commit()

            # 4. 返回响应
            return {
                "code": CODE_SUCCESS,
                "message": "success",
                "data": {
                    "driver_code": driver.driver_code,
                    "name": driver.name,
                    "phone": driver.phone,
                    "license_type": driver.license_type,
                    "shift": driver.shift,
                    "node_code": node.node_code,
                    "node_name": node.name,
                    "status": driver.status,
                    "created_at": driver.created_at.isoformat(),
                    "updated_at": driver.updated_at.isoformat()
                }
            }
        except Exception as e:
            db.rollback()
            return {"code": CODE_INTERNAL_ERROR, "message": f"创建司机失败: {str(e)}", "data": None}

    @staticmethod
    async def get_drivers(page: int, page_size: int, status: str = None,
                           node_code: str = None, db: Session = None) -> Dict[str, Any]:
        """获取司机列表"""
        try:
            # 1. 构建查询
            query = db.query(Driver)
            if status:
                query = query.filter(Driver.status == status)
            if node_code:
                node = db.query(Node).filter(Node.node_code == node_code).first()
                if node:
                    query = query.filter(Driver.node_id == node.id)

            # 2. 分页
            total = query.count()
            drivers = query.offset((page - 1) * page_size).limit(page_size).all()

            # 3. 构建响应
            items = []
            for driver in drivers:
                node = db.query(Node).filter(Node.id == driver.node_id).first()
                items.append({
                    "driver_code": driver.driver_code,
                    "name": driver.name,
                    "phone": driver.phone,
                    "license_type": driver.license_type,
                    "shift": driver.shift,
                    "node_code": node.node_code if node else "",
                    "node_name": node.name if node else "",
                    "status": driver.status,
                    "created_at": driver.created_at.isoformat(),
                    "updated_at": driver.updated_at.isoformat()
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
            return {"code": CODE_INTERNAL_ERROR, "message": f"获取司机列表失败: {str(e)}", "data": None}

    @staticmethod
    async def get_driver(driver_code: str, db: Session) -> Dict[str, Any]:
        """获取司机详情"""
        try:
            # 1. 查询Driver
            driver = db.query(Driver).filter(Driver.driver_code == driver_code).first()
            if not driver:
                return {"code": CODE_DRIVER_NOT_FOUND, "message": "司机不存在", "data": None}

            # 2. 获取节点信息
            node = db.query(Node).filter(Node.id == driver.node_id).first()

            # 3. 返回响应
            return {
                "code": CODE_SUCCESS,
                "message": "success",
                "data": {
                    "driver_code": driver.driver_code,
                    "name": driver.name,
                    "phone": driver.phone,
                    "license_type": driver.license_type,
                    "shift": driver.shift,
                    "node_code": node.node_code if node else "",
                    "node_name": node.name if node else "",
                    "status": driver.status,
                    "created_at": driver.created_at.isoformat(),
                    "updated_at": driver.updated_at.isoformat()
                }
            }
        except Exception as e:
            return {"code": CODE_INTERNAL_ERROR, "message": f"获取司机详情失败: {str(e)}", "data": None}

    @staticmethod
    async def update_driver(driver_code: str, driver_update: DriverUpdate, db: Session) -> Dict[str, Any]:
        """更新司机"""
        try:
            # 1. 查询Driver
            driver = db.query(Driver).filter(Driver.driver_code == driver_code).first()
            if not driver:
                return {"code": CODE_DRIVER_NOT_FOUND, "message": "司机不存在", "data": None}

            # 2. 更新字段
            if driver_update.name is not None:
                driver.name = driver_update.name
            if driver_update.phone is not None:
                driver.phone = driver_update.phone
            if driver_update.license_type is not None:
                driver.license_type = driver_update.license_type
            if driver_update.shift is not None:
                driver.shift = driver_update.shift
            if driver_update.node_code is not None:
                node = db.query(Node).filter(Node.node_code == driver_update.node_code).first()
                if not node:
                    return {"code": CODE_NODE_NOT_FOUND, "message": "节点不存在", "data": None}
                driver.node_id = node.id
            if driver_update.status is not None:
                try:
                    transition_driver_status(db, driver, driver_update.status)
                except ValueError as e:
                    return {"code": CODE_DRIVER_STATUS_NOT_ALLOWED, "message": str(e), "data": None}

            driver.updated_at = datetime.now()
            db.commit()

            # 3. 返回响应
            node = db.query(Node).filter(Node.id == driver.node_id).first()
            return {
                "code": CODE_SUCCESS,
                "message": "success",
                "data": {
                    "driver_code": driver.driver_code,
                    "name": driver.name,
                    "phone": driver.phone,
                    "license_type": driver.license_type,
                    "shift": driver.shift,
                    "node_code": node.node_code if node else "",
                    "node_name": node.name if node else "",
                    "status": driver.status,
                    "created_at": driver.created_at.isoformat(),
                    "updated_at": driver.updated_at.isoformat()
                }
            }
        except Exception as e:
            db.rollback()
            return {"code": CODE_INTERNAL_ERROR, "message": f"更新司机失败: {str(e)}", "data": None}

    @staticmethod
    async def delete_driver(driver_code: str, db: Session) -> Dict[str, Any]:
        """删除司机"""
        try:
            # 1. 查询Driver
            driver = db.query(Driver).filter(Driver.driver_code == driver_code).first()
            if not driver:
                return {"code": CODE_DRIVER_NOT_FOUND, "message": "司机不存在", "data": None}

            # 2. 校验司机状态（busy不可删除）
            if driver.status == "busy":
                return {"code": CODE_DRIVER_STATUS_NOT_ALLOWED, "message": "司机有未完成订单，不可删除", "data": None}

            # 3. 删除司机
            db.delete(driver)
            db.commit()

            return {"code": CODE_SUCCESS, "message": "success", "data": None}
        except Exception as e:
            db.rollback()
            return {"code": CODE_INTERNAL_ERROR, "message": f"删除司机失败: {str(e)}", "data": None}
