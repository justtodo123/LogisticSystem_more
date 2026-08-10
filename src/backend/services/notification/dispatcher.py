"""通知分发器（T3-2）

按运行时配置路由到各渠道：
1. DB 有 NotificationConfig 记录 → 使用 DB 配置（API 可运行时切换）
2. 无记录 → 回退环境变量 settings.NOTIFICATION_CHANNELS
3. dev 环境始终保留 console 渠道（开发可见）

所有渠道发送均包裹 try/except，任何失败都不会影响主业务流程。
"""
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from config.settings import settings
from models.notification_config import NotificationConfig

from .base import NotificationChannel
from .console import ConsoleChannel
from .email import EmailChannel
from .templates import build_notification
from .wechat_work import WechatWorkChannel

logger = logging.getLogger(__name__)

DEFAULT_CHANNELS = ["console"]


class NotificationDispatcher:
    """通知分发器：按配置路由到各渠道"""

    def __init__(self, db: Optional[Session] = None):
        self._db = db
        self._channels: Dict[str, NotificationChannel] = {
            "console": ConsoleChannel(),
            "email": EmailChannel(),
            "wechat_work": WechatWorkChannel(),
        }

    def _load_config(self) -> Dict[str, Any]:
        """加载启用渠道与渠道参数（DB 优先，否则环境默认）"""
        channels: List[str] = []
        email_recipients: Optional[List[str]] = None
        webhook_url: Optional[str] = None

        cfg_row = None
        if self._db is not None:
            try:
                cfg_row = (
                    self._db.query(NotificationConfig)
                    .filter(NotificationConfig.id == 1)
                    .first()
                )
            except Exception as e:  # 表不存在/查询失败 → 回退环境默认
                logger.warning("读取通知配置失败，回退环境默认: %s", e)

        if cfg_row is not None:
            # DB 显式配置：完全遵循运行时配置（即使 dev 也以配置为准）
            channels = list(cfg_row.enabled_channels or [])
            email_recipients = cfg_row.email_recipients
            webhook_url = cfg_row.wechat_webhook_url
        else:
            # 环境默认：dev 环境始终保留 console（开发可见）
            channels = _parse_channels(settings.NOTIFICATION_CHANNELS)
            if settings.ENV == "dev" and "console" not in channels:
                channels.append("console")
            if settings.EMAIL_RECIPIENTS:
                email_recipients = [
                    r.strip() for r in settings.EMAIL_RECIPIENTS.split(",") if r.strip()
                ]
            webhook_url = settings.WECHAT_WORK_WEBHOOK or None

        return {
            "channels": channels,
            "email_recipients": email_recipients,
            "webhook_url": webhook_url,
        }

    async def notify(
        self,
        scenario: str,
        context: Dict[str, Any],
        subject: Optional[str] = None,
        content: Optional[str] = None,
    ) -> Dict[str, str]:
        """发送通知，返回 {渠道名: ok/failed}。永不抛出异常。"""
        if subject is None or content is None:
            try:
                subject, content = build_notification(scenario, context)
            except ValueError as e:
                logger.error("%s", e)
                return {"_error": str(e)}

        cfg = self._load_config()

        # 运行时渠道参数注入
        email_channel = self._channels["email"]
        if cfg["email_recipients"]:
            email_channel.recipients = cfg["email_recipients"]
        wechat_channel = self._channels["wechat_work"]
        if cfg["webhook_url"]:
            wechat_channel.webhook_url = cfg["webhook_url"]

        results: Dict[str, str] = {}
        for name in cfg["channels"]:
            channel = self._channels.get(name)
            if channel is None:
                logger.warning("未知通知渠道: %s（忽略）", name)
                continue
            try:
                ok = await channel.send(subject, content, context)
                results[name] = "ok" if ok else "failed"
            except Exception as e:  # 通知失败不影响主业务流程
                logger.error("通知渠道 %s 发送异常（已忽略）: %s", name, e)
                results[name] = "failed"
        return results


def _parse_channels(raw: str) -> List[str]:
    """解析逗号分隔的渠道配置，如 'console,email'"""
    if not raw:
        return list(DEFAULT_CHANNELS)
    return [c.strip() for c in raw.split(",") if c.strip()]


async def send_notification(
    db: Session,
    scenario: str,
    context: Dict[str, Any],
    subject: Optional[str] = None,
    content: Optional[str] = None,
) -> Dict[str, str]:
    """发送通知（供业务服务调用）。永不抛出异常。"""
    dispatcher = NotificationDispatcher(db=db)
    return await dispatcher.notify(scenario, context, subject, content)


def send_notification_fire_and_forget(
    db: Session,
    scenario: str,
    context: Dict[str, Any],
    subject: Optional[str] = None,
    content: Optional[str] = None,
) -> None:
    """同步上下文中触发异步通知（不阻塞、不抛异常）

    供同步业务方法（如到货确认）使用：
    - 已有事件循环（FastAPI 异步请求）→ create_task 后台执行
    - 无事件循环（纯同步调用/测试）→ 直接同步执行
    """
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # 无运行中的事件循环：同步执行
        try:
            asyncio.run(
                send_notification(db, scenario, context, subject, content)
            )
        except Exception as e:  # 通知失败不影响主业务流程
            logger.error("通知发送失败（已忽略）: %s", e)
        return

    loop.create_task(
        send_notification(db, scenario, context, subject, content)
    )
