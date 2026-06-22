"""
DeepSeek服务单元测试：测试F015/F016/F017功能

测试目标：
- explain_schedule（F015 方案解释）
- review_schedule（F016 方案审查）
- analyze_exception（F017 异常分析）

使用Mock模拟DeepSeek API调用，测试各种成功和失败场景。
"""
import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock


def _mock_deepseek_response(mock_json_data):
    """
    辅助函数：创建模拟DeepSeek API响应的Mock
    
    Args:
        mock_json_data: 模拟的JSON响应数据
        
    Returns:
        Mock对象，模拟httpx.AsyncClient.post的返回
    """
    # 创建mock响应对象
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{
            "message": {
                "content": json.dumps(mock_json_data)
            }
        }]
    }
    
    # 创建mock客户端：post/__aenter__ 必须是 AsyncMock 以支持 await
    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    return mock_client


class TestExplainSchedule:
    """测试F015方案解释功能"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_explain_schedule_success(self):
        """测试成功生成方案解释"""
        from services.deepseek_service import DeepSeekService
        
        # 准备测试数据
        schedule_data = {
            "schedule_code": "GS001",
            "total_distance": 120.5,
            "total_time": 5.2,
            "total_goods": 15,
            "score": 0.85,
            "algorithm_type": "traditional",
        }
        
        # 创建mock响应数据
        mock_data = {
            "explanation": "这是一个优化的调度方案",
            "key_decisions": ["使用传统算法"],
            "potential_risks": [],
            "suggestions": ["建议优化路线"]
        }
        
        # 使用patch模拟httpx.AsyncClient
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = _mock_deepseek_response(mock_data)
            mock_client_class.return_value = mock_client
            
            # 调用被测试的方法
            result = await DeepSeekService.explain_schedule(schedule_data)
            
            # 验证结果
            assert "explanation" in result
            assert result["explanation"] == "这是一个优化的调度方案"
            assert len(result["key_decisions"]) > 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_explain_schedule_timeout(self):
        """测试DeepSeek API调用超时（降级响应）"""
        from services.deepseek_service import DeepSeekService
        
        schedule_data = {
            "schedule_code": "GS001",
            "total_distance": 120.5,
            "total_time": 5.2,
        }
        
        # 使用patch模拟超时异常：__aenter__正常，post抛出异常
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(side_effect=Exception("Timeout"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            result = await DeepSeekService.explain_schedule(schedule_data)
            
            # 验证降级响应
            assert result["explanation"] == "AI服务暂时不可用，请稍后重试"
            assert result["key_decisions"] == []
            assert result["potential_risks"] == []
            assert result["suggestions"] == []


class TestReviewSchedule:
    """测试F016方案审查功能"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_review_schedule_success(self):
        """测试成功生成方案审查报告"""
        from services.deepseek_service import DeepSeekService
        
        schedule_data = {"schedule_code": "GS001"}
        batch_data = {"batch_code": "DB001"}
        
        # 创建mock响应数据
        mock_data = {
            "risks": [
                {
                    "type": "road",
                    "description": "路线拥堵",
                    "severity": "medium",
                    "suggestion": "建议优化路线"
                }
            ]
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = _mock_deepseek_response(mock_data)
            mock_client_class.return_value = mock_client
            
            result = await DeepSeekService.review_schedule(schedule_data, batch_data)
            
            # 验证结果
            assert "risks" in result
            assert len(result["risks"]) > 0
            assert result["risks"][0]["type"] == "road"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_review_schedule_timeout(self):
        """测试DeepSeek API调用超时（降级响应）"""
        from services.deepseek_service import DeepSeekService
        
        schedule_data = {"schedule_code": "GS001"}
        batch_data = {"batch_code": "DB001"}
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(side_effect=Exception("Timeout"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            result = await DeepSeekService.review_schedule(schedule_data, batch_data)
            
            # 验证降级响应
            assert "risks" in result
            assert result["risks"] == []


class TestAnalyzeException:
    """测试F017异常分析功能"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_exception_success(self):
        """测试成功生成异常分析建议"""
        from services.deepseek_service import DeepSeekService
        
        exception_data = {
            "event_code": "EX001",
            "exception_type": "road",
            "description": "道路拥堵",
        }
        
        # 创建mock响应数据
        mock_data = {
            "root_cause": "道路拥堵导致配送延迟",
            "suggestions": ["建议重新规划路线"],
            "auto_fix_available": True
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = _mock_deepseek_response(mock_data)
            mock_client_class.return_value = mock_client
            
            result = await DeepSeekService.analyze_exception(exception_data)
            
            # 验证结果
            assert "root_cause" in result
            assert result["root_cause"] == "道路拥堵导致配送延迟"
            assert len(result["suggestions"]) > 0
            assert result["auto_fix_available"] is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_exception_timeout(self):
        """测试DeepSeek API调用超时（降级响应）"""
        from services.deepseek_service import DeepSeekService
        
        exception_data = {
            "event_code": "EX001",
            "exception_type": "road",
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(side_effect=Exception("Timeout"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            result = await DeepSeekService.analyze_exception(exception_data)
            
            # 验证降级响应
            assert result["root_cause"] == "AI服务暂时不可用，请稍后重试"
            assert result["suggestions"] == []
            assert result["auto_fix_available"] is False
