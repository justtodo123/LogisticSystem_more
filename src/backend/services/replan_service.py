"""
重规划服务（方案A：不修改现有服务层）

在 ReplanService 中实现版本链逻辑：
1. 读取原调度方案
2. 直接调用现有服务层（不修改它们）
3. 在 ReplanService 中更新新方案的版本链字段

阶段7新增。
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from models.exception_event import ExceptionEvent
from models.global_schedule import GlobalSchedule
from models.goods import Goods
from models.order import Order
from models.package import Package
from models.route import Route
from models.node_dispatch import NodeDispatch
from models.dispatch_batch import DispatchBatch
from models.vehicle import Vehicle
from models.node import Node
from utils.response import success_response, error_response
from services.state_machine import reset_goods_for_replan, mark_old_entities_exception, update_batch_status
from services.diff_service import build_diff_report
from services.replan_task_service import StepExecutionError, resume_async, start
from services.outbox_service import enqueue_outbox


class ReplanService:
    """重规划服务（方案A：不修改现有服务层）"""

    # ── T3-1 辅助方法：解析异常事件影响的订单 ──
    @staticmethod
    def _resolve_affected_order_codes(db: Session, event: ExceptionEvent) -> List[str]:
        """
        根据异常事件的 target 解析受影响的订单编码列表。

        - target_type="package" → 该包裹所属订单
        - target_type="node"    → 起点/终点为该节点的包裹所属订单
        - target_type="vehicle" → 该车辆调度明细内包裹所属订单
        """
        affected: List[str] = []

        def _collect_orders(pkg) -> None:
            if not pkg or not pkg.goods_items:
                return
            for gi in pkg.goods_items:
                order_code = gi.get("order_code")
                if order_code and order_code not in affected:
                    affected.append(order_code)

        if not event or not event.target_type or not event.target_code:
            return affected

        if event.target_type == "package":
            pkg = db.query(Package).filter(
                Package.package_code == event.target_code
            ).first()
            _collect_orders(pkg)

        elif event.target_type == "node":
            node = db.query(Node).filter(Node.node_code == event.target_code).first()
            if node:
                pkgs = db.query(Package).filter(
                    (Package.from_node_id == node.id) | (Package.to_node_id == node.id)
                ).all()
                for pkg in pkgs:
                    _collect_orders(pkg)

        elif event.target_type == "vehicle":
            vehicle = db.query(Vehicle).filter(
                Vehicle.vehicle_code == event.target_code
            ).first()
            if vehicle:
                dispatches = db.query(NodeDispatch).filter(
                    NodeDispatch.vehicle_id == vehicle.id
                ).all()
                for d in dispatches:
                    tasks = d.tasks
                    if isinstance(tasks, str):
                        import json
                        tasks = json.loads(tasks)
                    for task in tasks or []:
                        for pkg_code in task.get("package_codes", []):
                            pkg = db.query(Package).filter(
                                Package.package_code == pkg_code
                            ).first()
                            _collect_orders(pkg)

        return affected

    @staticmethod
    def _decide_strategy(
        strategy: str,
        affected_order_codes: List[str],
        all_order_codes: List[str],
    ) -> str:
        """策略归一化：hybrid 自动选择 partial / full"""
        strategy = (strategy or "full").lower()
        if strategy == "hybrid":
            if (
                affected_order_codes
                and len(affected_order_codes) <= max(1, len(all_order_codes) / 2)
            ):
                return "partial"
            return "full"
        return strategy if strategy in ("partial", "full") else "full"

    @staticmethod
    async def _redispatch_saga(
        db: Session,
        original: GlobalSchedule,
        replan_reason: str,
        event: Optional[ExceptionEvent],
        custom_weights: Optional[Dict[str, Any]],
        strategy: str,
        idempotency_key: Optional[str],
        after_commit_hook=None,
    ) -> Dict[str, Any]:
        """用持久化 current_step 驱动真实 F007-F006 重规划链路。"""
        from services.dispatch_service import DispatchService
        from services.route_service import RouteService
        from services.schedule_service import ScheduleService

        all_order_codes = original.order_codes
        if isinstance(all_order_codes, str):
            import json
            all_order_codes = json.loads(all_order_codes)
        affected_order_codes = (
            ReplanService._resolve_affected_order_codes(db, event)
            if event is not None
            else []
        )
        strategy = ReplanService._decide_strategy(
            strategy, affected_order_codes, all_order_codes or []
        )
        order_codes = (
            affected_order_codes
            if strategy == "partial" and affected_order_codes
            else all_order_codes
        )
        excluded_nodes = []
        excluded_vehicles = []
        if event and event.target_type == "node" and event.target_code:
            excluded_nodes.append(event.target_code)
        if event and event.target_type == "vehicle" and event.target_code:
            excluded_vehicles.append(event.target_code)

        key = idempotency_key or (
            f"redispatch:{original.schedule_code}:"
            f"{event.event_code if event else replan_reason}:{strategy}"
        )
        task = start(db, key)
        state: Dict[str, Any] = {}

        if task.current_step != "F007":
            schedule = (
                db.query(GlobalSchedule)
                .filter(
                    GlobalSchedule.parent_id == original.id,
                    GlobalSchedule.is_replan.is_(True),
                )
                .order_by(GlobalSchedule.id.desc())
                .first()
            )
            if schedule:
                state["schedule_code"] = schedule.schedule_code
        if task.current_step in {"F006", "NOTIFICATION", "COMPLETED"}:
            batch = (
                db.query(DispatchBatch)
                .join(GlobalSchedule, DispatchBatch.global_schedule_id == GlobalSchedule.id)
                .filter(GlobalSchedule.parent_id == original.id)
                .order_by(DispatchBatch.id.desc())
                .first()
            )
            if batch:
                state["batch_code"] = batch.batch_code

        async def f007(step_db: Session, _task):
            if event is None:
                reset_goods_for_replan(step_db, order_codes)
            result = await ScheduleService.create_global_schedule(
                order_codes=order_codes,
                algorithm=original.algorithm_type or "traditional",
                db=step_db,
                excluded_nodes=excluded_nodes or None,
                is_replan=True,
                custom_weights=custom_weights,
                commit=False,
            )
            if result.get("code") != 0:
                raise StepExecutionError(result.get("message", "F007 failed"))
            schedule_code = result["data"]["schedule_code"]
            schedule = step_db.query(GlobalSchedule).filter(
                GlobalSchedule.schedule_code == schedule_code
            ).first()
            schedule.version = original.version
            schedule.parent_id = original.id
            schedule.replan_reason = replan_reason
            schedule.is_replan = True
            state["schedule_code"] = schedule_code

        async def f021(step_db: Session, _task):
            result = await ScheduleService.confirm_schedule(
                schedule_code=state["schedule_code"], db=step_db, commit=False
            )
            if result.get("code") != 0:
                raise StepExecutionError(result.get("message", "F021 failed"))
            mark_old_entities_exception(step_db, original.id)

        async def f005(step_db: Session, _task):
            result = await DispatchService.create_node_dispatch(
                schedule_code=state["schedule_code"],
                demo_mode=event is None,
                db=step_db,
                excluded_vehicles=excluded_vehicles or None,
                is_replan=False,
                custom_weights=custom_weights,
                commit=False,
            )
            if result.get("code") != 0:
                raise StepExecutionError(result.get("message", "F005 failed"))
            state["batch_code"] = result["data"]["batch_code"]

        async def f006(step_db: Session, _task):
            result = await RouteService.create_route_planning(
                batch_code=state["batch_code"],
                dispatch_codes=None,
                db=step_db,
                custom_weights=custom_weights,
                commit=False,
            )
            if result.get("code") != 0:
                raise StepExecutionError(result.get("message", "F006 failed"))

        async def notification(_db: Session, _task):
            return None

        def compensate_f007(step_db: Session, _task) -> None:
            schedule = step_db.query(GlobalSchedule).filter(
                GlobalSchedule.schedule_code == state.get("schedule_code"),
                GlobalSchedule.status == "draft",
            ).first()
            if schedule:
                step_db.delete(schedule)

        def compensate_f005(step_db: Session, _task) -> None:
            batch = step_db.query(DispatchBatch).filter(
                DispatchBatch.batch_code == state.get("batch_code")
            ).first()
            if batch and batch.status != "in_transit":
                batch.status = "failed"

        def compensate_f006(step_db: Session, _task) -> None:
            routes = (
                step_db.query(Route)
                .join(NodeDispatch, Route.dispatch_id == NodeDispatch.id)
                .join(DispatchBatch, NodeDispatch.dispatch_batch_id == DispatchBatch.id)
                .filter(DispatchBatch.batch_code == state.get("batch_code"))
                .all()
            )
            batch = step_db.query(DispatchBatch).filter(
                DispatchBatch.batch_code == state.get("batch_code")
            ).first()
            if batch and batch.status not in {"in_transit", "completed"}:
                for route in routes:
                    step_db.delete(route)

        executors = {
            "F007": f007,
            "F021": f021,
            "F005": f005,
            "F006": f006,
            "NOTIFICATION": notification,
        }
        compensators = {
            "F007": compensate_f007,
            "F005": compensate_f005,
            "F006": compensate_f006,
        }
        notification_payload = {
            "original_schedule_code": original.schedule_code,
            "new_schedule_code": state.get("schedule_code"),
            "strategy": strategy,
            "replan_reason": replan_reason,
        }
        while task.current_step != "COMPLETED" and not task.manual_required:
            task = await resume_async(
                db,
                task.id,
                executors=executors,
                compensators=compensators,
                after_commit_hook=after_commit_hook,
                notification_payload=notification_payload,
            )
            notification_payload["new_schedule_code"] = state.get("schedule_code")

        if task.manual_required:
            return error_response(
                code=40901,
                message="重规划已进入人工处理",
                data={"task_id": task.id, "current_step": task.current_step},
            )
        schedule = db.query(GlobalSchedule).filter(
            GlobalSchedule.schedule_code == state.get("schedule_code")
        ).first()
        diff_summary = (
            build_diff_report(db, original, schedule, strategy=strategy)
            if schedule else None
        )
        return success_response(data={
            "task_id": task.id,
            "schedule_code": state.get("schedule_code"),
            "new_schedule_code": state.get("schedule_code"),
            "batch_code": state.get("batch_code"),
            "version": schedule.version if schedule else original.version + 1,
            "is_replan": True,
            "replan_reason": replan_reason,
            "original_schedule_code": original.schedule_code,
            "strategy": strategy,
            "diff_summary": diff_summary,
        })

    @staticmethod
    async def redispatch(
        db: Session,
        original_schedule_code: str,
        replan_reason: str,
        event: Optional[ExceptionEvent] = None,
        custom_weights: Optional[Dict[str, Any]] = None,
        draft_only: bool = False,
        strategy: str = "full",
        idempotency_key: Optional[str] = None,
        _after_commit_hook=None,
    ) -> Dict[str, Any]:
        """
        重调度（F007→F021→F005→F006）

        流程：
        1. 读取原调度方案（GlobalSchedule）
        2. 获取相关订单编号（partial 仅取受影响订单）
        3. 提取排除参数（excluded_nodes）
        4. 调用现有 ScheduleService.create_global_schedule()（不修改它）
        5. 更新新版调度方案的版本链字段
        6. 调用 DispatchService.create_node_dispatch() 执行节点调度
        7. 生成差异报告（diff_summary）

        Args:
            db: 数据库会话
            original_schedule_code: 原调度方案业务编号
            replan_reason: 重规划原因
            event: 异常事件对象（可选，用于提取排除参数与受影响订单）
            custom_weights: 自定义权重参数（可选，用于AI驱动的重规划）
            draft_only: 仅生成 draft 方案（跳过 confirm/F021/F005/F006）
            strategy: 重规划策略（partial=仅重排受影响订单 / full=全部重排 / hybrid=自动选择）

        Returns:
            统一响应格式 dict
        """
        try:
            # 1. 读取原调度方案
            original = db.query(GlobalSchedule).filter(
                GlobalSchedule.schedule_code == original_schedule_code
            ).first()

            if not original:
                return error_response(
                    code=40401,
                    message=f"原调度方案不存在: {original_schedule_code}",
                )

            if not draft_only:
                return await ReplanService._redispatch_saga(
                    db=db,
                    original=original,
                    replan_reason=replan_reason,
                    event=event,
                    custom_weights=custom_weights,
                    strategy=strategy,
                    idempotency_key=idempotency_key,
                    after_commit_hook=_after_commit_hook,
                )

            # 2. 获取相关订单编号（T3-1：按策略过滤受影响订单）
            all_order_codes = original.order_codes
            if isinstance(all_order_codes, str):
                import json
                all_order_codes = json.loads(all_order_codes)
            algorithm = original.algorithm_type or "traditional"

            affected_order_codes = (
                ReplanService._resolve_affected_order_codes(db, event)
                if event is not None
                else []
            )
            strategy = ReplanService._decide_strategy(
                strategy, affected_order_codes, all_order_codes or []
            )
            order_codes = (
                affected_order_codes
                if strategy == "partial" and affected_order_codes
                else all_order_codes
            )

            # 3. 判断是否为异常驱动的重规划（vs AI 权重重规划）
            #    异常驱动：有 event 对象 → is_replan=True → 查找 exception 状态订单/包裹
            #    AI 权重：无 event → is_replan=False → 查找 packed 状态包裹（新生成的）
            has_event = event is not None

            # 4. 提取排除参数
            excluded_nodes = []
            excluded_vehicles = []
            if event:
                if event.target_type == "node" and event.target_code:
                    excluded_nodes.append(event.target_code)
                elif event.target_type == "vehicle" and event.target_code:
                    excluded_vehicles.append(event.target_code)
                    # 同时从关联调度明细中查找该车辆参与的所有调度
                    vehicle = db.query(Vehicle).filter(
                        Vehicle.vehicle_code == event.target_code
                    ).first()
                    if vehicle:
                        dispatches = db.query(NodeDispatch).filter(
                            NodeDispatch.vehicle_id == vehicle.id
                        ).all()
                        for d in dispatches:
                            v = db.query(Vehicle).filter(Vehicle.id == d.vehicle_id).first()
                            if v and v.vehicle_code not in excluded_vehicles:
                                excluded_vehicles.append(v.vehicle_code)

            # 4.5 AI重规划（无异常事件）：仅重置 packed/in_transit
            #     packaging(is_replan=False) 只查 pending_pack 的货物。
            #     delivered 为终态，不回退、不再入包。
            #     draft_only=True 时不重置（仅生成草案，不改变现有状态）
            if not has_event and not draft_only:
                # AI 重规划：重置货物状态，使其重新参与 F007 调度
                reset_goods_for_replan(db, order_codes)

            # 5. 调用现有服务层（不修改它们）
            from services.schedule_service import ScheduleService

            schedule_result = await ScheduleService.create_global_schedule(
                order_codes=order_codes,
                algorithm=algorithm,
                db=db,
                excluded_nodes=excluded_nodes if excluded_nodes else None,
                is_replan=True,  # redispatch 始终是重规划，需跳过 active 方案检查
                custom_weights=custom_weights,  # AI驱动的自定义权重
                commit=False,
            )

            # 检查预览调度是否成功
            if schedule_result.get("code") != 0:
                return schedule_result

            new_schedule_code = schedule_result["data"]["schedule_code"]

            # draft_only：设置版本链后立即返回（不执行 confirm/F021/F005/F006）
            if draft_only:
                new_schedule = db.query(GlobalSchedule).filter(
                    GlobalSchedule.schedule_code == new_schedule_code
                ).first()
                if new_schedule:
                    new_schedule.version = original.version + 1
                    new_schedule.parent_id = original.id
                    new_schedule.replan_reason = replan_reason
                    new_schedule.is_replan = True
                    db.commit()
                # T3-1：差异报告
                diff_summary = build_diff_report(
                    db, original, new_schedule, strategy=strategy
                ) if new_schedule else None
                return success_response(data={
                    "schedule_code": new_schedule_code,
                    "new_schedule_code": new_schedule_code,
                    "status": "draft",
                    "version": new_schedule.version if new_schedule else original.version + 1,
                    "is_replan": True,
                    "replan_reason": replan_reason,
                    "original_schedule_code": original_schedule_code,
                    "strategy": strategy,
                    "diff_summary": diff_summary,
                })

            # 5.5 确认方案（draft → active，执行 F021 打包）
            confirm_result = await ScheduleService.confirm_schedule(
                schedule_code=new_schedule_code,
                db=db,
                commit=False,
            )
            if confirm_result.get("code") != 0:
                return confirm_result

            # 7. 更新新版调度方案的版本链字段
            new_schedule = db.query(GlobalSchedule).filter(
                GlobalSchedule.schedule_code == new_schedule_code
            ).first()

            if new_schedule:
                new_schedule.version = original.version + 1
                new_schedule.parent_id = original.id
                new_schedule.replan_reason = replan_reason
                new_schedule.is_replan = True
                db.commit()

            # 7.5 将原方案包裹标记为 exception（已被重规划替代）
            mark_old_entities_exception(db, original.id)

            # 6. 继续调用节点调度（获取该方案的完整结果）
            #    AI 重规划(has_event=False)：demo_mode=True 完成全链路 L0→L1→L2
            #    异常驱动(has_event=True)：demo_mode=False 仅生成方案，不自动送达
            from services.dispatch_service import DispatchService

            dispatch_result = await DispatchService.create_node_dispatch(
                schedule_code=new_schedule_code,
                demo_mode=not has_event,  # AI重规划自动完成全链路；异常重规划仅生成方案
                db=db,
                excluded_vehicles=excluded_vehicles if excluded_vehicles else None,
                is_replan=False,  # 新方案包裹始终为 packed，不需要查询 exception 包裹
                custom_weights=custom_weights,  # AI驱动的自定义权重
                commit=False,
            )

            # 调度失败时上报错误（不再静默吞掉）
            if not isinstance(dispatch_result, dict) or dispatch_result.get("code") != 0:
                error_msg = dispatch_result.get("message", "未知错误") if isinstance(dispatch_result, dict) else str(dispatch_result)
                return error_response(code=40001, message=f"节点调度失败：{error_msg}")

            batch_code = dispatch_result["data"].get("batch_code")

            # 6.5 执行路径规划（F006，为每辆车规划行驶路线）
            from services.route_service import RouteService
            route_result = await RouteService.create_route_planning(
                batch_code=batch_code,
                dispatch_codes=None,  # 批量规划该批次所有车辆
                db=db,
                custom_weights=custom_weights,
                commit=False,
            )
            if route_result.get("code") != 0:
                route_error = route_result.get("message", "未知错误") if isinstance(route_result, dict) else str(route_result)
                return error_response(code=40001, message=f"路径规划失败：{route_error}")

            # 8. 旧批次状态已由 mark_old_entities_exception() 更新为 failed
            db.commit()

            # T3-1：差异报告（新方案 vs 原方案）
            diff_summary = build_diff_report(
                db, original, new_schedule, strategy=strategy
            ) if new_schedule else None

            # 重规划通知只在请求事务中入队；外部 I/O 由 outbox worker 执行。
            enqueue_outbox(
                db,
                dedup_key=f"replan:{new_schedule_code}:completed",
                event_type="replan.completed",
                payload={
                    "original_schedule_code": original_schedule_code,
                    "new_schedule_code": new_schedule_code,
                    "strategy": strategy,
                    "replan_reason": replan_reason,
                    "diff_summary": diff_summary,
                },
            )
            db.commit()

            return success_response(data={
                "schedule_code": new_schedule_code,
                "new_schedule_code": new_schedule_code,
                "batch_code": batch_code,
                "version": new_schedule.version if new_schedule else original.version + 1,
                "is_replan": True,
                "replan_reason": replan_reason,
                "original_schedule_code": original_schedule_code,
                "strategy": strategy,
                "diff_summary": diff_summary,
            })

        except Exception as e:
            db.rollback()
            return error_response(code=40001, message=f"重调度失败: {str(e)}")

    @staticmethod
    async def redispatch_batch(
        db: Session,
        event_codes: List[str],
        replan_reason: str,
        strategy: str = "full",
    ) -> Dict[str, Any]:
        """
        批量异常重规划（T3-1）。

        同一调度方案关联的多个异常事件只触发一次重规划（不重复创建重规划任务）。
        每个唯一调度方案执行一次 redispatch，并回写所有关联事件的重规划批次码。

        Args:
            db: 数据库会话
            event_codes: 异常事件编码列表
            replan_reason: 重规划原因
            strategy: 重规划策略（partial/full/hybrid）

        Returns:
            统一响应格式 dict：{events: [...], replanned_schedules: [...]}
        """
        if not event_codes:
            return error_response(code=40001, message="未提供异常事件编码")

        events = (
            db.query(ExceptionEvent)
            .filter(ExceptionEvent.event_code.in_(event_codes))
            .all()
        )
        if not events:
            return error_response(code=40401, message="未找到匹配的异常事件")

        # 按关联调度方案分组（去重：同一方案只重规划一次）
        schedule_to_events: Dict[str, List[ExceptionEvent]] = {}
        skipped: List[str] = []
        for event in events:
            if event.status == "resolved":
                skipped.append(event.event_code)
                continue
            if not event.related_schedule_code:
                skipped.append(event.event_code)
                continue
            schedule_to_events.setdefault(event.related_schedule_code, []).append(event)

        results: List[Dict[str, Any]] = []
        for schedule_code, evts in schedule_to_events.items():
            # 用第一个事件提取排除参数；其余事件仅标记 replan_batch_code
            result = await ReplanService.redispatch(
                db=db,
                original_schedule_code=schedule_code,
                replan_reason=replan_reason,
                event=evts[0],
                strategy=strategy,
            )
            new_code = None
            if result.get("code") == 0 and result.get("data"):
                new_code = (
                    result["data"].get("schedule_code")
                    or result["data"].get("batch_code")
                )
                for evt in evts:
                    evt.replan_batch_code = new_code
            results.append({
                "schedule_code": schedule_code,
                "event_codes": [e.event_code for e in evts],
                "result_code": result.get("code"),
                "message": result.get("message"),
                "new_schedule_code": new_code,
                "strategy": result.get("data", {}).get("strategy", strategy) if result.get("code") == 0 else strategy,
                "diff_summary": result.get("data", {}).get("diff_summary") if result.get("code") == 0 else None,
            })
        db.commit()

        return success_response(data={
            "replanned_schedules": results,
            "skipped": skipped,
            "total_events": len(events),
            "strategy": strategy,
        })

    @staticmethod
    async def reroute(
        db: Session,
        original_route_code: str,
        replan_reason: str,
        excluded_vehicles: Optional[List[str]] = None,
        custom_weights: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        重路径规划（F006）
        
        流程：
        1. 读取原路径规划（Route）
        2. 通过 dispatch_id 找到关联的 dispatch_batch
        3. 获取同批次下所有 dispatch_codes
        4. 调用现有 RouteService.create_route_planning()（不修改它）
        5. 更新新路径规划的版本链字段
        6. 返回新路径规划编码
        
        Args:
            db: 数据库会话
            original_route_code: 原路径规划业务编号
            replan_reason: 重规划原因
            excluded_vehicles: 排除的车辆编码列表（可选，用于重规划规避异常车辆）
            custom_weights: 自定义权重参数（可选，用于AI驱动的重规划）
        
        Returns:
            统一响应格式 dict
        """
        try:
            # 1. 读取原路径规划
            original_route = db.query(Route).filter(
                Route.route_code == original_route_code
            ).first()

            if not original_route:
                return error_response(
                    code=40401,
                    message=f"原路径规划不存在: {original_route_code}",
                )

            # 2. 通过 dispatch_id 找到关联的 dispatch_batch
            dispatch = db.query(NodeDispatch).filter(
                NodeDispatch.id == original_route.dispatch_id
            ).first()

            if not dispatch:
                return error_response(
                    code=40001,
                    message=f"原路径规划关联的调度明细不存在",
                )

            batch = db.query(DispatchBatch).filter(
                DispatchBatch.id == dispatch.dispatch_batch_id
            ).first()

            if not batch:
                return error_response(
                    code=40001,
                    message=f"原路径规划关联的调度批次不存在",
                )

            # 3. 获取同批次下所有 dispatch_codes（仅重规划当前 dispatch 的路线）
            dispatch_codes = [dispatch.dispatch_code]

            # 4. 调用现有路径规划服务（不修改它）
            from services.route_service import RouteService

            route_result = await RouteService.create_route_planning(
                batch_code=batch.batch_code,
                dispatch_codes=dispatch_codes,
                db=db,
                excluded_vehicles=excluded_vehicles if excluded_vehicles else None,
                custom_weights=custom_weights,  # AI驱动的自定义权重
            )

            # 检查路径规划是否成功
            if route_result.get("code") != 0:
                return route_result

            new_routes_data = route_result["data"].get("routes", [])
            new_route_codes = [r["route_code"] for r in new_routes_data]

            # 5. 更新新路径规划的版本链字段
            for rc in new_route_codes:
                new_route = db.query(Route).filter(
                    Route.route_code == rc
                ).first()
                if new_route:
                    new_route.version = original_route.version + 1
                    new_route.parent_id = original_route.id
                    new_route.replan_reason = replan_reason
                    new_route.is_replan = True

            db.commit()

            new_route_code = new_route_codes[0] if new_route_codes else None

            # 重路径规划通知只入队，不在请求路径调用同步 SMTP/Webhook。
            enqueue_outbox(
                db,
                dedup_key=f"replan-route:{new_route_code}:completed",
                event_type="replan.completed",
                payload={
                    "original_schedule_code": batch.batch_code,
                    "new_schedule_code": new_route_code,
                    "strategy": "reroute",
                    "replan_reason": replan_reason,
                    "diff_summary": None,
                },
            )
            db.commit()

            return success_response(data={
                "batch_code": batch.batch_code,
                "route_codes": new_route_codes,
                "new_route_code": new_route_code,
                "version": original_route.version + 1,
                "is_replan": True,
                "replan_reason": replan_reason,
                "original_route_code": original_route_code,
            })

        except Exception as e:
            db.rollback()
            return error_response(code=40001, message=f"重路径规划失败: {str(e)}")
