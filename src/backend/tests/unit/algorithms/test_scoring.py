"""
算法单元测试：多目标评分引擎（T2-2）

测试目标：
- normalize_scores: min-max 归一化，direction 决定高分方向
- weighted_score: 按权重加权综合分
- score_breakdown: 单方案评分拆解
- rank_candidates: 跨候选排序，权重配置影响排序结果
- global_schedule 响应携带 objective_scores / score_breakdown / composite_score / alternatives
"""
import pytest

from algorithms import scoring
from algorithms.scoring import (
    normalize_scores,
    weighted_score,
    score_breakdown,
    rank_candidates,
)
from algorithms.global_schedule import global_schedule


OBJECTIVES = {
    "distance": {"weight": 0.5, "direction": "minimize", "metric": "distance"},
    "time": {"weight": 0.5, "direction": "minimize", "metric": "time"},
}


class TestNormalizeScores:
    """min-max 归一化"""

    @pytest.mark.unit
    def test_minimize_lower_is_better(self):
        """direction=minimize：原始值越低，归一化分越高"""
        assert normalize_scores([10.0, 20.0, 30.0], "minimize") == pytest.approx([1.0, 0.5, 0.0])

    @pytest.mark.unit
    def test_maximize_higher_is_better(self):
        """direction=maximize：原始值越高，归一化分越高"""
        assert normalize_scores([10.0, 20.0, 30.0], "maximize") == pytest.approx([0.0, 0.5, 1.0])

    @pytest.mark.unit
    def test_all_equal_returns_neutral(self):
        """全部相等（无法区分）时返回中性分 0.5"""
        assert normalize_scores([7.0, 7.0, 7.0], "minimize") == [0.5, 0.5, 0.5]

    @pytest.mark.unit
    def test_empty_returns_empty(self):
        assert normalize_scores([], "minimize") == []

    @pytest.mark.unit
    def test_single_sample_returns_neutral(self):
        """单样本时返回中性分 0.5（无跨候选参照）"""
        assert normalize_scores([42.0], "minimize") == [0.5]


class TestWeightedScore:
    """加权综合分"""

    @pytest.mark.unit
    def test_equal_scores_returns_that_score(self):
        scores = {"distance": 0.8, "time": 0.8}
        assert weighted_score(scores, OBJECTIVES) == pytest.approx(0.8)

    @pytest.mark.unit
    def test_weighted_average(self):
        scores = {"distance": 1.0, "time": 0.0}
        # 0.5*1.0 + 0.5*0.0 = 0.5
        assert weighted_score(scores, OBJECTIVES) == pytest.approx(0.5)

    @pytest.mark.unit
    def test_zero_total_weight_returns_zero(self):
        cfg = {"distance": {"weight": 0.0, "direction": "minimize", "metric": "distance"}}
        assert weighted_score({"distance": 0.9}, cfg) == 0.0


class TestScoreBreakdown:
    """单方案评分拆解"""

    @pytest.mark.unit
    def test_breakdown_has_expected_keys(self):
        metrics = {"distance": 120.0, "time": 3.0}
        bd = score_breakdown(metrics, OBJECTIVES)
        assert "overall" in bd
        assert "breakdown" in bd
        assert "distance" in bd["breakdown"]
        assert "time" in bd["breakdown"]
        dist = bd["breakdown"]["distance"]
        assert dist["raw"] == 120.0
        assert dist["metric"] == "distance"
        assert dist["direction"] == "minimize"
        assert dist["weight"] == 0.5
        # 单方案归一化为中性分
        assert dist["normalized"] == 0.5

    @pytest.mark.unit
    def test_overall_is_weighted_mean_of_neutral(self):
        metrics = {"distance": 100.0, "time": 2.0}
        bd = score_breakdown(metrics, OBJECTIVES)
        assert bd["overall"] == pytest.approx(0.5)


