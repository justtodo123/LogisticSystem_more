"""
调度编排服务

编排 F007 → F021 → 写库 的完整调度流程。
单事务保证原子性：global_schedules + packages + orders/goods 状态更新全部成功或全部回滚。

状态流转（与 API 契约 api-contract-phase3.md §3.2 一致）：

| 步骤    | 订单状态           | 货物状态               | 包裹状态              |
| ------- | ------------------ | ---------------------- | --------------------- |
| F007完成 | pending → delivering | pending_pack (不变)     | - (不涉及)            |
| F021完成 | delivering (不变)   | pending_pack → packed  | pending_pack → packed |
"""
import logging
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import desc

from algorithms.factory import get_global_strategy
from algorithms.packaging import packaging
from algorithms.explainer import build_explanation
from models.global_schedule import GlobalSchedule
from models.order import Order
from models.goods import Goods
from models.package import Package
from models.node import Node
from utils.response import success_response, error_response
from core.cas import claim_status
from core.error_codes import CODE_STATE_CONFLICT
from core.errors import DomainError
from services.state_machine import (
    update_orders_after_f007,
    update_goods_after_f021,
)

logger = logging.getLogger(__name__)

# 外部可选的调度算法（阶段3仅实现 traditional；deepseek 预留未实现）
SUPPORTED_ALGORITHMS = ("traditional",)



def _discard_remaining_draft(db: Session, schedule_code: str, *, commit: bool = True) -> None:
    """打包或确认失败后清理仍为 draft 的方案。"""
    try:
        leftover = db.query(GlobalSchedule).filter(
            GlobalSchedule.schedule_code == schedule_code,
            GlobalSchedule.status == "draft",
        ).first()
        if leftover:
            db.delete(leftover)
            if commit:
                db.commit()
            else:
                db.flush()
    except Exception:
        db.rollback()


async def _notify_schedule_confirmed(db: Session, gs: GlobalSchedule, raw_score: float) -> None:
    try:
        from services.notification import (
            SCENARIO_SCHEDULE_CONFIRMED,
            send_notification,
        )
        await send_notification(db, SCENARIO_SCHEDULE_CONFIRMED, {
            "schedule_code": gs.schedule_code,
            "total_goods": gs.total_goods,
            "total_distance": float(gs.total_distance),
            "total_time": float(gs.total_time),
            "score": raw_score,
            "is_replan": gs.is_replan,
        })
    except Exception:
        pass


# ── Score 归一化：内存缓存历史最大 score ──
_max_score_cache: Optional[float] = None


def _refresh_max_score(db: Session) -> float:
    """
    查询数据库历史最大 score，更新内存缓存，返回 max_possible。
    
    逻辑：
    1. 若 _max_score_cache 为 None（首次调用或进程重启），全表查询最大值
    2. 将传入的 raw_score 与缓存比较，取大者更新缓存
    3. 返回当前缓存值（即历史最大 score）
    
    Args:
        db: 数据库会话（仅在首次查询时使用）
        
    Returns:
        历史最大 score（若表中无数据则返回 1.0 避免除零）
    """
    global _max_score_cache
    if _max_score_cache is None:
        max_record = db.query(GlobalSchedule.score).order_by(
            GlobalSchedule.score.desc()
        ).first()
        _max_score_cache = float(max_record[0]) if max_record and max_record[0] else 1.0
    return _max_score_cache


def _calc_score_display(raw_score: float, max_possible: float) -> int:
    """
    计算归一化百分制分数（0~100，越高越好）。
    
    公式：score_display = 100 - min(100, raw_score / max_possible × 100)
    - raw_score 越小（越好），score_display 越大
    - 最优（raw_score=0）：score_display=100
    - 最差（raw_score=max_possible）：score_display=0
    
    Args:
        raw_score: 原始 score（越小越好）
        max_possible: 历史最大 score
        
    Returns:
        归一化分数（0~100 整数）
    """
    if max_possible <= 0:
        return 100
    ratio = raw_score / max_possible * 100.0
    display = 100 - min(100.0, ratio)
    return max(0, int(round(display)))


