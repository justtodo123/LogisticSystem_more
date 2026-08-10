"""
算法单元测试：调度结果解释器（T2-3）

测试目标：
- analyze_constraints: 约束命中分析（同订单汇聚/容量/时效/满载率）
- build_explanation: 结构化解释结构（score_breakdown/composite_score/constraints_hit/alternatives/summary）
- build_prompt_section: AI 提示词包含结构化数据
- GET 详情响应携带 explanation（经 schedule_service）
"""
import pytest

from algorithms.explainer import (
    analyze_constraints,
    build_explanation,
    build_prompt_section,
)
from algorithms.global_schedule import global_schedule


class TestAnalyzeConstraints:
    """约束命中分析"""

    @pytest.mark.unit
    def test_converging_orders_reported(self):
        """多货物订单汇聚到相同 L1 → 约束命中（info）"""
        schedule_data = {
            "goods_schedules": [
                {"goods_code": "G1", "order_code": "O1", "path": ["SC001", "SO001", "SO010"]},
                {"goods_code": "G2", "order_code": "O1", "path": ["SC002", "SO001", "SO010"]},
            ]
        }
        constraints = analyze_constraints(schedule_data)
        converge = [c for c in constraints if c["name"] == "同订单汇聚"]
        assert converge
        assert converge[0]["hit"] is True
        assert "汇聚" in converge[0]["detail"]

    @pytest.mark.unit
    def test_diverging_orders_flagged_warning(self):
        """多货物订单分散到不同 L1 → 警告"""
        schedule_data = {
            "goods_schedules": [
                {"goods_code": "G1", "order_code": "O1", "path": ["SC001", "SO001", "SO010"]},
                {"goods_code": "G2", "order_code": "O1", "path": ["SC002", "SO002", "SO010"]},
            ]
        }
        constraints = analyze_constraints(schedule_data)
        converge = [c for c in constraints if c["name"] == "同订单汇聚"]
        assert converge[0]["severity"] == "warning"
        assert converge[0]["hit"] is True

    @pytest.mark.unit
    def test_l1_capacity_reported(self):
        """L1 容量约束：统计各 L1 承载货物数"""
        schedule_data = {
            "goods_schedules": [
                {"goods_code": "G1", "order_code": "O1", "path": ["SC001", "SO001", "SO010"]},
                {"goods_code": "G2", "order_code": "O2", "path": ["SC002", "SO001", "SO010"]},
            ]
        }
        constraints = analyze_constraints(schedule_data)
        cap = [c for c in constraints if c["name"] == "L1 容量"]
        assert cap
        assert "SO001" in cap[0]["detail"]
        assert "2" in cap[0]["detail"]

    @pytest.mark.unit
    def test_on_time_warning_when_rate_low(self):
        """时效率 < 100% → 警告"""
        constraints = analyze_constraints({"goods_schedules": [], "metrics": {"on_time_rate": 0.6}})
        on_time = [c for c in constraints if c["name"] == "最大存储时长"]
        assert on_time
        assert on_time[0]["severity"] == "warning"

    @pytest.mark.unit
    def test_empty_schedule_no_crash(self):
        """空方案不崩溃"""
        assert analyze_constraints({"goods_schedules": []}) == []


class TestBuildExplanation:
    """结构化解释构建"""

    @pytest.mark.unit
    def test_explanation_structure(self):
        """解释包含 score_breakdown/composite_score/constraints_hit/alternatives/summary"""
        schedule_data = {
            "goods_schedules": [
                {"goods_code": "G1", "order_code": "O1", "path": ["SC001", "SO001", "SO010"]},
            ],
            "total_distance": 120.5,
            "total_time": 3.2,
            "total_goods": 1,
            "objective_scores": {"distance": 0.8, "time": 0.7, "load_rate": 0.5,
                                 "on_time_rate": 0.5, "cost": 0.6},
            "score_breakdown": {
                "overall": 0.5,
                "breakdown": {
                    "distance": {"raw": 120.5, "weight": 0.3, "direction": "minimize", "normalized": 0.5},
                    "time": {"raw": 3.2, "weight": 0.25, "direction": "minimize", "normalized": 0.5},
                    "load_rate": {"raw": 0.5, "weight": 0.2, "direction": "maximize", "normalized": 0.5},
                    "on_time_rate": {"raw": 1.0, "weight": 0.15, "direction": "maximize", "normalized": 0.5},
                    "cost": {"raw": 180.0, "weight": 0.1, "direction": "minimize", "normalized": 0.5},
                },
            },
            "composite_score": 0.66,
            "alternatives": [
                {"profile": "time_first", "overall_score": 0.6, "total_distance": 130.0, "total_time": 2.8}
            ],
        }
        exp = build_explanation(schedule_data)
        assert "score_breakdown" in exp
        assert "composite_score" in exp
        assert exp["composite_score"] == 0.66
        assert "constraints_hit" in exp
        assert "alternatives" in exp
        assert exp["alternatives"][0]["profile"] == "time_first"
        assert "summary" in exp
        # score_breakdown 为列表，含各目标
        objectives = [i["objective"] for i in exp["score_breakdown"]]
        assert "distance" in objectives
        assert "load_rate" in objectives
        dist_item = next(i for i in exp["score_breakdown"] if i["objective"] == "distance")
        assert dist_item["raw"] == 120.5
        assert dist_item["score"] == 0.8

    @pytest.mark.unit
    def test_explanation_from_global_schedule(self, db_session, test_nodes, test_orders, test_goods):
        """F007 输出可直接构建解释（T2-2/T2-3 联动）"""
        result = global_schedule(order_codes=None, algorithm="traditional", db=db_session)
        exp = build_explanation(result)
        assert len(exp["score_breakdown"]) == 5  # 5 个目标
        assert exp["composite_score"] == result["composite_score"]
        # 18 票货物、9 订单 → 同订单汇聚约束命中
        converge = [c for c in exp["constraints_hit"] if c["name"] == "同订单汇聚"]
        assert converge
        # 备选方案传递
        assert len(exp["alternatives"]) >= 2


class TestBuildPromptSection:
    """AI 提示词结构化数据"""

    @pytest.mark.unit
    def test_prompt_contains_structured_data(self, db_session, test_nodes, test_orders, test_goods):
        """prompt 包含分项评分/约束/备选，而非仅方案 ID"""
        result = global_schedule(order_codes=None, algorithm="traditional", db=db_session)
        section = build_prompt_section(result)
        assert "分项目标评分" in section
        assert "distance" in section
        assert "约束分析" in section
        assert "同订单汇聚" in section
        assert "备选方案" in section
        assert "balanced" in section or "distance_first" in section
