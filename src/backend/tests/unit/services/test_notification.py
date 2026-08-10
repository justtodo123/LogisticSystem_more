"""
通知服务单元测试（T3-2）

测试目标：
- 三个渠道（Console / Email / WechatWork）的发送行为
- 通知内容模板渲染
- 分发器按配置路由（dev 环境默认 console）
- 通知失败不影响主业务流程（各渠道异常不抛出）
"""
import pytest
from unittest.mock import patch, AsyncMock

from config import settings
from services.notification.base import NotificationChannel
from services.notification.console import ConsoleChannel
from services.notification.email import EmailChannel
from services.notification.wechat_work import WechatWorkChannel
from services.notification.templates import (
    ALL_SCENARIOS,
    SCENARIO_ARRIVAL_CONFIRMED,
    SCENARIO_EXCEPTION_CREATED,
    SCENARIO_REPLAN_COMPLETED,
    SCENARIO_SCHEDULE_CONFIRMED,
    build_notification,
)
from services.notification.dispatcher import NotificationDispatcher, send_notification
from models.notification_config import NotificationConfig

CTX = {
    "schedule_code": "GS001",
    "event_code": "EX001",
    "original_schedule_code": "GS001",
    "new_schedule_code": "GS002",
    "package_code": "PKG001",
    "replan_reason": "节点容量不足",
    "description": "测试描述",
    "exception_type": "node",
    "recommended_action": "redispatch",
    "strategy": "partial",
    "diff_summary": {"affected_count": 2, "new_eta_delta": 0.5, "cost_delta": 12.0},
    "total_goods": 5,
    "total_distance": 100.0,
    "total_time": 10.0,
    "score": 0.8,
}


class TestChannels:
    """渠道发送行为"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_console_channel_prints(self, capsys):
        """Console 渠道：print 输出 + 返回 True"""
        channel = ConsoleChannel()
        ok = await channel.send("主题", "正文", {})
        captured = capsys.readouterr()
        assert ok is True
        assert "主题" in captured.out
        assert "正文" in captured.out

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_email_channel_skips_without_smtp(self):
        """Email 渠道：未配置 SMTP 时优雅跳过（返回 False，不抛异常）"""
        channel = EmailChannel(host="", user="")
        ok = await channel.send("主题", "正文", {})
        assert ok is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_email_channel_skips_without_recipients(self):
        """Email 渠道：已配置 SMTP 但无收件人时优雅跳过"""
        channel = EmailChannel(host="smtp.test.com", user="u", password="p", recipients=[])
        ok = await channel.send("主题", "正文", {})
        assert ok is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_wechat_skips_without_webhook(self):
        """企业微信渠道：未配置 Webhook URL 时优雅跳过"""
        channel = WechatWorkChannel(webhook_url="")
        ok = await channel.send("主题", "正文", {})
        assert ok is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_base_channel_abstract(self):
        """Base 渠道：抽象类不可直接实例化"""
        with pytest.raises(TypeError):
            NotificationChannel()


class TestTemplates:
    """通知模板渲染"""

    @pytest.mark.unit
    def test_all_scenarios_render(self):
        """四种场景均可渲染出 (subject, content)"""
        for scenario in ALL_SCENARIOS:
            subject, content = build_notification(scenario, CTX)
            assert subject
            assert content

    @pytest.mark.unit
    def test_unknown_scenario_raises(self):
        """未知场景抛出 ValueError"""
        with pytest.raises(ValueError):
            build_notification("unknown_scenario", {})

    @pytest.mark.unit
    def test_schedule_confirmed_content(self):
        """调度确认模板包含方案编码"""
        subject, content = build_notification(SCENARIO_SCHEDULE_CONFIRMED, CTX)
        assert "GS001" in content

    @pytest.mark.unit
    def test_replan_content_has_diff(self):
        """重规划模板包含差异报告"""
        subject, content = build_notification(SCENARIO_REPLAN_COMPLETED, CTX)
        assert "GS002" in content
        assert "受影响包裹" in content


class TestDispatcher:
    """通知分发器"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_dev_defaults_to_console(self, db_session):
        """dev 环境：无 DB 配置时默认 console 渠道（验收标准）"""
        results = await send_notification(
            db_session, SCENARIO_EXCEPTION_CREATED, CTX
        )
        assert results.get("console") == "ok"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_db_config_overrides_channels(self, db_session):
        """DB 配置可运行时切换渠道（dev 下显式配置同样生效）"""
        db_session.add(NotificationConfig(
            id=1,
            enabled_channels=["email"],
            email_recipients=["ops@example.com"],
            wechat_webhook_url=None,
        ))
        db_session.commit()

        dispatcher = NotificationDispatcher(db=db_session)
        cfg = dispatcher._load_config()
        assert cfg["channels"] == ["email"]  # 显式配置完全遵循
        assert cfg["email_recipients"] == ["ops@example.com"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_channel_failure_does_not_raise(self, db_session):
        """渠道发送失败不抛出异常，主流程不受影响（验收标准）"""
        dispatcher = NotificationDispatcher(db=db_session)
        # 模拟 console 渠道抛出异常
        with patch.object(
            dispatcher._channels["console"], "send",
            new=AsyncMock(side_effect=Exception("boom")),
        ):
            results = await dispatcher.notify(SCENARIO_EXCEPTION_CREATED, CTX)
        assert results.get("console") == "failed"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_notify_never_raises(self, db_session):
        """notify 对任何输入都不抛异常"""
        results = await dispatcher_notify_guard(db_session)
        assert isinstance(results, dict)


async def dispatcher_notify_guard(db_session):
    """helper：包裹一次完整 notify 调用"""
    dispatcher = NotificationDispatcher(db=db_session)
    return await dispatcher.notify("schedule_confirmed", CTX)


class TestFireAndForget:
    """同步上下文通知触发"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fire_and_forget_in_event_loop(self, db_session):
        """有事件循环时 create_task 后台执行，不阻塞"""
        from services.notification.dispatcher import (
            send_notification_fire_and_forget,
        )
        # 不应抛出
        send_notification_fire_and_forget(
            db_session, SCENARIO_ARRIVAL_CONFIRMED, CTX
        )
        # 让后台任务跑完
        import asyncio
        await asyncio.sleep(0.1)


class TestBusinessHooks:
    """业务服务通知钩子"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_exception_triggers_notification(
        self, db_session, test_nodes,
    ):
        """创建异常事件触发通知（console 输出）"""
        from services.exception_service import ExceptionService
        from schemas.exception_event import CreateExceptionEventRequest

        node_code = list(test_nodes.keys())[0]
        data = CreateExceptionEventRequest(
            exception_type="node",
            exception_subtype="capacity_limit",
            target_type="node",
            target_code=node_code,
            recommended_action="redispatch",
            description="容量不足告警测试",
        )
        result = await ExceptionService.create_exception_event(db=db_session, data=data)
        assert result["code"] == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_schedule_confirm_triggers_notification(
        self, db_session, test_nodes, test_orders, test_goods,
    ):
        """确认调度方案触发通知（console 输出）"""
        from services.schedule_service import ScheduleService

        order_codes = list(test_orders.keys())[:3]
        result = await ScheduleService.create_global_schedule(
            order_codes=order_codes,
            algorithm="traditional",
            db=db_session,
        )
        assert result["code"] == 0, result
        schedule_code = result["data"]["schedule_code"]
        confirm = await ScheduleService.confirm_schedule(
            schedule_code=schedule_code, db=db_session
        )
        assert confirm["code"] == 0, confirm
