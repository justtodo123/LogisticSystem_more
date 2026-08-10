from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.sql import func
from .base import Base


class NotificationConfig(Base):
    """通知渠道配置表（T3-2 新增）

    单行记录（id=1）：
    - enabled_channels: 启用的渠道列表，如 ["console"] / ["console","email","wechat_work"]
    - email_recipients: 邮件收件人列表（运行时切换邮件渠道）
    - wechat_webhook_url: 企业微信群机器人 Webhook URL

    未写入记录时回退到环境变量配置（settings.NOTIFICATION_CHANNELS / SMTP_* / WECHAT_WORK_WEBHOOK）。
    """
    __tablename__ = "notification_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    enabled_channels = Column(JSON, nullable=False)  # ["console", "email", "wechat_work"]
    email_recipients = Column(JSON, nullable=True)  # ["ops@example.com"]
    wechat_webhook_url = Column(String(1024), nullable=True)
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
