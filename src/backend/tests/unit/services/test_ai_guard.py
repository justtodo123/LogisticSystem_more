"""
AI 规则闸门测试（T6-1）

覆盖：
- validate_and_retry：校验失败 → 错误反馈重试 → 成功 / 重试耗尽抛 AIValidationError
- JSON 解析失败 → 反馈重试 → 耗尽抛 AIValidationError
- AIValidationError 携带原始输出 + 校验错误
- 业务规则检查：权重归一化、风险枚举白名单、异常分析建议
- deepseek_service 接线：3 次校验失败后抛 AIValidationError / parse 返回明确错误
"""
import json
from unittest.mock import AsyncMock, patch

import pytest

from core.ai_guard import (
    AIValidationError,
    check_algorithm_params,
    check_analyze_result,
    check_review_result,
    classify_suggestion_level,
    normalize_algorithm_weights,
    should_gate,
    validate_and_retry,
)
from schemas.ai_output import (
    AnalyzeExceptionResult,
    ParsedAlgorithmParams,
    ReviewResult,
)


def _content_round_trip(data) -> str:
    """把 dict 包装成 AI 返回文本（直接 JSON）"""
    return json.dumps(data, ensure_ascii=False)


def _mk_api_call(responses):
    """按顺序返回 response 文本的异步回调，并记录每次收到的 prompt"""
    call_prompts = []
    calls = list(responses)

    async def _call(user_prompt, system_prompt):
        call_prompts.append(user_prompt)
        if calls:
            return calls.pop(0)
        raise AssertionError("API 被调用次数超过预期")

    return _call, call_prompts


@pytest.mark.unit
@pytest.mark.asyncio
class TestValidateAndRetry:
    async def test_first_attempt_valid(self):
        """首次调用即校验通过 → 返回结构化结果，不重试"""
        api_call, prompts = _mk_api_call([
            _content_round_trip({
                "global_schedule": {
                    "algorithm": "traditional",
                    "weights": {"distance": 0.5, "time": 0.3, "package_count": 0.2},
                }
            }),
        ])
        result = await validate_and_retry(
            schema=ParsedAlgorithmParams, api_call=api_call, user_prompt="p"
        )
        assert result.global_schedule.algorithm == "traditional"
        assert len(prompts) == 1

    async def test_retry_after_validation_error(self):
        """第 1 次缺少字段 → 校验失败；第 2 次补全 → 成功；prompt 应携带错误反馈"""
        api_call, prompts = _mk_api_call([
            # 缺少 global_schedule.weights（校验失败）
            _content_round_trip({"global_schedule": {"algorithm": "traditional"}}),
            # 修正后补全 weights（校验通过）
            _content_round_trip({
                "global_schedule": {
                    "algorithm": "traditional",
                    "weights": {"distance": 0.6, "time": 0.3, "package_count": 0.1},
                }
            }),
        ])
        result = await validate_and_retry(
            schema=ParsedAlgorithmParams, api_call=api_call, user_prompt="p"
        )
        assert result.global_schedule.weights.distance == 0.6
        # 第 2 次 prompt 应包含"校验未通过"的错误反馈
        assert len(prompts) == 2
        assert "校验未通过" in prompts[1]

    async def test_retry_after_json_decode_error(self):
        """第 1 次返回非 JSON 文本 → 解析失败反馈重试；第 2 次合法 → 成功"""
        api_call, prompts = _mk_api_call([
            "这不是 JSON",
            _content_round_trip({
                "global_schedule": {
                    "algorithm": "traditional",
                    "weights": {"distance": 0.5, "time": 0.3, "package_count": 0.2},
                }
            }),
        ])
        result = await validate_and_retry(
            schema=ParsedAlgorithmParams, api_call=api_call, user_prompt="p"
        )
        assert len(prompts) == 2
        assert result.global_schedule.algorithm == "traditional"

    async def test_exhaust_retries_raises_validation_error(self):
        """3 次均校验失败 → 抛 AIValidationError，且携带原始输出 + 校验错误"""
        bad = _content_round_trip({"global_schedule": {"algorithm": "traditional"}})
        api_call, prompts = _mk_api_call([bad, bad, bad])

        with pytest.raises(AIValidationError) as exc_info:
            await validate_and_retry(
                schema=ParsedAlgorithmParams, api_call=api_call, user_prompt="p"
            )

        assert len(prompts) == 3
        err = exc_info.value
        assert err.raw_output == bad
        assert "weights" in str(err)  # 校验错误信息包含缺失字段
        assert "原始输出" in str(err)

    async def test_json_always_invalid_raises(self):
        """3 次均为无效 JSON → 抛 AIValidationError（json_decode 错误）"""
        api_call, _ = _mk_api_call(["no json", "no json", "no json"])
        with pytest.raises(AIValidationError) as exc_info:
            await validate_and_retry(
                schema=ParsedAlgorithmParams, api_call=api_call, user_prompt="p"
            )
        assert exc_info.value.raw_output == "no json"

    async def test_markdown_fenced_json_accepted(self):
        """AI 输出包裹在 ```json ``` 内也应能提取并校验"""
        content = "```json\n" + _content_round_trip({
            "global_schedule": {
                "algorithm": "greedy",
                "weights": {"distance": 0.5, "time": 0.3, "package_count": 0.2},
            }
        }) + "\n```"
        api_call, _ = _mk_api_call([content])
        result = await validate_and_retry(
            schema=ParsedAlgorithmParams, api_call=api_call, user_prompt="p"
        )
        assert result.global_schedule.algorithm == "greedy"


