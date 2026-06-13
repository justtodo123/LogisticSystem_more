from typing import List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import json

from models.package import Package
from models.node import Node
from models.goods import Goods
from models.order import Order
from schemas.package import PackageRepack, PackageResponse
from core.error_codes import (CODE_SUCCESS, CODE_INTERNAL_ERROR,
                             CODE_PACKAGE_NOT_FOUND, CODE_PACKAGE_STATUS_NOT_ALLOWED,
                             CODE_GOODS_NOT_FOUND, CODE_NODE_NOT_FOUND)


class PackageService:
    """包裹服务"""

    @staticmethod
    async def get_packages(page: int, page_size: int, status: str = None, 
                          from_node_code: str = None, to_node_code: str = None, 
                          db: Session = None) -> Dict[str, Any]:
        """获取包裹列表"""
        try:
            # 1. 构建查询
            query = db.query(Package)
            if status:
                query = query.filter(Package.status == status)
            if from_node_code:
                from_node = db.query(Node).filter(Node.node_code == from_node_code).first()
                if from_node:
                    query = query.filter(Package.from_node_id == from_node.id)
            if to_node_code:
                to_node = db.query(Node).filter(Node.node_code == to_node_code).first()
                if to_node:
                    query = query.filter(Package.to_node_id == to_node.id)

            # 2. 分页
            total = query.count()
            packages = query.offset((page - 1) * page_size).limit(page_size).all()

            # 3. 构建响应
            items = []
            for pkg in packages:
                from_node = db.query(Node).filter(Node.id == pkg.from_node_id).first()
                to_node = db.query(Node).filter(Node.id == pkg.to_node_id).first()
                items.append({
                    "package_code": pkg.package_code,
                    "weight": float(pkg.weight),
                    "volume": float(pkg.volume),
                    "status": pkg.status,
                    "from_node_code": from_node.node_code if from_node else "",
                    "from_node_name": from_node.name if from_node else "",
                    "to_node_code": to_node.node_code if to_node else "",
                    "to_node_name": to_node.name if to_node else "",
                    "created_at": pkg.created_at.isoformat(),
                    "updated_at": pkg.updated_at.isoformat()
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
            return {"code": CODE_INTERNAL_ERROR, "message": f"获取包裹列表失败: {str(e)}", "data": None}

    @staticmethod
    async def get_package(package_code: str, db: Session) -> Dict[str, Any]:
        """获取包裹详情"""
        try:
            # 1. 查询Package
            pkg = db.query(Package).filter(Package.package_code == package_code).first()
            if not pkg:
                return {"code": CODE_PACKAGE_NOT_FOUND, "message": "包裹不存在", "data": None}

            # 2. 获取节点信息
            from_node = db.query(Node).filter(Node.id == pkg.from_node_id).first()
            to_node = db.query(Node).filter(Node.id == pkg.to_node_id).first()

            # 3. 解析goods_items
            goods_items = json.loads(pkg.goods_items) if pkg.goods_items else []

            # 4. 返回响应
            return {
                "code": CODE_SUCCESS,
                "message": "success",
                "data": {
                    "package_code": pkg.package_code,
                    "weight": float(pkg.weight),
                    "volume": float(pkg.volume),
                    "status": pkg.status,
                    "from_node_code": from_node.node_code if from_node else "",
                    "from_node_name": from_node.name if from_node else "",
                    "to_node_code": to_node.node_code if to_node else "",
                    "to_node_name": to_node.name if to_node else "",
                    "from_longitude": float(pkg.from_longitude) if pkg.from_longitude else None,
                    "from_latitude": float(pkg.from_latitude) if pkg.from_latitude else None,
                    "to_longitude": float(pkg.to_longitude) if pkg.to_longitude else None,
                    "to_latitude": float(pkg.to_latitude) if pkg.to_latitude else None,
                    "goods_items": goods_items,
                    "dispatch_code": None,  # TODO: 获取dispatch_code
                    "created_at": pkg.created_at.isoformat(),
                    "updated_at": pkg.updated_at.isoformat()
                }
            }
        except Exception as e:
            return {"code": CODE_INTERNAL_ERROR, "message": f"获取包裹详情失败: {str(e)}", "data": None}

    @staticmethod
    async def repack_package(package_code: str, repack: PackageRepack, db: Session) -> Dict[str, Any]:
        """重新打包包裹"""
        try:
            # 1. 查询原包裹，校验状态必须为 pending_pack
            pkg = db.query(Package).filter(Package.package_code == package_code).first()
            if not pkg:
                return {"code": CODE_PACKAGE_NOT_FOUND, "message": "包裹不存在", "data": None}
            
            if pkg.status != "pending_pack":
                return {"code": CODE_PACKAGE_STATUS_NOT_ALLOWED, "message": "包裹状态不允许repack", "data": None}

            # 2. 校验 goods_codes 中的货物是否属于原包裹
            original_goods_items = json.loads(pkg.goods_items) if pkg.goods_items else []
            original_goods_codes = [item["goods_code"] for item in original_goods_items]
            
            for goods_code in repack.goods_codes:
                if goods_code not in original_goods_codes:
                    return {"code": CODE_PACKAGE_STATUS_NOT_ALLOWED, "message": f"货物 {goods_code} 不属于原包裹", "data": None}

            # 3. 校验货物状态必须为 pending_pack，且处于同一个节点
            goods_list = []
            node_id = None
            for goods_code in repack.goods_codes:
                goods = db.query(Goods).filter(Goods.goods_code == goods_code).first()
                if not goods:
                    return {"code": CODE_GOODS_NOT_FOUND, "message": f"货物 {goods_code} 不存在", "data": None}
                if goods.status != "pending_pack":
                    return {"code": CODE_PACKAGE_STATUS_NOT_ALLOWED, "message": f"货物 {goods_code} 状态不是 pending_pack", "data": None}
                
                # 检查是否处于同一个节点
                if node_id is None:
                    node_id = goods.node_id
                elif goods.node_id != node_id:
                    return {"code": CODE_NODE_NOT_FOUND, "message": f"货物 {goods_code} 与其他货物不在同一个节点", "data": None}
                
                goods_list.append({
                    "goods_code": goods.goods_code,
                    "order_code": db.query(Order).filter(Order.id == goods.order_id).first().order_code if db.query(Order).filter(Order.id == goods.order_id).first() else ""
                })

            # 4. 创建新包裹（状态 pending_pack，goods_items 为重新分配的货物）
            import time
            new_package_code = f"PKG{int(time.time() * 1000)}"
            
            # 计算新包裹的重量和体积
            total_weight = 0
            total_volume = 0
            for goods_code in repack.goods_codes:
                goods = db.query(Goods).filter(Goods.goods_code == goods_code).first()
                total_weight += float(goods.weight)
                total_volume += float(goods.volume)
            
            new_pkg = Package(
                package_code=new_package_code,
                weight=total_weight,
                volume=total_volume,
                status="pending_pack",
                from_node_id=node_id,
                to_node_id=pkg.to_node_id,  # 保持原目标节点
                goods_items=json.dumps(goods_list, ensure_ascii=False)
            )
            db.add(new_pkg)
            db.flush()

            # 5. 原包裹状态改为 exception
            pkg.status = "exception"
            pkg.updated_at = datetime.now()
            
            db.commit()

            # 6. 返回新包裹信息
            from_node = db.query(Node).filter(Node.id == new_pkg.from_node_id).first()
            to_node = db.query(Node).filter(Node.id == new_pkg.to_node_id).first()
            return {
                "code": CODE_SUCCESS,
                "message": "success",
                "data": {
                    "package_code": new_pkg.package_code,
                    "weight": float(new_pkg.weight),
                    "volume": float(new_pkg.volume),
                    "status": new_pkg.status,
                    "from_node_code": from_node.node_code if from_node else "",
                    "from_node_name": from_node.name if from_node else "",
                    "to_node_code": to_node.node_code if to_node else "",
                    "to_node_name": to_node.name if to_node else "",
                    "goods_items": goods_list,
                    "created_at": new_pkg.created_at.isoformat(),
                    "updated_at": new_pkg.updated_at.isoformat()
                }
            }
        except Exception as e:
            db.rollback()
            return {"code": CODE_INTERNAL_ERROR, "message": f"重新打包失败: {str(e)}", "data": None}
