"""SMTP 邮件通知渠道"""
import logging
import smtplib
from email.header import Header
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

from config.settings import settings

from .base import NotificationChannel

logger = logging.getLogger(__name__)


class EmailChannel(NotificationChannel):
    """SMTP 邮件渠道

    配置优先级：构造参数 > settings（.env 的 SMTP_*）> 运行时 API 传入的收件人。
    未配置 SMTP 或收件人时优雅跳过（返回 False），不影响主业务流程。
    """
    name = "email"
    label = "邮件"

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        from_addr: Optional[str] = None,
        recipients: Optional[List[str]] = None,
    ):
        self.host = host or settings.SMTP_HOST
        self.port = port or settings.SMTP_PORT
        self.user = user or settings.SMTP_USER
        self.password = password or settings.SMTP_PASSWORD
        self.from_addr = (
            from_addr
            or settings.SMTP_FROM
            or (settings.SMTP_USER or "no-reply@local")
        )
        self.recipients = recipients or []

    @property
    def configured(self) -> bool:
        return bool(self.host and self.user)

    async def send(
        self,
        subject: str,
        content: str,
        context: Dict[str, Any],
    ) -> bool:
        if not self.configured:
            logger.warning("邮件渠道未配置 SMTP（SMTP_HOST/SMTP_USER），跳过发送")
            return False
        if not self.recipients:
            logger.warning("邮件渠道未配置收件人，跳过发送")
            return False

        msg = MIMEText(content, "plain", "utf-8")
        msg["Subject"] = Header(subject, "utf-8")
        msg["From"] = self.from_addr
        msg["To"] = ", ".join(self.recipients)

        try:
            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                if self.user and self.password:
                    server.login(self.user, self.password)
                server.sendmail(self.from_addr, self.recipients, msg.as_string())
            logger.info("邮件通知发送成功: %s -> %s", subject, self.recipients)
            return True
        except Exception as e:  # 通知失败不影响主业务流程
            logger.error("邮件通知发送失败: %s", e)
            return False