@pytest.mark.unit
class TestBusinessRules:
    def test_check_algorithm_params_weights_sum(self):
        """权重和偏离 1.0 → 报违规"""
        ok = ParsedAlgorithmParams.model_validate({
            "global_schedule": {
                "weights": {"distance": 0.5, "time": 0.3, "package_count": 0.2}
            }
        })
        assert check_algorithm_params(ok) == []

        bad = ParsedAlgorithmParams.model_validate({
            "global_schedule": {
                "weights": {"distance": 0.9, "time": 0.3, "package_count": 0.2}
            }
        })
        violations = check_algorithm_params(bad)
        assert len(violations) == 1
        assert "1.0" in violations[0]

    def test_check_review_result_whitelist(self):
        """非法风险类型/级别/空建议 → 报违规"""
        ok = ReviewResult.model_validate({
            "risks": [{
                "type": "road", "description": "拥堵",
                "severity": "medium", "suggestion": "绕行",
            }]
        })
        assert check_review_result(ok) == []

        bad = ReviewResult.model_validate({
            "risks": [
                {"type": "alien", "description": "x", "severity": "medium", "suggestion": "a"},
                {"type": "road", "description": "y", "severity": "critical", "suggestion": "b"},
                {"type": "road", "description": "z", "severity": "low", "suggestion": ""},
            ]
        })
        violations = check_review_result(bad)
        assert len(violations) == 3

    def test_check_analyze_result_suggestions(self):
        """异常分析无建议 → 报违规"""
        ok = AnalyzeExceptionResult.model_validate({
            "root_cause": "拥堵", "suggestions": ["绕行"], "auto_fix_available": True,
        })
        assert check_analyze_result(ok) == []

        bad = AnalyzeExceptionResult.model_validate({
            "root_cause": "拥堵", "suggestions": [], "auto_fix_available": False,
        })
        assert len(check_analyze_result(bad)) == 1


@pytest.mark.unit
class TestSuggestionGate:
    """T6-2：AI 建议确认闸门级别分类与闸门判定"""

    def test_classify_parse_is_suggestion(self):
        """parse（生成调度建议）→ suggestion，需人工确认"""
        assert classify_suggestion_level("parse") == "suggestion"

    def test_classify_others_are_info(self):
        """explain/review/analyze → info，仅供展示"""
        for source in ("explain", "review", "analyze"):
            assert classify_suggestion_level(source) == "info"

    def test_should_gate(self):
        """suggestion/action 进入闸门，info 直接展示"""
        assert should_gate("suggestion") is True
        assert should_gate("action") is True
        assert should_gate("info") is False


@pytest.mark.unit
class TestNormalizeWeights:
    def test_drop_unknown_keys_and_renormalize(self):
        """丢弃未知键、钳制到 [0,1]、按比例归一化"""
        out = normalize_algorithm_weights({
            "global_schedule": {
                "algorithm": "greedy",
                "weights": {"distance": 0.8, "time": 0.5, "package_count": 0.2, "magic": 99},
            }
        })
        gs = out["global_schedule"]
        assert gs["algorithm"] == "greedy"
        assert set(gs["weights"].keys()) == {"distance", "time", "package_count"}
        total = sum(gs["weights"].values())
        assert total == pytest.approx(1.0, abs=1e-6)
        assert "magic" not in gs["weights"]

    def test_all_zero_falls_back_to_default(self):
        """权重全 0 → 回退默认权重"""
        out = normalize_algorithm_weights({
            "global_schedule": {"weights": {"distance": 0, "time": 0, "package_count": 0}}
        })
        assert out["global_schedule"]["weights"] == {
            "distance": 0.5, "time": 0.3, "package_count": 0.2,
        }

    def test_missing_weights_uses_default(self):
        """缺 global_schedule / weights → 默认"""
        out = normalize_algorithm_weights({})
        assert out["global_schedule"]["weights"] == {
            "distance": 0.5, "time": 0.3, "package_count": 0.2,
        }

    def test_non_numeric_weight_dropped(self):
        """权重含非数字 → 丢弃该键并归一化剩余"""
        out = normalize_algorithm_weights({
            "global_schedule": {
                "weights": {"distance": "abc", "time": 0.3, "package_count": 0.2},
            }
        })
        weights = out["global_schedule"]["weights"]
        assert "distance" not in weights
        total = sum(weights.values())
        assert total == pytest.approx(1.0, abs=1e-6)


