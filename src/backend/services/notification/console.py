"""Console 通知渠道（开发环境，print 输出）"""
import logging
from typing import Dict, Any

from .base import NotificationChannel

logger = logging.getLogger(__name__)


class ConsoleChannel(NotificationChannel):
    """开发环境控制台渠道

    验收标准：`ENV=dev` 时通知通过 print() 输出到控制台。
    """
    name = "console"
    label = "控制台"

    async def send(
        self,
        subject: str,
        content: str,
        context: Dict[str, Any],
    ) -> bool:
        print(f"[通知:{self.name}] {subject}\n{content}")
        logger.info("控制台通知发送成功: %s", subject)
        return True
