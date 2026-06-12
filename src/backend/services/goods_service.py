from typing import Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload
from datetime import datetime

from models.goods import Goods
from models.order import Order
from models.node import Node
from schemas.goods import GoodsUpdate, GoodsResponse
from core.error_codes import (CODE_SUCCESS, CODE_INTERNAL_ERROR,
                             CODE_GOODS_NOT_FOUND, CODE_NODE_NOT_FOUND)


class GoodsService:
    """货物服务"""

    @staticmethod
    async def get_goods(page: int, page_size: int, status: str = None, 
                       node_code: str = None, db: Session = None) -> Dict[str, Any]:
        """获取货物列表"""
        try:
            # 1. 构建查询（使用joinedload预加载关联对象，减少N+1查询）
            query = db.query(Goods).options(
                joinedload(Goods.order),
                joinedload(Goods.node)
            )
            if status:
                query = query.filter(Goods.status == status)
            if node_code:
                node = db.query(Node).filter(Node.node_code == node_code).first()
                if node:
                    query = query.filter(Goods.node_id == node.id)

            # 2. 分页
            total = query.count()
            goods = query.offset((page - 1) * page_size).limit(page_size).all()

            # 3. 构建响应
            items = []
            for g in goods:
                # 获取订单信息（已从关联加载）
                order = g.order
                # 获取节点信息（已从关联加载）
                node = g.node
                
                items.append({
                    "goods_code": g.goods_code,
                    "goods_name": g.goods_name,
                    "goods_type": g.goods_type,
                    "weight": float(g.weight),
                    "volume": float(g.volume),
                    "status": g.status,
                    "order_code": order.order_code if order else "",
                    "node_code": node.node_code if node else "",
                    "node_name": node.name if node else "",
                    "created_at": g.created_at.isoformat(),
                    "updated_at": g.updated_at.isoformat()
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
            return {"code": CODE_INTERNAL_ERROR, "message": f"获取货物列表失败: {str(e)}", "data": None}

    @staticmethod
    async def get_good(goods_code: str, db: Session) -> Dict[str, Any]:
        """获取货物详情"""
        try:
            # 1. 查询Goods
            goods = db.query(Goods).filter(Goods.goods_code == goods_code).first()
            if not goods:
                return {"code": CODE_GOODS_NOT_FOUND, "message": "货物不存在", "data": None}

            # 2. 获取订单信息
            order = db.query(Order).filter(Order.id == goods.order_id).first()
            
            # 3. 获取节点信息
            node = db.query(Node).filter(Node.id == goods.node_id).first()

            # 4. 返回响应
            return {
                "code": CODE_SUCCESS,
                "message": "success",
                "data": {
                    "goods_code": goods.goods_code,
                    "goods_name": goods.goods_name,
                    "goods_type": goods.goods_type,
                    "weight": float(goods.weight),
                    "volume": float(goods.volume),
                    "status": goods.status,
                    "order_code": order.order_code if order else "",
                    "node_code": node.node_code if node else "",
                    "node_name": node.name if node else "",
                    "created_at": goods.created_at.isoformat(),
                    "updated_at": goods.updated_at.isoformat()
                }
            }
        except Exception as e:
            return {"code": CODE_INTERNAL_ERROR, "message": f"获取货物详情失败: {str(e)}", "data": None}

    @staticmethod
    async def update_good(goods_code: str, goods_update: GoodsUpdate, db: Session) -> Dict[str, Any]:
        """更新货物"""
        try:
            # 1. 查询Goods
            goods = db.query(Goods).filter(Goods.goods_code == goods_code).first()
            if not goods:
                return {"code": CODE_GOODS_NOT_FOUND, "message": "货物不存在", "data": None}

            # 2. 更新字段
            if goods_update.goods_name is not None:
                goods.goods_name = goods_update.goods_name
            if goods_update.goods_type is not None:
                goods.goods_type = goods_update.goods_type
            if goods_update.weight is not None:
                goods.weight = goods_update.weight
            if goods_update.volume is not None:
                goods.volume = goods_update.volume
            if goods_update.node_code is not None:
                node = db.query(Node).filter(Node.node_code == goods_update.node_code).first()
                if not node:
                    return {"code": CODE_NODE_NOT_FOUND, "message": "节点不存在", "data": None}
                goods.node_id = node.id

            goods.updated_at = datetime.now()
            db.commit()

            # 3. 返回响应
            order = db.query(Order).filter(Order.id == goods.order_id).first()
            node = db.query(Node).filter(Node.id == goods.node_id).first()
            return {
                "code": CODE_SUCCESS,
                "message": "success",
                "data": {
                    "goods_code": goods.goods_code,
                    "goods_name": goods.goods_name,
                    "goods_type": goods.goods_type,
                    "weight": float(goods.weight),
                    "volume": float(goods.volume),
                    "status": goods.status,
                    "order_code": order.order_code if order else "",
                    "node_code": node.node_code if node else "",
                    "node_name": node.name if node else "",
                    "created_at": goods.created_at.isoformat(),
                    "updated_at": goods.updated_at.isoformat()
                }
            }
        except Exception as e:
            db.rollback()
            return {"code": CODE_INTERNAL_ERROR, "message": f"更新货物失败: {str(e)}", "data": None}