def _update_max_score_if_needed(raw_score: float) -> None:
    """
    比较 raw_score 与缓存的最大值，若更大则更新缓存。
    
    Args:
        raw_score: 本次计算的原始 score
    """
    global _max_score_cache
    if _max_score_cache is not None and raw_score > _max_score_cache:
        _max_score_cache = raw_score


class ScheduleService:
    """调度编排服务"""

    @staticmethod
    async def create_global_schedule(
        order_codes: Optional[List[str]],
        algorithm: str,
        db: Session,
        preview: bool = True,
        excluded_nodes: Optional[List[str]] = None,
        is_replan: bool = False,
        custom_weights: Optional[Dict[str, Any]] = None,
        commit: bool = True,
    ) -> Dict[str, Any]:
        """
        创建全局调度方案（预览模式）

        流程：
        - preview=True（默认）：仅执行 F007，生成 draft 方案
        - preview=False：报错（已移除直接落库功能，请先预览再确认）

        Args:
            order_codes: 订单编号列表（可选）
            algorithm: 算法类型
            db: 数据库会话
            preview: 是否为预览模式（必填，P1-2 强制）
            excluded_nodes: 排除的节点编码列表（重规划时使用）
            is_replan: 是否为重规划模式
            custom_weights: 自定义权重参数

        Returns:
            统一响应格式 dict
        """
        if not preview:
            return error_response(code=40000, message="P1-2 已移除直接落库功能，请先预览再确认")

        # 参数校验：algorithm 必须是已实现的算法，未知算法尽早返回参数错误而非业务错误
        if algorithm not in SUPPORTED_ALGORITHMS:
            return error_response(
                code=40000,
                message=f"不支持的算法: {algorithm}，当前支持: {', '.join(SUPPORTED_ALGORITHMS)}",
            )

        try:
            # 1. 检查是否已有 active 方案（避免重复调度）
            #    重规划（is_replan=True）跳过此检查：重规划本身就是为同一批订单创建新方案
            if order_codes and not is_replan:
                active_schedules = db.query(GlobalSchedule).filter(
                    GlobalSchedule.status == "active"
                ).all()
                order_set = set(order_codes)
                for gs in active_schedules:
                    if gs.order_codes:
                        for existing_code in gs.order_codes:
                            if existing_code in order_set:
                                return error_response(
                                    code=40002,
                                    message=f"订单 {existing_code} 已有活跃的调度方案 ({gs.schedule_code})，请先完成或丢弃现有方案"
                                )
            
            # 2. 执行 F007（纯计算，经策略工厂按 engine 选择算法）
            schedule_result = get_global_strategy().schedule(
                db=db,
                order_codes=order_codes,
                algorithm=algorithm,
                excluded_nodes=excluded_nodes,
                is_replan=is_replan,
                custom_weights=custom_weights,
            )
            
            # 3. 仅存 global_schedules（status=draft）
            #    T2-3：构建结构化解释（评分拆解/约束命中/备选方案）并随方案落库
            explanation = build_explanation(schedule_result)
            global_schedule_obj = GlobalSchedule(
                schedule_code=schedule_result["schedule_code"],
                order_codes=schedule_result["order_codes"],
                goods_schedules=schedule_result["goods_schedules"],
                total_distance=schedule_result["total_distance"],
                total_time=schedule_result["total_time"],
                total_goods=schedule_result["total_goods"],
                score=schedule_result["score"],
                algorithm_type=algorithm,
                version=1,
                is_replan=is_replan,
                status="draft",  # 新建记录直接设为 draft（非状态转换，不进 state_machine）
                explanation_data=explanation,
            )
            db.add(global_schedule_obj)
            if commit:
                db.commit()
            else:
                db.flush()
            
            # 4. 计算 score_display（归一化百分制）
            raw_score = float(schedule_result["score"])
            max_possible = _refresh_max_score(db)
            _update_max_score_if_needed(raw_score)
            score_display = _calc_score_display(raw_score, max_possible)
            
            return success_response(data={
                "schedule_code": schedule_result["schedule_code"],
                "total_distance": schedule_result["total_distance"],
                "total_time": schedule_result["total_time"],
                "total_goods": schedule_result["total_goods"],
                "score": raw_score,
                "score_display": score_display,
                "package_count": 0,  # 预览时不生成包裹
                "version": 1,
                "is_replan": is_replan,
                "status": "draft",  # 新增
                # T2-2 多目标评分
                "composite_score": schedule_result.get("composite_score"),
                "objective_scores": schedule_result.get("objective_scores"),
                "score_breakdown": schedule_result.get("score_breakdown"),
                "alternatives": schedule_result.get("alternatives", []),
                # T2-3 调度结果可解释性
                "explanation": explanation,
            })
            
        except DomainError:
            db.rollback()
            raise

        except ValueError as e:
            db.rollback()
            return error_response(code=40001, message=f"全局调度失败: {str(e)}")
            
        except Exception as e:
            db.rollback()
            return error_response(code=40001, message=f"全局调度异常: {str(e)}")

    @staticmethod
    async def get_global_schedules(
        page: int,
        page_size: int,
        order_code: Optional[str],
        status: Optional[str] = None,
        db: Session = None,
    ) -> Dict[str, Any]:
        """
        获取历史全局调度方案列表

        Args:
            page: 页码
            page_size: 每页数量
            order_code: 按订单编号筛选（可选）
            status: 按状态筛选（可选：active/draft，默认过滤 draft）
            db: 数据库会话

        Returns:
            统一响应格式 dict
        """
        query = db.query(GlobalSchedule)

        # 默认过滤 draft（只显示 active）
        if status is None:
            query = query.filter(GlobalSchedule.status == "active")
        else:
            query = query.filter(GlobalSchedule.status == status)

        if order_code:
            # JSON 字段包含匹配（SQLite 不支持 JSON_CONTAINS，用 LIKE）
            query = query.filter(
                GlobalSchedule.order_codes.cast(str).like(f"%{order_code}%")
            )

        # 获取历史最大 score（用于归一化）
        max_possible = _refresh_max_score(db)

        total = query.count()
        schedules = (
            query.order_by(desc(GlobalSchedule.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        items = []
        for gs in schedules:
            pkg_count = db.query(Package).filter(
                Package.schedule_id == gs.id
            ).count()
            raw_score = float(gs.score)
            score_display = _calc_score_display(raw_score, max_possible)
            items.append({
                "schedule_code": gs.schedule_code,
                "total_distance": float(gs.total_distance),
                "total_time": float(gs.total_time),
                "total_goods": gs.total_goods,
                "score": raw_score,
                "score_display": score_display,
                "package_count": pkg_count,
                "version": gs.version,
                "is_replan": gs.is_replan,
                "status": gs.status,
                "created_at": gs.created_at.isoformat() if gs.created_at else None,
            })

        return success_response(data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        })

    @staticmethod
    async def get_global_schedule(
        schedule_code: str,
        db: Session,
    ) -> Dict[str, Any]:
        """
        获取全局调度方案详情

        Args:
            schedule_code: 调度方案编号
            db: 数据库会话

        Returns:
            统一响应格式 dict
        """
        try:
            gs = (
                db.query(GlobalSchedule)
                .filter(GlobalSchedule.schedule_code == schedule_code)
                .first()
            )

            if not gs:
                return error_response(code=40401, message=f"调度方案不存在: {schedule_code}")

            # 计算 score_display（归一化百分制）
            max_possible = _refresh_max_score(db)
            raw_score = float(gs.score)
            score_display = _calc_score_display(raw_score, max_possible)

            # 查询关联 packages
            packages = (
                db.query(Package)
                .filter(Package.schedule_id == gs.id)
                .all()
            )

            # 重新构建 goods_schedules（含 node_name 和货物描述）
            # 1. 收集所有的 node_code 和 goods_code
            all_node_codes = set()
            all_goods_codes = set()
            goods_schedules_data = gs.goods_schedules
            if not isinstance(goods_schedules_data, list):
                return error_response(code=50001, message=f"goods_schedules 格式错误，应为列表，实际为 {type(goods_schedules_data)}")
            
            for item in goods_schedules_data:
                if not isinstance(item, dict):
                    continue
                path = item.get("path", [])
                if not isinstance(path, list):
                    continue
                for nc in path:
                    if isinstance(nc, str):
                        all_node_codes.add(nc)
                goods_code = item.get("goods_code")
                if goods_code and isinstance(goods_code, str):
                    all_goods_codes.add(goods_code)

            # 2. 批量查询 Node 和 Goods
            nodes_map = {
                n.node_code: n
                for n in db.query(Node).filter(Node.node_code.in_(all_node_codes)).all()
            }
            goods_map = {
                g.goods_code: g
                for g in db.query(Goods).filter(Goods.goods_code.in_(all_goods_codes)).all()
            }

            # 3. 构建新的 goods_schedules
            new_goods_schedules = []
            for item in goods_schedules_data:
                # 构建 path 对象数组（含 node_name）
                path_with_name = []
                for nc in item["path"]:
                    n = nodes_map.get(nc)
                    path_with_name.append({
                        "node_code": nc,
                        "node_name": n.name if n else nc,
                    })

                # 获取货物描述
                g = goods_map.get(item["goods_code"])

                new_goods_schedules.append({
                    "goods_code": item["goods_code"],
                    "goods_name": g.goods_name if g else None,
                    "goods_type": g.goods_type if g else None,
                    "weight": float(g.weight) if g else None,
                    "volume": float(g.volume) if g else None,
                    "node_code": g.node.node_code if g and g.node else None,
                    "order_code": item["order_code"],
                    "path": path_with_name,
                })

            pkg_list = []
            for pkg in packages:
                from_node = pkg.from_node
                to_node = pkg.to_node
                pkg_list.append({
                    "package_code": pkg.package_code,
                    "weight": float(pkg.weight),
                    "volume": float(pkg.volume),
                    "status": pkg.status,
                    "from_node_code": from_node.node_code if from_node else None,
                    "to_node_code": to_node.node_code if to_node else None,
                    "goods_items": pkg.goods_items,
                })

            # T2-3：读取落库的结构化解释；历史方案无数据时按存储字段现场构建
            explanation = gs.explanation_data
            if not explanation:
                explanation = build_explanation({
                    "goods_schedules": new_goods_schedules,
                    "total_distance": float(gs.total_distance),
                    "total_time": float(gs.total_time),
                    "total_goods": gs.total_goods,
                })

            return success_response(data={
                "schedule_code": gs.schedule_code,
                "total_distance": float(gs.total_distance),
                "total_time": float(gs.total_time),
                "total_goods": gs.total_goods,
                "score": raw_score,
                "score_display": score_display,
                "package_count": len(pkg_list),
                "version": gs.version,
                "is_replan": gs.is_replan,
                "goods_schedules": new_goods_schedules,
                "packages": pkg_list,
                "explanation": explanation,
                "created_at": gs.created_at.isoformat() if gs.created_at else None,
            })
        except Exception as e:
            logger.error("get_global_schedule failed: %s", e, exc_info=True)
            return error_response(code=50000, message=f"获取调度方案详情失败: {str(e)}")


    @staticmethod
    async def confirm_schedule(
        schedule_code: str,
        db: Session,
        *,
        commit: bool = True,
    ) -> Dict[str, Any]:
        """
        确认 draft 调度方案。

        先条件更新抢占 draft→active，再执行 F021 与本地副作用。
        通知在事务提交之后发送，避免持锁调用外部通道。
        """
        try:
            gs = db.query(GlobalSchedule).filter(
                GlobalSchedule.schedule_code == schedule_code,
            ).first()

            if not gs:
                return error_response(
                    code=40401,
                    message=f"draft 方案不存在或已确认: {schedule_code}"
                )
            if gs.status != "draft":
                raise DomainError(CODE_STATE_CONFLICT)

            claim_status(
                db,
                GlobalSchedule,
                identity=GlobalSchedule.id == gs.id,
                from_statuses="draft",
                to_status="active",
                increment_version=True,
            )
            db.refresh(gs)

            orders = db.query(Order).filter(
                Order.order_code.in_(gs.order_codes)
            ).all()

            allowed_statuses = (
                ("unassigned", "exception")
                if not gs.is_replan
                else ("unassigned", "exception", "assigned", "in_transit")
            )
            for order in orders:
                if order.status not in allowed_statuses:
                    db.delete(gs)
                    if commit:
                        db.commit()
                    return error_response(
                        code=40003,
                        message=f"订单 {order.order_code} 状态已变化（当前: {order.status}），请重新预览"
                    )

            schedule_result = {
                "schedule_code": gs.schedule_code,
                "order_codes": gs.order_codes,
                "goods_schedules": gs.goods_schedules,
                "total_distance": gs.total_distance,
                "total_time": gs.total_time,
                "total_goods": gs.total_goods,
                "score": gs.score,
            }
            packages = packaging(
                schedule_result, gs.id, db,
                is_replan=(orders[0].status == "exception")
            )

            for pkg in packages:
                pkg.schedule_id = gs.id
                db.add(pkg)

            update_orders_after_f007(db, gs.order_codes)
            update_goods_after_f021(db, gs.id, is_replan=(orders[0].status == "exception"))

            if commit:
                db.commit()
            else:
                db.flush()

            raw_score = float(gs.score)
            max_possible = _refresh_max_score(db)
            _update_max_score_if_needed(raw_score)
            score_display = _calc_score_display(raw_score, max_possible)
            pkg_count = db.query(Package).filter(
                Package.schedule_id == gs.id
            ).count()

            if commit:
                await _notify_schedule_confirmed(db, gs, raw_score)

            return success_response(data={
                "schedule_code": gs.schedule_code,
                "total_distance": float(gs.total_distance),
                "total_time": float(gs.total_time),
                "total_goods": gs.total_goods,
                "score": raw_score,
                "score_display": score_display,
                "package_count": pkg_count,
                "version": gs.version,
                "is_replan": gs.is_replan,
                "status": "active",
            })

        except DomainError:
            db.rollback()
            raise
        except ValueError as e:
            db.rollback()
            _discard_remaining_draft(db, schedule_code, commit=commit)
            return error_response(code=50001, message=f"确认失败，draft 已丢弃: {str(e)}")
        except Exception as e:
            db.rollback()
            _discard_remaining_draft(db, schedule_code, commit=commit)
            return error_response(code=50001, message=f"确认失败，draft 已丢弃: {str(e)}")


    @staticmethod
    async def discard_draft(
        schedule_code: str,
        db: Session,
    ) -> Dict[str, Any]:
        """
        丢弃 draft 调度方案
        
        Args:
            schedule_code: draft 方案的调度编号
            db: 数据库会话
            
        Returns:
            统一响应格式 dict
        """
        gs = db.query(GlobalSchedule).filter(
            GlobalSchedule.schedule_code == schedule_code,
            GlobalSchedule.status == "draft",
        ).first()
        
        if not gs:
            return error_response(
                code=40401,
                message=f"draft 方案不存在或已确认: {schedule_code}"
            )
        
        db.delete(gs)
        db.commit()
        
        return success_response(data={
            "schedule_code": schedule_code,
            "status": "discarded",
        })