class TestRankCandidates:
    """跨候选多目标排序"""

    @pytest.mark.unit
    def test_better_candidate_ranked_first(self):
        """距离/时间更优的方案综合分更高，排在最前"""
        candidates = [
            {"profile": "A", "metrics": {"distance": 200.0, "time": 5.0}},
            {"profile": "B", "metrics": {"distance": 100.0, "time": 3.0}},
        ]
        ranked = rank_candidates(candidates, OBJECTIVES)
        assert ranked[0]["profile"] == "B"
        assert ranked[0]["overall_score"] >= ranked[1]["overall_score"]
        # 附加 objective_scores
        assert set(ranked[0]["objective_scores"]) == {"distance", "time"}
        assert 0.0 <= ranked[0]["overall_score"] <= 1.0

    @pytest.mark.unit
    def test_weight_change_flips_ranking(self):
        """修改权重配置后排序倾向相应变化（验收标准 2）：
        A 距离更优但时间更差；B 时间更优但距离更差。
        距离权重大 → A 胜；时间权重大 → B 胜。
        """
        candidates = [
            {"profile": "A", "metrics": {"distance": 100.0, "time": 5.0}},
            {"profile": "B", "metrics": {"distance": 200.0, "time": 3.0}},
        ]
        distance_heavy = {
            "distance": {"weight": 0.9, "direction": "minimize", "metric": "distance"},
            "time": {"weight": 0.1, "direction": "minimize", "metric": "time"},
        }
        time_heavy = {
            "distance": {"weight": 0.1, "direction": "minimize", "metric": "distance"},
            "time": {"weight": 0.9, "direction": "minimize", "metric": "time"},
        }
        assert rank_candidates(candidates, distance_heavy)[0]["profile"] == "A"
        assert rank_candidates(candidates, time_heavy)[0]["profile"] == "B"

    @pytest.mark.unit
    def test_empty_candidates_returns_empty(self):
        assert rank_candidates([], OBJECTIVES) == []

    @pytest.mark.unit
    def test_maximize_objective_prefers_higher(self):
        """direction=maximize：load_rate 更高的候选获得更高该目标分"""
        cfg = {"load_rate": {"weight": 1.0, "direction": "maximize", "metric": "load_rate"}}
        candidates = [
            {"profile": "low", "metrics": {"load_rate": 0.4}},
            {"profile": "high", "metrics": {"load_rate": 0.9}},
        ]
        ranked = rank_candidates(candidates, cfg)
        assert ranked[0]["profile"] == "high"
        assert ranked[0]["objective_scores"]["load_rate"] == pytest.approx(1.0)


class TestGlobalScheduleObjectiveOutput:
    """F007 输出携带多目标评分（T2-2 验收标准 3）"""

    @pytest.mark.unit
    def test_global_schedule_returns_objective_fields(
        self, db_session, test_nodes, test_orders, test_goods
    ):
        result = global_schedule(
            order_codes=None, algorithm="traditional", db=db_session
        )
        # 原有字段不受影响
        assert result["schedule_code"].startswith("GS")
        assert result["total_goods"] == 18
        assert result["score"] > 0

        # T2-2 新增字段
        assert "objective_scores" in result
        assert "distance" in result["objective_scores"]
        assert "time" in result["objective_scores"]
        assert "score_breakdown" in result
        assert "breakdown" in result["score_breakdown"]
        assert result["score_breakdown"]["breakdown"]["distance"]["metric"] == "distance"
        assert "composite_score" in result
        assert 0.0 <= result["composite_score"] <= 1.0

        # 备选方案 ≥ 2（合计 ≥3 份候选）
        assert "alternatives" in result
        assert len(result["alternatives"]) >= 2
        # 备选方案按综合分降序（主方案综合分 ≥ 任一备选）
        for alt in result["alternatives"]:
            assert alt["overall_score"] <= result["composite_score"]
            assert "objective_scores" in alt
