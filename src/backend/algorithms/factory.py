"""
调度算法策略工厂（T2-1）

按 `algorithm_config.json` 的 "engine" 字段选择具体调度策略，实现算法可插拔：

    strategy = get_global_strategy()      # 全局调度（F007）
    strategy = get_dispatch_strategy()    # 节点调度（F005）
    result = strategy.schedule(db, ...)

新增算法时：实现对应策略类（继承 algorithms.base.SchedulingStrategy），
在下方注册表中登记即可，服务层无需改动。
"""
import os
import json
from typing import Any, Dict, Optional

from algorithms.base import SchedulingStrategy, DummyStrategy
from algorithms.global_schedule import GreedyGlobalScheduleStrategy
from algorithms.node_dispatch import GreedyNodeDispatchStrategy


def _config_path() -> str:
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config", "algorithm_config.json",
    )


def load_algorithm_config() -> Dict[str, Any]:
    """加载算法配置文件（带缓存语义，供策略与评分模块共用）"""
    with open(_config_path(), "r", encoding="utf-8") as f:
        return json.load(f)


def _load_engine() -> str:
    """读取当前默认调度引擎标识"""
    config = load_algorithm_config()
    return config.get("engine", "greedy")


# 全局调度策略注册表：engine 名 → 策略实例
_GLOBAL_STRATEGIES: Dict[str, SchedulingStrategy] = {
    "greedy": GreedyGlobalScheduleStrategy(),
    "dummy": DummyStrategy(),
}

# 节点调度策略注册表：engine 名 → 策略实例
_DISPATCH_STRATEGIES: Dict[str, SchedulingStrategy] = {
    "greedy": GreedyNodeDispatchStrategy(),
    "dummy": DummyStrategy(),
}


def get_global_strategy(engine: Optional[str] = None) -> SchedulingStrategy:
    """
    获取全局调度策略。

    Args:
        engine: 策略标识；缺省时读取 algorithm_config.json 的 "engine"。

    Returns:
        对应策略实例；未知 engine 时回退到 greedy。
    """
    engine = engine or _load_engine()
    return _GLOBAL_STRATEGIES.get(engine, _GLOBAL_STRATEGIES["greedy"])


def get_dispatch_strategy(engine: Optional[str] = None) -> SchedulingStrategy:
    """
    获取节点调度策略。

    Args:
        engine: 策略标识；缺省时读取 algorithm_config.json 的 "engine"。

    Returns:
        对应策略实例；未知 engine 时回退到 greedy。
    """
    engine = engine or _load_engine()
    return _DISPATCH_STRATEGIES.get(engine, _DISPATCH_STRATEGIES["greedy"])
