"""
调度算法策略模式基础定义（T2-1）

定义统一的调度策略抽象基类 `SchedulingStrategy`、结果数据类 `ScheduleResult`
以及测试用空策略 `DummyStrategy`。具体算法（F007/F005/F006）通过继承该基类
实现可插拔：更换算法只需新增策略类并在 factory 中注册，无需改动服务层。

使用方式：
    strategy = get_global_strategy()          # 读取 algorithm_config.json 的 engine
    result = strategy.schedule(db, order_codes=..., algorithm="traditional")
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ScheduleResult:
    """
    调度结果统一数据类。

    注：为保持与既有算法模块（global_schedule / node_dispatch）的返回格式完全一致，
    贪心策略的 `schedule()` 仍返回普通 dict；本数据类供后续结构化策略（多目标评分、
    OR-Tools 等）及测试桩使用。
    """
    data: Dict[str, Any] = field(default_factory=dict)
    code: int = 0
    message: str = "success"

    def to_dict(self) -> Dict[str, Any]:
        return self.data


class SchedulingStrategy(ABC):
    """
    调度算法策略抽象基类。

    子类需实现：
        name: 策略标识（与 algorithm_config.json 的 "engine" 对应）
        schedule(db, **kwargs): 执行调度，返回结果字典
    """

    name: str = "base"

    @abstractmethod
    def schedule(self, db: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        执行调度。

        Args:
            db: 数据库会话
            **kwargs: 策略特定参数（订单编码、算法类型、排除节点/车辆等）

        Returns:
            调度结果字典（格式与既有算法模块保持一致）
        """
        raise NotImplementedError


class DummyStrategy(SchedulingStrategy):
    """
    测试用空策略：不执行真实调度，返回固定结果。

    用于验证策略模式的可插拔性——通过工厂切换 engine 时，服务层无需改动即可
    注入任意策略（见 tests/unit/algorithms/test_strategy_factory.py）。
    """

    name = "dummy"

    def __init__(self, result: Optional[Dict[str, Any]] = None) -> None:
        self._result: Dict[str, Any] = result or {
            "schedule_code": "GS_DUMMY",
            "order_codes": [],
            "total_goods": 0,
            "total_distance": 0.0,
            "total_time": 0.0,
            "score": 0.0,
            "goods_schedules": [],
            "message": "dummy strategy result",
        }

    def schedule(self, db: Any, **kwargs: Any) -> Dict[str, Any]:
        return dict(self._result)
