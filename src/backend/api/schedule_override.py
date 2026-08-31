"""
人工干预调度 API（T2-4）

提供调度员在方案执行前对节点调度明细进行人工调整的端点：
- PUT /api/override/vehicle：更换调度车辆（自动校验 + 自动重算路线）
- PUT /api/override/driver：更换调度司机（自动校验）
- POST /api/override/recalculate：批量重算已干预明细的路线
- POST /api/override/undo：撤销干预，恢复到调整前状态
"""

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config.database import get_db
from api.dependencies import require_permission_with_optional_idempotency
from models.user import User
from models.node_dispatch import NodeDispatch
from models.dispatch_batch import DispatchBatch
from models.vehicle import Vehicle
from models.driver import Driver
from services.override_service import OverrideService
from services.log_service import LogService
from utils.response import error_response


router = APIRouter(prefix="/api/override", tags=["人工干预调度"])


class VehicleOverrideRequest(BaseModel):
    dispatch_code: str
    vehicle_code: str
    reason: Optional[str] = None


class DriverOverrideRequest(BaseModel):
    dispatch_code: str
    driver_code: str
    reason: Optional[str] = None


class RecalculateOverrideRequest(BaseModel):
    batch_code: str
    reason: Optional[str] = None


class UndoOverrideRequest(BaseModel):
    dispatch_code: str


@router.put("/vehicle", summary="人工干预：更换调度车辆")
async def override_vehicle(
    request: VehicleOverrideRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission_with_optional_idempotency("schedule:execute")),
):
    """
    更换某条调度明细的车辆。

    自动校验：容量 / 时窗 / 路径数 / 车辆状态，不满足时返回拒绝原因。
    校验通过后自动重算该明细的路线并生成新版本。
    """
    dispatch = db.query(NodeDispatch).filter(NodeDispatch.dispatch_code == request.dispatch_code).first()
    if not dispatch:
        return error_response(code=40400, message=f"调度明细不存在：{request.dispatch_code}")
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_code == request.vehicle_code).first()
    if not vehicle:
        return error_response(code=40400, message=f"车辆不存在：{request.vehicle_code}")

    result = OverrideService.override_vehicle(
        db, dispatch.id, vehicle.id, reason=request.reason,
    )

    if result["code"] == 0:
        LogService.log_event(
            event_name="schedule_override",
            user_id=current_user.id,
            role=current_user.role,
            event_data={
                "action": "override_vehicle",
                "dispatch_code": request.dispatch_code,
                "vehicle_code": request.vehicle_code,
                "reason": request.reason,
            },
            db=db,
        )
    return result


@router.put("/driver", summary="人工干预：更换调度司机")
async def override_driver(
    request: DriverOverrideRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission_with_optional_idempotency("schedule:execute")),
):
    """
    更换某条调度明细的司机。

    自动校验：驾时 / 排班 / 节点匹配 / 司机状态，不满足时返回拒绝原因。
    """
    dispatch = db.query(NodeDispatch).filter(NodeDispatch.dispatch_code == request.dispatch_code).first()
    if not dispatch:
        return error_response(code=40400, message=f"调度明细不存在：{request.dispatch_code}")
    driver = db.query(Driver).filter(Driver.driver_code == request.driver_code).first()
    if not driver:
        return error_response(code=40400, message=f"司机不存在：{request.driver_code}")

    result = OverrideService.override_driver(
        db, dispatch.id, driver.id, reason=request.reason,
    )

    if result["code"] == 0:
        LogService.log_event(
            event_name="schedule_override",
            user_id=current_user.id,
            role=current_user.role,
            event_data={
                "action": "override_driver",
                "dispatch_code": request.dispatch_code,
                "driver_code": request.driver_code,
                "reason": request.reason,
            },
            db=db,
        )
    return result


@router.post("/recalculate", summary="人工干预：批量重算已干预明细路线")
async def recalculate_override(
    request: RecalculateOverrideRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission_with_optional_idempotency("schedule:execute")),
):
    """
    对批次内已人工干预的调度明细批量重算路线（仅影响被调整的任务链）。
    """
    batch = db.query(DispatchBatch).filter(DispatchBatch.batch_code == request.batch_code).first()
    if not batch:
        return error_response(code=40400, message=f"调度批次不存在：{request.batch_code}")

    result = OverrideService.recalculate_after_override(
        db, batch.id, reason=request.reason,
    )

    if result["code"] == 0:
        LogService.log_event(
            event_name="schedule_override",
            user_id=current_user.id,
            role=current_user.role,
            event_data={
                "action": "recalculate_override",
                "batch_code": request.batch_code,
                "recalculated_count": result["data"]["recalculated_count"],
            },
            db=db,
        )
    return result


@router.post("/undo", summary="人工干预：撤销干预")
async def undo_override(
    request: UndoOverrideRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission_with_optional_idempotency("schedule:execute")),
):
    """
    撤销某条调度明细的人工干预，恢复到调整前状态（车辆/司机 + 路线版本回退）。
    """
    dispatch = db.query(NodeDispatch).filter(NodeDispatch.dispatch_code == request.dispatch_code).first()
    if not dispatch:
        return error_response(code=40400, message=f"调度明细不存在：{request.dispatch_code}")

    result = OverrideService.undo_override(db, dispatch.id)

    if result["code"] == 0:
        LogService.log_event(
            event_name="schedule_override",
            user_id=current_user.id,
            role=current_user.role,
            event_data={
                "action": "undo_override",
                "dispatch_code": request.dispatch_code,
            },
            db=db,
        )
    return result
