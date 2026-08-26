"""
导出 API（T5-1）：订单报表 / 调度结果导出

- POST /api/export/orders?format=xlsx|csv — 下载完整订单表
- POST /api/export/schedule?schedule_code=xxx&format=xlsx|csv — 下载调度结果
"""
from datetime import datetime

from fastapi import APIRouter, Depends, Query

from core.error_codes import CODE_NOT_FOUND
from core.errors import DomainError
from fastapi.responses import Response
from sqlalchemy.orm import Session

from api.dependencies import require_dispatcher
from config.database import get_db
from models.user import User
from services import export_service

router = APIRouter(prefix="/api/export", tags=["数据导出"])

# 支持的文件格式 → MIME 类型
MEDIA_TYPES = {
    "csv": "text/csv; charset=utf-8",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

SUPPORTED_FORMAT = Query("xlsx", pattern="^(csv|xlsx)$", description="导出格式：csv / xlsx")


@router.post("/orders", summary="导出订单报表")
async def export_orders(
    format: str = SUPPORTED_FORMAT,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dispatcher),
):
    """导出完整订单表，返回文件下载。

    需要角色：dispatcher / admin
    """
    data = export_service.export_orders(format, db)
    filename = f"orders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
    return Response(
        content=data,
        media_type=MEDIA_TYPES[format],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/schedule", summary="导出调度结果")
async def export_schedule(
    schedule_code: str = Query(..., description="调度方案编号"),
    format: str = SUPPORTED_FORMAT,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dispatcher),
):
    """导出指定调度方案结果，返回文件下载。

    需要角色：dispatcher / admin
    """
    try:
        data = export_service.export_schedule(format, schedule_code, db)
    except ValueError:
        raise DomainError(CODE_NOT_FOUND)
    filename = f"schedule_{schedule_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
    return Response(
        content=data,
        media_type=MEDIA_TYPES[format],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
