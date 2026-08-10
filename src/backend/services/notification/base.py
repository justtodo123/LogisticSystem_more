"""可插拔通知渠道抽象基类（T3-2）"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class NotificationChannel(ABC):
    """通知渠道抽象基类

    所有渠道必须实现 send()，并遵守以下约定：
    - 返回 True = 发送成功；返回 False = 配置缺失/发送失败
    - 任何异常都不得向上抛出（由分发器兜底捕获）
    """

    name: str = "base"
    label: str = "未命名渠道"

    @abstractmethod
    async def send(
        self,
        subject: str,
        content: str,
        context: Dict[str, Any],
    ) -> bool:
        """发送通知

        Args:
            subject: 通知主题
            content: 通知正文
            context: 业务上下文（订单/方案/异常等编号，供渠道模板使用）

        Returns:
            True 表示发送成功
        """
        raise NotImplementedError
