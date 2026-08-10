"""
算法单元测试：策略模式工厂（T2-1）

测试目标：
- get_global_strategy / get_dispatch_strategy 按配置返回对应策略
- Greedy 策略行为与既有算法函数一致（可插拔且不破坏既有行为）
- DummyStrategy 可注入并按预期返回（验证策略可插拔性）
"""
import pytest

from algorithms.factory import (
    get_global_strategy,
    get_dispatch_strategy,
    load_algorithm_config,
)
from algorithms.base import DummyStrategy
from algorithms.global_schedule import GreedyGlobalScheduleStrategy
from algorithms.node_dispatch import GreedyNodeDispatchStrategy


class TestFactoryEngineSelection:
    """工厂按 engine 选择策略"""

    @pytest.mark.unit
    def test_config_has_engine_greedy(self):
        """algorithm_config.json 默认 engine=greedy"""
        config = load_algorithm_config()
        assert config.get("engine") == "greedy"

    @pytest.mark.unit
    def test_get_global_strategy_default_is_greedy(self):
        """默认（读取配置）返回 GreedyGlobalScheduleStrategy"""
        strategy = get_global_strategy()
        assert isinstance(strategy, GreedyGlobalScheduleStrategy)

    @pytest.mark.unit
    def test_get_dispatch_strategy_default_is_greedy(self):
        """默认（读取配置）返回 GreedyNodeDispatchStrategy"""
        strategy = get_dispatch_strategy()
        assert isinstance(strategy, GreedyNodeDispatchStrategy)

    @pytest.mark.unit
    def test_get_global_strategy_dummy(self):
        """显式指定 engine='dummy' 时返回 DummyStrategy"""
        strategy = get_global_strategy(engine="dummy")
        assert isinstance(strategy, DummyStrategy)

    @pytest.mark.unit
    def test_get_strategy_unknown_falls_back_to_greedy(self):
        """未知 engine 回退到 greedy"""
        assert isinstance(get_global_strategy(engine="unknown"), GreedyGlobalScheduleStrategy)
        assert isinstance(get_dispatch_strategy(engine="unknown"), GreedyNodeDispatchStrategy)


class TestStrategyBehavior:
    """策略行为与既有算法一致"""

    @pytest.mark.unit
    def test_dummy_strategy_returns_fixed_result(self):
        """DummyStrategy 返回固定结果，不依赖数据库"""
        strategy = DummyStrategy()
        result = strategy.schedule(db=None)
        assert result["schedule_code"] == "GS_DUMMY"
        assert result["total_goods"] == 0

    @pytest.mark.unit
    def test_dummy_strategy_custom_result(self):
        """DummyStrategy 支持自定义返回结果（注入测试场景）"""
        custom = {"schedule_code": "GS_X", "total_goods": 5}
        strategy = DummyStrategy(result=custom)
        result = strategy.schedule(db=None)
        assert result == custom

    @pytest.mark.unit
    def test_greedy_global_strategy_matches_module_function(
        self, db_session, test_nodes, test_orders, test_goods
    ):
        """Greedy 策略 schedule() 结果与直接调用 global_schedule() 一致"""
        from algorithms.global_schedule import global_schedule
        from unittest.mock import patch

        # 编号生成器带内存序号（连续调用会自增），patch 成固定值以便逐字段比对
        with patch("algorithms.global_schedule._generate_schedule_code", return_value="GS_FIXED"):
            strategy = get_global_strategy()
            via_strategy = strategy.schedule(
                db=db_session, order_codes=None, algorithm="traditional"
            )
            via_function = global_schedule(
                order_codes=None, algorithm="traditional", db=db_session
            )
        assert via_strategy == via_function
