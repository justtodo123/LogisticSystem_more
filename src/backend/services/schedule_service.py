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
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import desc

from algorithms.global_schedule import global_schedule
from algorithms.packaging import packaging
from models.global_schedule import GlobalSchedule
from models.order import Order
from models.goods import Goods
from models.package import Package
from models.node import Node
from utils.response import success_response, error_response
from services.state_machine import update_orders_after_f007, update_goods_after_f021


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
        excluded_nodes: Optional[List[str]] = None,
        is_replan: bool = False,
        custom_weights: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        编排 F007 → F021 → 写库（单事务）

        流程（与 API 契约 api-contract-phase3.md §3.2 一致）：
        1. 调用 F007 全局调度算法（纯计算，不写状态）
        2. 调用 F021 打包算法（纯计算，生成 pending_pack 包裹）
        3a. F007 完成 → 写入 global_schedule + 订单 pending/exception → delivering
        3b. F021 完成 → 写入 packages(pending_pack/exception→packed) + 货物 pending_pack/exception → packed
        4. db.commit() 单事务提交

        Args:
            order_codes: 订单编号列表（可选）
            algorithm: 算法类型
            db: 数据库会话
            excluded_nodes: 排除的节点编码列表（重规划时使用）
            is_replan: 是否为重规划模式（True=处理exception状态，False=处理pending状态）
            custom_weights: 自定义权重参数（可选，优先级高于 algorithm_config.json）

        Returns:
            统一响应格式 dict
        """
        try:
            # ── 1. F007 全局调度（纯计算） ──
            schedule_result = global_schedule(
                order_codes, algorithm, db,
                excluded_nodes=excluded_nodes,
                is_replan=is_replan,
                custom_weights=custom_weights,
            )

            # ── 2. F021 打包（纯计算，暂不传 schedule_id） ──
            packages = packaging(schedule_result, None, db, is_replan=is_replan)

            # ── 3. 单事务写入 ──
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
            )
            db.add(global_schedule_obj)
            db.flush()  # 获取 global_schedule_obj.id

            # ── 3a. F007 完成 → 更新订单状态：pending→delivering（正常）或 exception→delivering（重规划） ──
            update_orders_after_f007(db, schedule_result["order_codes"])

            # ── 3b. 写入 packages ──
            # 包裹状态由 packaging() 算法决定：
            #   L0→L1 包裹: packed（货物与包裹在同一节点，可立即发运）
            #   L1→L2 包裹: pending_pack（货物尚在L0，需等货物到达L1后重新打包）
            for pkg in packages:
                pkg.schedule_id = global_schedule_obj.id
                db.add(pkg)

            # F021 完成后更新货物状态：pending_pack→packed（正常）或 exception→packed（重规划）
            update_goods_after_f021(db, global_schedule_obj.id, is_replan)

            db.commit()

            # ── 计算 score_display（归一化百分制）──
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
                "package_count": len(packages),
                "version": 1,
                "is_replan": is_replan,
            })

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
        db: Session,
    ) -> Dict[str, Any]:
        """
        获取历史全局调度方案列表

        Args:
            page: 页码
            page_size: 每页数量
            order_code: 按订单编号筛选（可选）
            db: 数据库会话

        Returns:
            统一响应格式 dict
        """
        query = db.query(GlobalSchedule)

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
            
            print(f"[DEBUG] gs.id={gs.id}, gs.score={gs.score}, raw_score={raw_score}, max_possible={max_possible}, score_display={score_display}")
            print(f"[DEBUG] gs.goods_schedules type={type(gs.goods_schedules)}, len={len(gs.goods_schedules) if isinstance(gs.goods_schedules, list) else 'N/A'}")

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
                "created_at": gs.created_at.isoformat() if gs.created_at else None,
            })
        except Exception as e:
            print(f"[ERROR] get_global_schedule failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return error_response(code=50000, message=f"获取调度方案详情失败: {str(e)}")