@pytest.mark.unit
@pytest.mark.asyncio
class TestDeepSeekValidationWiring:
    """验证 deepseek_service 已接入校验管线"""

    @patch("services.deepseek_service.DeepSeekService._post_chat", new_callable=AsyncMock)
    async def test_explain_raises_after_invalid_outputs(self, mock_post):
        """explain：3 次均返回类型错误的输出 → AIValidationError 向上抛出（含原始输出）"""
        from services.deepseek_service import DeepSeekService

        bad = json.dumps({"explanation": 123})  # explanation 应为 str
        mock_post.return_value = bad

        with pytest.raises(AIValidationError) as exc_info:
            await DeepSeekService.explain_schedule({"schedule_code": "GS001"})
        assert exc_info.value.raw_output == bad
        assert mock_post.await_count == 3  # 校验失败 → 重试 3 次

    @patch("services.deepseek_service.DeepSeekService._post_chat", new_callable=AsyncMock)
    async def test_review_raises_after_invalid_outputs(self, mock_post):
        """review：3 次均非法输出 → AIValidationError"""
        from services.deepseek_service import DeepSeekService

        mock_post.return_value = '{"risks": "不是列表"}'

        with pytest.raises(AIValidationError):
            await DeepSeekService.review_schedule({"schedule_code": "GS001"}, {"batch_code": "B1"})
        assert mock_post.await_count == 3

    @patch("services.deepseek_service.DeepSeekService._post_chat", new_callable=AsyncMock)
    async def test_analyze_raises_after_invalid_outputs(self, mock_post):
        """analyze：3 次均非法输出 → AIValidationError"""
        from services.deepseek_service import DeepSeekService

        mock_post.return_value = '{"root_cause": "", "suggestions": []}'

        with pytest.raises(AIValidationError):
            await DeepSeekService.analyze_exception({"event_code": "EX1"})
        assert mock_post.await_count == 3

    @patch("services.deepseek_service.settings.DEEPSEEK_API_KEY", "fake-key")
    @patch("services.deepseek_service.DeepSeekService._post_chat", new_callable=AsyncMock)
    async def test_parse_returns_clear_error_after_invalid_outputs(self, mock_post):
        """parse：3 次均非法输出 → 返回 success=False 且 error 含原始输出 + 校验错误"""
        from services.deepseek_service import DeepSeekService

        bad = '{"global_schedule": {"algorithm": "traditional"}}'  # 缺 weights
        mock_post.return_value = bad

        result = await DeepSeekService.parse_natural_language("缩短距离", {"order_count": 0})
        assert result["success"] is False
        assert "AI 输出校验失败" in result["error"]
        assert "weights" in result["error"]
        assert result["raw_response"] == bad
        assert mock_post.await_count == 3
        # 降级返回默认参数
        assert result["algorithm_params"]["global_schedule"]["weights"]["distance"] == 0.5

    @patch("services.deepseek_service.settings.DEEPSEEK_API_KEY", "fake-key")
    @patch("services.deepseek_service.DeepSeekService._post_chat", new_callable=AsyncMock)
    async def test_parse_retries_then_succeeds(self, mock_post):
        """parse：第 1 次非法 → 反馈重试；第 2 次合法 → 成功并返回归一化参数"""
        from services.deepseek_service import DeepSeekService

        bad = '{"global_schedule": {"algorithm": "traditional"}}'
        good = json.dumps({
            "global_schedule": {
                "algorithm": "traditional",
                "weights": {"distance": 0.7, "time": 0.2, "package_count": 0.1},
            }
        })
        mock_post.side_effect = [bad, good]

        result = await DeepSeekService.parse_natural_language("缩短距离", {"order_count": 0})
        assert result["success"] is True
        assert mock_post.await_count == 2
        params = result["algorithm_params"]["global_schedule"]["weights"]
        assert params["distance"] == pytest.approx(0.7)
