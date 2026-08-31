"""
通知管理 API 路由（T3-2）

- GET  /api/notifications/config : 获取通知渠道配置
- PUT  /api/notifications/config : 运行时切换通知渠道
- POST /api/notifications/test   : 发送测试通知

需要角色：dispatcher / manager
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import require_permission, require_permission_with_optional_idempotency
from config.database import get_db
from models.user import User
from schemas.notification import (
    TestNotificationRequest,
    UpdateNotificationConfigRequest,
)
from services.log_service import LogService
from services.notification import ALL_SCENARIOS, send_notification
from services.notification_config_service import (
    get_notification_config,
    update_notification_config,
)
from utils.response import success_response

router = APIRouter(prefix="/api/notifications", tags=["消息通知"])


@router.get("/config")
async def get_config(
    current_user: User = Depends(require_permission("notifications:read")),
    db: Session = Depends(get_db),
):
    """获取通知渠道配置"""
    return get_notification_config(db)


@router.put("/config")
async def update_config(
    body: UpdateNotificationConfigRequest,
    current_user: User = Depends(require_permission_with_optional_idempotency("notifications:write")),
    db: Session = Depends(get_db),
):
    """运行时切换通知渠道（写 notification_configs 表，单行 id=1）"""
    result = update_notification_config(db, body)

    LogService.log_event(
        event_name="notification_config",
        user_id=current_user.id,
        role=current_user.role,
        event_data={
            "enabled_channels": result["data"].get("enabled_channels"),
            "email_recipients": result["data"].get("email_recipients"),
            "wechat_webhook_url": bool(result["data"].get("wechat_webhook_url")),
        },
        db=db,
    )
    return result


@router.post("/test")
async def test_notification(
    body: TestNotificationRequest,
    current_user: User = Depends(require_permission_with_optional_idempotency("notifications:write")),
    db: Session = Depends(get_db),
):
    """发送一条测试通知到所有启用渠道（验收标准：运行时切换渠道验证）"""
    if body.scenario not in ALL_SCENARIOS:
        return {
            "code": 40000,
            "message": f"无效的通知场景: {body.scenario}",
            "data": None,
        }

    context = {
        "schedule_code": "TEST-SCHEDULE",
        "event_code": "TEST-EXCEPTION",
        "original_schedule_code": "TEST-ORIG",
        "new_schedule_code": "TEST-NEW",
        "package_code": "TEST-PACKAGE",
        "replan_reason": "测试通知",
    }
    results = await send_notification(db, body.scenario, context)

    LogService.log_event(
        event_name="notification_test",
        user_id=current_user.id,
        role=current_user.role,
        event_data={"scenario": body.scenario, "results": results},
        db=db,
    )

    return success_response(data={
        "scenario": body.scenario,
        "results": results,
    })
