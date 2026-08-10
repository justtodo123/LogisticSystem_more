"""
通知配置服务（T3-2）

提供通知渠道配置的读取/更新/测试，运行时切换渠道。
"""
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from config.settings import settings
from models.notification_config import NotificationConfig
from schemas.notification import UpdateNotificationConfigRequest
from utils.response import success_response


def _env_recipients() -> List[str]:
    if not settings.EMAIL_RECIPIENTS:
        return []
    return [r.strip() for r in settings.EMAIL_RECIPIENTS.split(",") if r.strip()]


def _env_channels() -> List[str]:
    raw = settings.NOTIFICATION_CHANNELS or "console"
    channels = [c.strip() for c in raw.split(",") if c.strip()]
    if settings.ENV == "dev" and "console" not in channels:
        channels.append("console")
    return channels


def get_notification_config(db: Session) -> Dict[str, Any]:
    """读取当前通知配置（DB 优先，否则环境默认）"""
    cfg = db.query(NotificationConfig).filter(NotificationConfig.id == 1).first()
    if cfg is not None:
        return success_response(data={
            "enabled_channels": cfg.enabled_channels or [],
            "email_recipients": cfg.email_recipients or [],
            "wechat_webhook_url": cfg.wechat_webhook_url,
            "environment": settings.ENV,
        })
    return success_response(data={
        "enabled_channels": _env_channels(),
        "email_recipients": _env_recipients(),
        "wechat_webhook_url": settings.WECHAT_WORK_WEBHOOK or None,
        "environment": settings.ENV,
    })


def update_notification_config(
    db: Session,
    data: UpdateNotificationConfigRequest,
) -> Dict[str, Any]:
    """更新通知配置（运行时切换渠道），单行 upsert（id=1）"""
    cfg = db.query(NotificationConfig).filter(NotificationConfig.id == 1).first()
    if cfg is None:
        cfg = NotificationConfig(
            id=1,
            enabled_channels=_env_channels(),
            email_recipients=_env_recipients(),
            wechat_webhook_url=settings.WECHAT_WORK_WEBHOOK or None,
        )
        db.add(cfg)

    if data.enabled_channels is not None:
        cfg.enabled_channels = data.enabled_channels
    if data.email_recipients is not None:
        cfg.email_recipients = data.email_recipients
    if data.wechat_webhook_url is not None:
        cfg.wechat_webhook_url = data.wechat_webhook_url

    db.commit()
    db.refresh(cfg)

    return success_response(data={
        "enabled_channels": cfg.enabled_channels,
        "email_recipients": cfg.email_recipients or [],
        "wechat_webhook_url": cfg.wechat_webhook_url,
        "environment": settings.ENV,
    })
