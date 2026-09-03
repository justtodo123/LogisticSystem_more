"""企业微信 Webhook 通知渠道"""
import logging
from typing import Any, Dict, Optional

import httpx

from config.settings import settings
from core.dependency import outbound_trace_headers, track_dependency

from .base import NotificationChannel

logger = logging.getLogger(__name__)


class WechatWorkChannel(NotificationChannel):
    """企业微信群机器人 Webhook 渠道

    Webhook URL 优先级：构造参数 > settings.WECHAT_WORK_WEBHOOK > 运行时 API 传入。
    未配置时优雅跳过（返回 False），不影响主业务流程。
    """
    name = "wechat_work"
    label = "企业微信"

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or settings.WECHAT_WORK_WEBHOOK

    async def send(
        self,
        subject: str,
        content: str,
        context: Dict[str, Any],
    ) -> bool:
        if not self.webhook_url:
            logger.warning("企业微信渠道未配置 Webhook URL，跳过发送")
            return False

        try:
            payload = {
                "msgtype": "text",
                "text": {"content": f"【{subject}】\n{content}"},
            }
            with track_dependency("wechat", "webhook") as dep:
                try:
                    async with httpx.AsyncClient(timeout=10) as client:
                        resp = await client.post(
                            self.webhook_url,
                            json=payload,
                            headers=outbound_trace_headers(),
                        )
                        resp.raise_for_status()
                except Exception as exc:
                    dep["status"] = "error"
                    dep["error_type"] = type(exc).__name__
                    logger.error("企业微信通知发送失败: %s", exc)
                    return False
            logger.info("企业微信通知发送成功: %s", subject)
            return True
        except Exception as e:  # 通知失败不影响主业务流程
            logger.error("企业微信通知发送失败: %s", e)
            return False
