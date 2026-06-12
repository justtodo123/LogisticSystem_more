from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from models.node import Node
from models.storage_center import StorageCenter
from models.sorting_center import SortingCenter
from schemas.node import StorageCenterResponse, SortingCenterResponse, NodeResponse
from core.error_codes import (CODE_SUCCESS, CODE_INTERNAL_ERROR, CODE_CONFLICT,
                             CODE_NODE_NOT_FOUND, CODE_STORAGE_CENTER_NOT_FOUND,
                             CODE_SORTING_CENTER_NOT_FOUND)


class NodeService:
    """节点服务"""

    @staticmethod
    async def create_storage_center(center_create: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """创建存储中心（原子操作nodes+storage_centers）"""
        try:
            # 1. 检查node_code是否已存在
            existing = db.query(Node).filter(Node.node_code == center_create["node_code"]).first()
            if existing:
                return {"code": CODE_CONFLICT, "message": "存储中心编号已存在", "data": None}

            # 2. 创建Node记录
            node = Node(
                node_code=center_create["node_code"],
                name=center_create["name"],
                location=center_create["location"],
                latitude=center_create["latitude"],
                longitude=center_create["longitude"],
                node_type="storage_center"
            )
            db.add(node)
            db.flush()  # 获取node.id

            # 3. 创建StorageCenter记录
            storage_center = StorageCenter(
                node_id=node.id,
                capacity=center_create["capacity"],
                inventory=center_create.get("inventory", 0)
            )
            db.add(storage_center)
            db.commit()

            # 4. 返回响应
            return {
                "code": CODE_SUCCESS,
                "message": "success",
                "data": {
                    "node_code": node.node_code,
                    "name": node.name,
                    "location": node.location,
                    "latitude": float(node.latitude),
                    "longitude": float(node.longitude),
                    "capacity": float(storage_center.capacity),
                    "inventory": storage_center.inventory,
                    "created_at": node.created_at.isoformat(),
                    "updated_at": node.updated_at.isoformat()
                }
            }
        except Exception as e:
            db.rollback()
            return {"code": CODE_INTERNAL_ERROR, "message": f"创建存储中心失败: {str(e)}", "data": None}

    @staticmethod
    async def update_storage_center(node_code: str, center_update: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """更新存储中心"""
        try:
            # 1. 查询Node和StorageCenter
            node = db.query(Node).filter(Node.node_code == node_code, Node.node_type == "storage_center").first()
            if not node:
                return {"code": CODE_NODE_NOT_FOUND, "message": "存储中心不存在", "data": None}

            storage_center = db.query(StorageCenter).filter(StorageCenter.node_id == node.id).first()
            if not storage_center:
                return {"code": CODE_STORAGE_CENTER_NOT_FOUND, "message": "存储中心数据不存在", "data": None}

            # 2. 更新Node字段
            if "name" in center_update:
                node.name = center_update["name"]
            if "location" in center_update:
                node.location = center_update["location"]
            if "latitude" in center_update:
                node.latitude = center_update["latitude"]
            if "longitude" in center_update:
                node.longitude = center_update["longitude"]

            # 3. 更新StorageCenter字段
            if "capacity" in center_update:
                storage_center.capacity = center_update["capacity"]
            if "inventory" in center_update:
                storage_center.inventory = center_update["inventory"]

            node.updated_at = datetime.now()
            db.commit()

            # 4. 返回响应
            return {
                "code": CODE_SUCCESS,
                "message": "success",
                "data": {
                    "node_code": node.node_code,
                    "name": node.name,
                    "location": node.location,
                    "latitude": float(node.latitude),
                    "longitude": float(node.longitude),
                    "capacity": float(storage_center.capacity),
                    "inventory": storage_center.inventory,
                    "created_at": node.created_at.isoformat(),
                    "updated_at": node.updated_at.isoformat()
                }
            }
        except Exception as e:
            db.rollback()
            return {"code": CODE_INTERNAL_ERROR, "message": f"更新存储中心失败: {str(e)}", "data": None}

    @staticmethod
    async def delete_storage_center(node_code: str, db: Session) -> Dict[str, Any]:
        """删除存储中心"""
        try:
            # 1. 查询Node
            node = db.query(Node).filter(Node.node_code == node_code, Node.node_type == "storage_center").first()
            if not node:
                return {"code": CODE_NODE_NOT_FOUND, "message": "存储中心不存在", "data": None}

            # 2. 删除StorageCenter（会自动删除，因为定义了cascade）
            # 3. 删除Node
            db.delete(node)
            db.commit()

            return {"code": CODE_SUCCESS, "message": "success", "data": None}
        except Exception as e:
            db.rollback()
            return {"code": CODE_INTERNAL_ERROR, "message": f"删除存储中心失败: {str(e)}", "data": None}

    @staticmethod
    async def create_sorting_center(center_create: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """创建分拣中心（原子操作nodes+sorting_centers）"""
        try:
            # 1. 检查node_code是否已存在
            existing = db.query(Node).filter(Node.node_code == center_create["node_code"]).first()
            if existing:
                return {"code": CODE_CONFLICT, "message": "分拣中心编号已存在", "data": None}

            # 2. 创建Node记录
            node = Node(
                node_code=center_create["node_code"],
                name=center_create["name"],
                location=center_create["location"],
                latitude=center_create["latitude"],
                longitude=center_create["longitude"],
                node_type="sorting_center"
            )
            db.add(node)
            db.flush()  # 获取node.id

            # 3. 创建SortingCenter记录
            sorting_center = SortingCenter(
                node_id=node.id,
                level=center_create["level"],
                capacity=center_create.get("capacity"),
                max_storage_time=center_create.get("max_storage_time")
            )
            db.add(sorting_center)
            db.commit()

            # 4. 返回响应
            return {
                "code": CODE_SUCCESS,
                "message": "success",
                "data": {
                    "node_code": node.node_code,
                    "name": node.name,
                    "location": node.location,
                    "latitude": float(node.latitude),
                    "longitude": float(node.longitude),
                    "level": sorting_center.level,
                    "capacity": float(sorting_center.capacity) if sorting_center.capacity else None,
                    "max_storage_time": sorting_center.max_storage_time,
                    "created_at": node.created_at.isoformat(),
                    "updated_at": node.updated_at.isoformat()
                }
            }
        except Exception as e:
            db.rollback()
            return {"code": CODE_INTERNAL_ERROR, "message": f"创建分拣中心失败: {str(e)}", "data": None}

    @staticmethod
    async def update_sorting_center(node_code: str, center_update: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """更新分拣中心"""
        try:
            # 1. 查询Node和SortingCenter
            node = db.query(Node).filter(Node.node_code == node_code, Node.node_type == "sorting_center").first()
            if not node:
                return {"code": CODE_NODE_NOT_FOUND, "message": "分拣中心不存在", "data": None}

            sorting_center = db.query(SortingCenter).filter(SortingCenter.node_id == node.id).first()
            if not sorting_center:
                return {"code": CODE_SORTING_CENTER_NOT_FOUND, "message": "分拣中心数据不存在", "data": None}

            # 2. 更新Node字段
            if "name" in center_update:
                node.name = center_update["name"]
            if "location" in center_update:
                node.location = center_update["location"]
            if "latitude" in center_update:
                node.latitude = center_update["latitude"]
            if "longitude" in center_update:
                node.longitude = center_update["longitude"]

            # 3. 更新SortingCenter字段
            if "level" in center_update:
                sorting_center.level = center_update["level"]
            if "capacity" in center_update:
                sorting_center.capacity = center_update["capacity"]
            if "max_storage_time" in center_update:
                sorting_center.max_storage_time = center_update["max_storage_time"]

            node.updated_at = datetime.now()
            db.commit()

            # 4. 返回响应
            return {
                "code": CODE_SUCCESS,
                "message": "success",
                "data": {
                    "node_code": node.node_code,
                    "name": node.name,
                    "location": node.location,
                    "latitude": float(node.latitude),
                    "longitude": float(node.longitude),
                    "level": sorting_center.level,
                    "capacity": float(sorting_center.capacity) if sorting_center.capacity else None,
                    "max_storage_time": sorting_center.max_storage_time,
                    "created_at": node.created_at.isoformat(),
                    "updated_at": node.updated_at.isoformat()
                }
            }
        except Exception as e:
            db.rollback()
            return {"code": CODE_INTERNAL_ERROR, "message": f"更新分拣中心失败: {str(e)}", "data": None}

    @staticmethod
    async def delete_sorting_center(node_code: str, db: Session) -> Dict[str, Any]:
        """删除分拣中心"""
        try:
            # 1. 查询Node
            node = db.query(Node).filter(Node.node_code == node_code, Node.node_type == "sorting_center").first()
            if not node:
                return {"code": CODE_NODE_NOT_FOUND, "message": "分拣中心不存在", "data": None}

            # 2. 删除SortingCenter（会自动删除，因为定义了cascade）
            # 3. 删除Node
            db.delete(node)
            db.commit()

            return {"code": CODE_SUCCESS, "message": "success", "data": None}
        except Exception as e:
            db.rollback()
            return {"code": CODE_INTERNAL_ERROR, "message": f"删除分拣中心失败: {str(e)}", "data": None}

    @staticmethod
    async def get_nodes(page: int, page_size: int, node_type: str = None, db: Session = None) -> Dict[str, Any]:
        """获取节点列表"""
        try:
            # 1. 构建查询
            query = db.query(Node)
            if node_type:
                query = query.filter(Node.node_type == node_type)

            # 2. 分页
            total = query.count()
            nodes = query.offset((page - 1) * page_size).limit(page_size).all()

            # 3. 构建响应
            items = []
            for node in nodes:
                item = {
                    "node_code": node.node_code,
                    "name": node.name,
                    "location": node.location,
                    "latitude": float(node.latitude),
                    "longitude": float(node.longitude),
                    "node_type": node.node_type,
                    "created_at": node.created_at.isoformat(),
                    "updated_at": node.updated_at.isoformat()
                }
                items.append(item)

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
            return {"code": CODE_INTERNAL_ERROR, "message": f"获取节点列表失败: {str(e)}", "data": None}

    @staticmethod
    async def get_node(node_code: str, db: Session) -> Dict[str, Any]:
        """获取节点详情"""
        try:
            # 1. 查询Node
            node = db.query(Node).filter(Node.node_code == node_code).first()
            if not node:
                return {"code": CODE_NODE_NOT_FOUND, "message": "节点不存在", "data": None}

            # 2. 构建响应
            result = {
                "node_code": node.node_code,
                "name": node.name,
                "location": node.location,
                "latitude": float(node.latitude),
                "longitude": float(node.longitude),
                "node_type": node.node_type,
                "created_at": node.created_at.isoformat(),
                "updated_at": node.updated_at.isoformat()
            }

            # 3. 根据节点类型添加额外信息
            if node.node_type == "storage_center":
                storage_center = db.query(StorageCenter).filter(StorageCenter.node_id == node.id).first()
                if storage_center:
                    result["capacity"] = float(storage_center.capacity)
                    result["inventory"] = storage_center.inventory
            elif node.node_type == "sorting_center":
                sorting_center = db.query(SortingCenter).filter(SortingCenter.node_id == node.id).first()
                if sorting_center:
                    result["level"] = sorting_center.level
                    result["capacity"] = float(sorting_center.capacity) if sorting_center.capacity else None
                    result["max_storage_time"] = sorting_center.max_storage_time

            return {
                "code": CODE_SUCCESS,
                "message": "success",
                "data": result
            }
        except Exception as e:
            return {"code": CODE_INTERNAL_ERROR, "message": f"获取节点详情失败: {str(e)}", "data": None}
