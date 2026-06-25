"""
到货确认 API 路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from services.arrival_confirm_service import ArrivalConfirmService
from schemas.arrival_confirm import (
    ArrivalConfirmRequest,
    BatchArrivalConfirmRequest,
    ArrivalPackageResponse
)
from core.error_codes import CODE_SUCCESS, CODE_INTERNAL_ERROR, CODE_PACKAGE_NOT_FOUND
from config.database import get_db

router = APIRouter(prefix="/api/simulation", tags=["simulation"])


@router.post("/confirm-arrival")
async def confirm_arrival(
    request: ArrivalConfirmRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    单个到货确认
    
    正常路径：包裹 delivered，货物 pending_pack，触发 F021 重新打包
    异常路径：包裹 exception，货物 exception，订单 exception，写入 exception_events
    """
    try:
        result = ArrivalConfirmService.confirm_arrival(
            db=db,
            schedule_code=request.schedule_code,
            package_code=request.package_code,
            is_normal=request.is_normal,
            exception_subtype=request.exception_subtype,
            remark=request.remark
        )
        db.commit()
        return {
            "code": CODE_SUCCESS,
            "message": "success",
            "data": result,
            "meta": {"degraded": False, "degraded_reason": None}
        }
    except Exception as e:
        db.rollback()
        return {"code": CODE_INTERNAL_ERROR, "message": f"到货确认失败：{str(e)}", "data": None}


@router.post("/confirm-arrival-batch")
async def confirm_arrival_batch(
    request: BatchArrivalConfirmRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    批量到货确认（事务性，任一失败则全部回滚）
    
    请求体：
    {
        "schedule_code": "GS20260609001",
        "confirmations": [
            {"package_code": "PKG001", "is_normal": true},
            {"package_code": "PKG002", "is_normal": false, "exception_subtype": "damaged"}
        ]
    }
    """
    try:
        result = ArrivalConfirmService.confirm_arrival_batch(
            db=db,
            schedule_code=request.schedule_code,
            confirmations=[conf.dict() for conf in request.confirmations]
        )
        db.commit()
        return {
            "code": CODE_SUCCESS,
            "message": "success",
            "data": result,
            "meta": {"degraded": False, "degraded_reason": None}
        }
    except Exception as e:
        db.rollback()
        return {"code": CODE_INTERNAL_ERROR, "message": f"批量到货确认失败：{str(e)}", "data": None}


@router.get("/arrival-packages")
async def get_arrival_packages(
    schedule_code: str,
    node_code: str = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    查询到站包裹（状态为 in_transit 或 delivered 的包裹）
    
    参数：
    - schedule_code：调度方案编号（必填）
    - node_code：到站节点编号（可选，不传则查所有）
    """
    try:
        results = ArrivalConfirmService.get_arrival_packages(
            db=db,
            schedule_code=schedule_code,
            node_code=node_code
        )
        return {
            "code": CODE_SUCCESS,
            "message": "success",
            "data": results,
            "meta": {"degraded": False, "degraded_reason": None}
        }
    except Exception as e:
        return {"code": CODE_INTERNAL_ERROR, "message": f"查询到站包裹失败：{str(e)}", "data": None}
