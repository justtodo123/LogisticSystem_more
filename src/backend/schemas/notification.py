"""
通知配置 Schema（T3-2）
"""
from pydantic import BaseModel, Field, model_validator
from typing import List, Optional

# 允许的渠道
ALLOWED_CHANNELS = {"console", "email", "wechat_work"}


class NotificationConfigResponse(BaseModel):
    """通知配置响应体"""
    enabled_channels: List[str]
    email_recipients: List[str]
    wechat_webhook_url: Optional[str] = None
    environment: str


class UpdateNotificationConfigRequest(BaseModel):
    """更新通知配置请求体"""
    enabled_channels: Optional[List[str]] = Field(
        None, description="启用的渠道：console / email / wechat_work"
    )
    email_recipients: Optional[List[str]] = Field(
        None, description="邮件收件人列表"
    )
    wechat_webhook_url: Optional[str] = Field(
        None, description="企业微信 Webhook URL"
    )

    @model_validator(mode="after")
    def validate_channels(self) -> "UpdateNotificationConfigRequest":
        if self.enabled_channels is not None:
            invalid = set(self.enabled_channels) - ALLOWED_CHANNELS
            if invalid:
                raise ValueError(
                    f"无效的通知渠道: {', '.join(sorted(invalid))}，"
                    f"允许值: {', '.join(sorted(ALLOWED_CHANNELS))}"
                )
        return self


class TestNotificationRequest(BaseModel):
    """测试通知请求体（可选：指定场景）"""
    scenario: str = "exception_created"
