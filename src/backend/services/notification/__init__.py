"""消息通知服务（T3-2）"""
from .base import NotificationChannel
from .console import ConsoleChannel
from .dispatcher import (
    NotificationDispatcher,
    send_notification,
    send_notification_fire_and_forget,
)
from .email import EmailChannel
from .templates import (
    ALL_SCENARIOS,
    SCENARIO_ARRIVAL_CONFIRMED,
    SCENARIO_EXCEPTION_CREATED,
    SCENARIO_REPLAN_COMPLETED,
    SCENARIO_SCHEDULE_CONFIRMED,
)
from .wechat_work import WechatWorkChannel

__all__ = [
    "NotificationChannel",
    "ConsoleChannel",
    "EmailChannel",
    "WechatWorkChannel",
    "NotificationDispatcher",
    "send_notification",
    "send_notification_fire_and_forget",
    "ALL_SCENARIOS",
    "SCENARIO_SCHEDULE_CONFIRMED",
    "SCENARIO_EXCEPTION_CREATED",
    "SCENARIO_REPLAN_COMPLETED",
    "SCENARIO_ARRIVAL_CONFIRMED",
]
