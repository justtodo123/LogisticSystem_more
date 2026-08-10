"""
人工干预调度服务（T2-4）

调度员在方案确认/执行前对节点调度明细进行人工调整：
- override_vehicle: 更换调度车辆 → 校验约束（容量/时窗/路径数/状态）→ 更新分配 → 自动重算路线
- override_driver: 更换调度司机 → 校验约束（驾时/排班/节点匹配）→ 更新分配
- recalculate_after_override: 对批次内已干预的调度明细批量重算路线
- undo_override: 撤销干预，恢复到调整前状态（vehicle/driver + 路线版本链回退）

撤销机制：
- NodeDispatch.override_snapshot 记录首次干预前的原始分配（vehicle_id/driver_id）
- 换车后重算生成 Route 新版本（is_replan=True），撤销时删除新版本恢复原始路线
- GlobalSchedule.undo_version 记录撤销次数
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from models.node_dispatch import NodeDispatch
from models.dispatch_batch import DispatchBatch
from models.global_schedule import GlobalSchedule
from models.vehicle import Vehicle
from models.driver import Driver
from models.route import Route
from models.package import Package
from algorithms.route_planning import run_route_planning
from utils.response import success_response, error_response


def _total_package_weight(db: Session, dispatch: NodeDispatch) -> float:
    """计算调度明细承载的包裹总重（kg）"""
    tasks = dispatch.tasks
    if isinstance(tasks, str):
        import json
        tasks = json.loads(tasks)
    total = 0.0
    for task in tasks or []:
        if task.get("is_return"):
            continue
        for pkg_code in task.get("package_codes", []):
            pkg = db.query(Package).filter(Package.package_code == pkg_code).first()
            if pkg and pkg.weight is not None:
                total += float(pkg.weight)
    return total


def _time_span_hours(start, end) -> Optional[float]:
    """计算两个 TIME 对象之间的跨度（小时），跨零点时按当天窗口处理"""
    if start is None or end is None:
        return None
    start_min = start.hour * 60 + start.minute
    end_min = end.hour * 60 + end.minute
    if end_min < start_min:  # 跨零点窗口（如 22:00 ~ 06:00）
        end_min += 24 * 60
    return (end_min - start_min) / 60.0


def validate_vehicle(db: Session, dispatch: NodeDispatch, new_vehicle: Vehicle) -> List[str]:
    """校验更换车辆约束，返回违规原因列表（为空表示通过）

    约束项：
    1. 车辆状态必须为 idle（未在途/未占用）
    2. 容量：承载包裹总重 ≤ 有效载重（capacity × load_rate_max）
    3. 时窗：车辆可用时段覆盖当前时刻，且跨度 ≥ 任务时长
    4. 路径数：今日已规划路线数 < route_limit
    """
    errors: List[str] = []
    if new_vehicle.status != "idle":
        errors.append(f"车辆 {new_vehicle.vehicle_code} 当前状态为「{new_vehicle.status}」，不可用于人工干预")

    # 容量
    total_weight = _total_package_weight(db, dispatch)
    load_rate = new_vehicle.load_rate_max if new_vehicle.load_rate_max is not None else 0.9
    effective_capacity = float(new_vehicle.capacity) * load_rate
    if total_weight > effective_capacity:
        errors.append(
            f"该调度包裹总重 {total_weight:.1f}kg 超过 {new_vehicle.vehicle_code} "
            f"有效载重 {effective_capacity:.1f}kg（装载率上限 {load_rate:.0%}）"
        )

    # 时窗
    if new_vehicle.time_window_start and new_vehicle.time_window_end:
        now = datetime.now().time()
        if not (new_vehicle.time_window_start <= now <= new_vehicle.time_window_end):
            errors.append(
                f"车辆 {new_vehicle.vehicle_code} 当前不在可用时段"
                f"（{new_vehicle.time_window_start:%H:%M} ~ {new_vehicle.time_window_end:%H:%M}）"
            )
        span_hours = _time_span_hours(new_vehicle.time_window_start, new_vehicle.time_window_end)
        if span_hours is not None and dispatch.total_time is not None and span_hours < float(dispatch.total_time):
            errors.append(
                f"车辆 {new_vehicle.vehicle_code} 可用时段不足"
                f"（任务需 {float(dispatch.total_time):.1f}h，时段仅 {span_hours:.1f}h）"
            )

    # 路径数限制
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_route_count = (
        db.query(Route)
        .filter(Route.vehicle_id == new_vehicle.id, Route.created_at >= today_start)
        .count()
    )
    route_limit = new_vehicle.route_limit if new_vehicle.route_limit is not None else 5
    if today_route_count >= route_limit:
        errors.append(f"车辆 {new_vehicle.vehicle_code} 今日路线数已达上限（{route_limit} 条）")

    return errors


def validate_driver(db: Session, dispatch: NodeDispatch, new_driver: Driver) -> List[str]:
    """校验更换司机约束，返回违规原因列表（为空表示通过）

    约束项：
    1. 司机状态必须为 idle
    2. 驾时：任务时长 ≤ 单日最大驾驶时长
    3. 节点匹配：司机须位于车辆所在节点（与 F005 选司机规则一致）
    4. 排班：当前时刻在排班时段内
    """
    errors: List[str] = []
    if new_driver.status != "idle":
        errors.append(f"司机 {new_driver.driver_code} 当前状态为「{new_driver.status}」，不可用于人工干预")

    # 驾时（dispatch.total_time 单位为小时，与 F005 写入一致）
    if dispatch.total_time is not None and new_driver.max_drive_hours is not None:
        if float(dispatch.total_time) > float(new_driver.max_drive_hours):
            errors.append(
                f"任务时长 {float(dispatch.total_time):.1f}h 超过司机 {new_driver.driver_code} "
                f"单日最大驾驶时长 {float(new_driver.max_drive_hours):.1f}h"
            )

    # 节点匹配
    vehicle = db.query(Vehicle).filter(Vehicle.id == dispatch.vehicle_id).first()
    if vehicle and new_driver.node_id != vehicle.node_id:
        errors.append(
            f"司机 {new_driver.driver_code} 不在车辆 {vehicle.vehicle_code} 所在节点"
            f"（司机节点 ≠ 车辆节点），无法执行该调度"
        )

    # 排班
    if new_driver.shift_start and new_driver.shift_end:
        now = datetime.now().time()
        if not (new_driver.shift_start <= now <= new_driver.shift_end):
            errors.append(
                f"司机 {new_driver.driver_code} 当前不在排班时段"
                f"（{new_driver.shift_start:%H:%M} ~ {new_driver.shift_end:%H:%M}）"
            )

    return errors


def _recompute_route(
    db: Session,
    dispatch: NodeDispatch,
    vehicle: Vehicle,
    reason: str,
) -> Dict[str, Any]:
    """重算路线并写入新版本 Route（版本链 + is_replan 标记），返回 route_data"""
    route_data = run_route_planning(db, dispatch.id)
    latest_route = (
        db.query(Route)
        .filter(Route.dispatch_id == dispatch.id)
        .order_by(Route.version.desc())
        .first()
    )
    new_route = Route(
        route_code=route_data["route_code"],
        dispatch_id=route_data["dispatch_id"],
        vehicle_id=route_data["vehicle_id"],
        route_segments=route_data["route_segments"],
        total_distance=route_data["total_distance"],
        total_time=route_data["total_time"],
        total_emission=route_data["total_emission"],
        algorithm_type=route_data["algorithm_type"],
        version=(latest_route.version if latest_route else 0) + 1,
        parent_id=latest_route.id if latest_route else None,
        replan_reason=reason,
        is_replan=True,
    )
    db.add(new_route)
    db.flush()
    return route_data


class OverrideService:
    """人工干预调度服务"""

    @staticmethod
    def override_vehicle(
        db: Session,
        dispatch_id: int,
        new_vehicle_id: int,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """更换调度车辆：校验约束 → 更新分配 → 自动重算路线"""
        dispatch = db.query(NodeDispatch).filter(NodeDispatch.id == dispatch_id).first()
        if not dispatch:
            return error_response(code=40400, message=f"调度明细不存在：dispatch_id={dispatch_id}")

        new_vehicle = db.query(Vehicle).filter(Vehicle.id == new_vehicle_id).first()
        if not new_vehicle:
            return error_response(code=40400, message=f"车辆不存在：vehicle_id={new_vehicle_id}")

        if dispatch.vehicle_id == new_vehicle_id:
            return error_response(code=40001, message="目标车辆与当前车辆相同，无需更换")

        errors = validate_vehicle(db, dispatch, new_vehicle)
        if errors:
            return error_response(code=40001, message="人工干预被拒绝：" + "；".join(errors))

        old_vehicle = db.query(Vehicle).filter(Vehicle.id == dispatch.vehicle_id).first()

        # 记录撤销快照（仅首次干预时记录原始状态）
        if not dispatch.override_snapshot:
            dispatch.override_snapshot = {
                "vehicle_id": dispatch.vehicle_id,
                "driver_id": dispatch.driver_id,
                "old_vehicle_code": old_vehicle.vehicle_code if old_vehicle else None,
                "reason": reason,
                "overridden_at": datetime.now().isoformat(),
            }

        # 更新分配
        dispatch.vehicle_id = new_vehicle_id
        dispatch.version = (dispatch.version or 1) + 1
        reason_text = reason or (
            f"人工干预换车：{old_vehicle.vehicle_code if old_vehicle else ''} → {new_vehicle.vehicle_code}"
        )

        # 自动重算路线
        route_data = _recompute_route(db, dispatch, new_vehicle, reason_text)
        db.commit()

        return success_response(data={
            "dispatch_code": dispatch.dispatch_code,
            "vehicle_code": new_vehicle.vehicle_code,
            "driver_code": dispatch.driver.driver_code if dispatch.driver else None,
            "version": dispatch.version,
            "total_distance": float(route_data["total_distance"]),
            "total_time": float(route_data["total_time"]),
            "total_emission": float(route_data["total_emission"]),
            "route_code": route_data["route_code"],
            "recalculated": True,
            "can_undo": bool(dispatch.override_snapshot),
        })

    @staticmethod
    def override_driver(
        db: Session,
        dispatch_id: int,
        new_driver_id: int,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """更换调度司机：校验约束 → 更新分配"""
        dispatch = db.query(NodeDispatch).filter(NodeDispatch.id == dispatch_id).first()
        if not dispatch:
            return error_response(code=40400, message=f"调度明细不存在：dispatch_id={dispatch_id}")

        new_driver = db.query(Driver).filter(Driver.id == new_driver_id).first()
        if not new_driver:
            return error_response(code=40400, message=f"司机不存在：driver_id={new_driver_id}")

        if dispatch.driver_id == new_driver_id:
            return error_response(code=40001, message="目标司机与当前司机相同，无需更换")

        errors = validate_driver(db, dispatch, new_driver)
        if errors:
            return error_response(code=40001, message="人工干预被拒绝：" + "；".join(errors))

        old_driver = db.query(Driver).filter(Driver.id == dispatch.driver_id).first() if dispatch.driver_id else None

        if not dispatch.override_snapshot:
            dispatch.override_snapshot = {
                "vehicle_id": dispatch.vehicle_id,
                "driver_id": dispatch.driver_id,
                "old_vehicle_code": None,
                "reason": reason,
                "overridden_at": datetime.now().isoformat(),
            }

        dispatch.driver_id = new_driver_id
        dispatch.version = (dispatch.version or 1) + 1
        db.commit()

        return success_response(data={
            "dispatch_code": dispatch.dispatch_code,
            "vehicle_code": dispatch.vehicle.vehicle_code if dispatch.vehicle else None,
            "driver_code": new_driver.driver_code,
            "version": dispatch.version,
            "can_undo": bool(dispatch.override_snapshot),
        })

    @staticmethod
    def recalculate_after_override(
        db: Session,
        batch_id: int,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """批量重算：仅重算批次内已人工干预（override_snapshot 非空）的调度明细路线"""
        batch = db.query(DispatchBatch).filter(DispatchBatch.id == batch_id).first()
        if not batch:
            return error_response(code=40400, message=f"调度批次不存在：batch_id={batch_id}")

        overridden = (
            db.query(NodeDispatch)
            .filter(
                NodeDispatch.dispatch_batch_id == batch.id,
                NodeDispatch.override_snapshot.isnot(None),
            )
            .all()
        )

        recalculated = []
        for dispatch in overridden:
            vehicle = db.query(Vehicle).filter(Vehicle.id == dispatch.vehicle_id).first()
            if not vehicle:
                continue
            reason_text = reason or f"人工干预后重算：{dispatch.dispatch_code}"
            route_data = _recompute_route(db, dispatch, vehicle, reason_text)
            recalculated.append({
                "dispatch_code": dispatch.dispatch_code,
                "route_code": route_data["route_code"],
                "total_distance": float(route_data["total_distance"]),
                "total_time": float(route_data["total_time"]),
                "total_emission": float(route_data["total_emission"]),
            })
        db.commit()

        return success_response(data={
            "batch_code": batch.batch_code,
            "recalculated_count": len(recalculated),
            "dispatches": recalculated,
        })

    @staticmethod
    def undo_override(db: Session, dispatch_id: int) -> Dict[str, Any]:
        """撤销人工干预：恢复车辆/司机，删除干预生成的路线新版本，恢复到调整前状态"""
        dispatch = db.query(NodeDispatch).filter(NodeDispatch.id == dispatch_id).first()
        if not dispatch:
            return error_response(code=40400, message=f"调度明细不存在：dispatch_id={dispatch_id}")

        snapshot = dispatch.override_snapshot
        if not snapshot:
            return error_response(code=40001, message="该调度明细无人工干预记录，无需撤销")

        # 恢复车辆/司机
        dispatch.vehicle_id = snapshot.get("vehicle_id")
        dispatch.driver_id = snapshot.get("driver_id")
        dispatch.version = (dispatch.version or 1) + 1

        # 删除干预生成的路线新版本（保留最原始的路线）
        deleted_codes = []
        routes = (
            db.query(Route)
            .filter(Route.dispatch_id == dispatch.id)
            .order_by(Route.version.asc())
            .all()
        )
        for route in routes[1:]:
            deleted_codes.append(route.route_code)
            db.delete(route)

        # 清空快照
        dispatch.override_snapshot = None

        # undo_version 自增（GlobalSchedule 层）
        gs = None
        batch = db.query(DispatchBatch).filter(DispatchBatch.id == dispatch.dispatch_batch_id).first()
        if batch:
            gs = db.query(GlobalSchedule).filter(GlobalSchedule.id == batch.global_schedule_id).first()
            if gs:
                gs.undo_version = (gs.undo_version or 0) + 1
        db.flush()
        db.commit()

        return success_response(data={
            "dispatch_code": dispatch.dispatch_code,
            "vehicle_code": dispatch.vehicle.vehicle_code if dispatch.vehicle else None,
            "driver_code": dispatch.driver.driver_code if dispatch.driver else None,
            "version": dispatch.version,
            "undo_version": gs.undo_version if gs else None,
            "deleted_route_codes": deleted_codes,
        })
