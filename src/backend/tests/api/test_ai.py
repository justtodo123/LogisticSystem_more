"""
AI助手API测试

测试AI助手相关的API端点：
- POST /api/ai/explain (F015 方案解释)
- POST /api/ai/review (F016 方案审查)
- POST /api/ai/analyze-exception (F017 异常分析)

使用Mock模拟服务层调用，避免实际调用DeepSeek API。
"""
import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.fixture
def auth_headers(client, test_users):
    """认证头（调度员）"""
    # 登录获取token
    response = client.post("/api/auth/login", json={
        "username": "dispatcher",
        "password": "123456"
    })
    assert response.status_code == 200, f"登录失败: {response.json()}"
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_schedule_data():
    """模拟调度方案数据"""
    return {
        "schedule_code": "GS001",
        "order_codes": ["O001", "O002"],
        "goods_schedules": [
            {"goods_code": "G001", "order_code": "O001", "path": ["SC001", "SO001", "SO010"]}
        ],
        "total_distance": 120.5,
        "total_time": 5.2,
        "total_goods": 15,
        "score": 0.85,
        "algorithm_type": "traditional",
        "version": 1,
        "is_replan": False,
        "created_at": "2026-06-15T10:00:00",
    }


@pytest.fixture
def mock_batch_data():
    """模拟批次数据"""
    return {
        "batch_code": "DB001",
        "global_schedule_id": 1,
        "status": "completed",
        "l0_l1_dispatch_count": 3,
        "l1_l2_dispatch_count": 2,
        "dispatches": [
            {
                "dispatch_code": "ND001",
                "vehicle_code": "VEH001",
                "driver_code": "DRV001",
                "total_distance": 50.0,
                "total_time": 2.0,
            }
        ],
        "routes": [
            {
                "route_code": "RT001",
                "vehicle_code": "VEH001",
                "total_distance": 50.0,
                "total_time": 2.0,
            }
        ],
        "created_at": "2026-06-15T10:05:00",
    }


@pytest.fixture
def mock_exception_data():
    """模拟异常事件数据"""
    return {
        "event_code": "EX001",
        "exception_type": "road",
        "exception_subtype": "congestion",
        "target_type": "route",
        "target_code": "RT001",
        "recommended_action": "reroute",
        "description": "道路拥堵导致配送延迟",
        "status": "open",
        "related_schedule_code": "GS001",
        "created_at": "2026-06-15T10:10:00",
    }


@pytest.mark.api
@pytest.mark.phase9
class TestExplainScheduleAPI:
    """测试F015方案解释API"""

    def test_explain_with_schedule_code_success(self, client, auth_headers, mock_schedule_data):
        """测试使用schedule_code成功获取方案解释"""
        # Mock服务层方法
        with patch("api.ai.ScheduleService.get_global_schedule", new_callable=AsyncMock) as mock_get_schedule, \
             patch("api.ai.DeepSeekService.explain_schedule", new_callable=AsyncMock) as mock_explain:
            
            # 配置mock返回值
            mock_get_schedule.return_value = {
                "code": 0,
                "message": "success",
                "data": mock_schedule_data
            }
            
            mock_explain.return_value = {
                "explanation": "这是一个优化的调度方案",
                "key_decisions": ["使用传统算法"],
                "potential_risks": [],
                "suggestions": ["建议优化路线"]
            }
            
            # 执行API调用
            response = client.post(
                "/api/ai/explain",
                json={"schedule_code": "GS001"},
                headers=auth_headers
            )
            
            # 验证
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert "explanation" in data["data"]
            assert data["data"]["explanation"] == "这是一个优化的调度方案"

    def test_explain_with_batch_code_success(self, client, auth_headers, mock_batch_data):
        """测试使用batch_code成功获取方案解释"""
        with patch("api.ai.DispatchService.get_dispatch_batch_detail", new_callable=AsyncMock) as mock_get_batch, \
             patch("api.ai.DeepSeekService.explain_schedule", new_callable=AsyncMock) as mock_explain:
            
            mock_get_batch.return_value = {
                "code": 0,
                "message": "success",
                "data": mock_batch_data
            }
            
            mock_explain.return_value = {
                "explanation": "批次DB001的解释",
                "key_decisions": [],
                "potential_risks": [],
                "suggestions": []
            }
            
            response = client.post(
                "/api/ai/explain",
                json={"batch_code": "DB001"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0

    def test_explain_without_params(self, client, auth_headers):
        """测试不传入任何参数（应该返回错误）"""
        response = client.post(
            "/api/ai/explain",
            json={},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] != 0  # 应该返回错误码
        assert "schedule_code" in data["message"].lower() or "batch_code" in data["message"].lower()

    def test_explain_schedule_not_found(self, client, auth_headers):
        """测试调度方案不存在"""
        with patch("api.ai.ScheduleService.get_global_schedule", new_callable=AsyncMock) as mock_get_schedule:
            mock_get_schedule.return_value = {
                "code": 40401,
                "message": "调度方案不存在",
                "data": None
            }
            
            response = client.post(
                "/api/ai/explain",
                json={"schedule_code": "GS_NONEXISTENT"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 40401

    def test_explain_degraded_response(self, client, auth_headers, mock_schedule_data):
        """测试DeepSeek服务降级响应"""
        with patch("api.ai.ScheduleService.get_global_schedule", new_callable=AsyncMock) as mock_get_schedule, \
             patch("api.ai.DeepSeekService.explain_schedule", new_callable=AsyncMock) as mock_explain:
            
            mock_get_schedule.return_value = {
                "code": 0,
                "message": "success",
                "data": mock_schedule_data
            }
            
            # Mock降级响应
            mock_explain.return_value = {
                "explanation": "AI服务暂时不可用，请稍后重试",
                "key_decisions": [],
                "potential_risks": [],
                "suggestions": []
            }
            
            response = client.post(
                "/api/ai/explain",
                json={"schedule_code": "GS001"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert "AI服务暂时不可用" in data["data"]["explanation"]


@pytest.mark.api
@pytest.mark.phase9
class TestReviewScheduleAPI:
    """测试F016方案审查API"""

    def test_review_with_schedule_and_batch_success(self, client, auth_headers, mock_schedule_data, mock_batch_data):
        """测试同时传入schedule_code和batch_code成功获取审查报告"""
        with patch("api.ai.ScheduleService.get_global_schedule", new_callable=AsyncMock) as mock_get_schedule, \
             patch("api.ai.DispatchService.get_dispatch_batch_detail", new_callable=AsyncMock) as mock_get_batch, \
             patch("api.ai.DeepSeekService.review_schedule", new_callable=AsyncMock) as mock_review:
            
            mock_get_schedule.return_value = {
                "code": 0,
                "message": "success",
                "data": mock_schedule_data
            }
            
            mock_get_batch.return_value = {
                "code": 0,
                "message": "success",
                "data": mock_batch_data
            }
            
            mock_review.return_value = {
                "risks": [
                    {
                        "type": "road",
                        "description": "路线RT001可能存在拥堵",
                        "severity": "medium",
                        "suggestion": "建议使用实时路况数据优化路线"
                    }
                ]
            }
            
            response = client.post(
                "/api/ai/review",
                json={"schedule_code": "GS001", "batch_code": "DB001"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert "risks" in data["data"]
            assert len(data["data"]["risks"]) > 0

    def test_review_without_params(self, client, auth_headers):
        """测试不传入任何参数（应该返回错误）"""
        response = client.post(
            "/api/ai/review",
            json={},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] != 0

    def test_review_empty_risks(self, client, auth_headers, mock_schedule_data, mock_batch_data):
        """测试返回空风险列表（无风险场景）"""
        with patch("api.ai.ScheduleService.get_global_schedule", new_callable=AsyncMock) as mock_get_schedule, \
             patch("api.ai.DispatchService.get_dispatch_batch_detail", new_callable=AsyncMock) as mock_get_batch, \
             patch("api.ai.DeepSeekService.review_schedule", new_callable=AsyncMock) as mock_review:
            
            mock_get_schedule.return_value = {
                "code": 0,
                "message": "success",
                "data": mock_schedule_data
            }
            
            mock_get_batch.return_value = {
                "code": 0,
                "message": "success",
                "data": mock_batch_data
            }
            
            # Mock返回空风险列表
            mock_review.return_value = {"risks": []}
            
            response = client.post(
                "/api/ai/review",
                json={"schedule_code": "GS001", "batch_code": "DB001"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert data["data"]["risks"] == []


@pytest.mark.api
@pytest.mark.phase9
class TestAnalyzeExceptionAPI:
    """测试F017异常分析API"""

    def test_analyze_exception_success(self, client, auth_headers, mock_exception_data, mock_schedule_data):
        """测试成功获取异常分析建议"""
        with patch("api.ai.ExceptionService.get_exception_event_by_code", new_callable=AsyncMock) as mock_get_exception, \
             patch("api.ai.ScheduleService.get_global_schedule", new_callable=AsyncMock) as mock_get_schedule, \
             patch("api.ai.DeepSeekService.analyze_exception", new_callable=AsyncMock) as mock_analyze:
            
            mock_get_exception.return_value = {
                "code": 0,
                "message": "success",
                "data": mock_exception_data
            }
            
            mock_get_schedule.return_value = {
                "code": 0,
                "message": "success",
                "data": mock_schedule_data
            }
            
            mock_analyze.return_value = {
                "root_cause": "道路RT001所在路段发生拥堵",
                "suggestions": ["建议重新规划路线"],
                "auto_fix_available": True
            }
            
            response = client.post(
                "/api/ai/analyze-exception",
                json={"event_code": "EX001"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert "root_cause" in data["data"]
            assert "suggestions" in data["data"]
            assert "auto_fix_available" in data["data"]

    def test_analyze_exception_not_found(self, client, auth_headers):
        """测试异常事件不存在"""
        with patch("api.ai.ExceptionService.get_exception_event_by_code", new_callable=AsyncMock) as mock_get_exception:
            mock_get_exception.return_value = {
                "code": 40401,
                "message": "异常事件不存在",
                "data": None
            }
            
            response = client.post(
                "/api/ai/analyze-exception",
                json={"event_code": "EX_NONEXISTENT"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 40401

    def test_analyze_exception_without_event_code(self, client, auth_headers):
        """测试不传入event_code（应该返回参数错误）"""
        response = client.post(
            "/api/ai/analyze-exception",
            json={},
            headers=auth_headers
        )
        
        # Pydantic校验失败返回422
        assert response.status_code == 422

    def test_analyze_exception_without_related_schedule(self, client, auth_headers):
        """测试异常事件无关联调度方案"""
        exception_data = {
            "event_code": "EX002",
            "exception_type": "node",
            "exception_subtype": "capacity_limit",
            "target_type": "node",
            "target_code": "SC001",
            "recommended_action": "redispatch",
            "description": "容量不足",
            "status": "open",
            "related_schedule_code": None,  # 无关联调度方案
        }
        
        with patch("api.ai.ExceptionService.get_exception_event_by_code", new_callable=AsyncMock) as mock_get_exception, \
             patch("api.ai.DeepSeekService.analyze_exception", new_callable=AsyncMock) as mock_analyze:
            
            mock_get_exception.return_value = {
                "code": 0,
                "message": "success",
                "data": exception_data
            }
            
            mock_analyze.return_value = {
                "root_cause": "存储中心容量不足",
                "suggestions": ["建议增加容量"],
                "auto_fix_available": False
            }
            
            response = client.post(
                "/api/ai/analyze-exception",
                json={"event_code": "EX002"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert data["data"]["auto_fix_available"] is False

    def test_analyze_exception_degraded_response(self, client, auth_headers, mock_exception_data):
        """测试DeepSeek服务降级响应"""
        with patch("api.ai.ExceptionService.get_exception_event_by_code", new_callable=AsyncMock) as mock_get_exception, \
             patch("api.ai.DeepSeekService.analyze_exception", new_callable=AsyncMock) as mock_analyze:
            
            mock_get_exception.return_value = {
                "code": 0,
                "message": "success",
                "data": mock_exception_data
            }
            
            # Mock降级响应
            mock_analyze.return_value = {
                "root_cause": "AI服务暂时不可用，请稍后重试",
                "suggestions": [],
                "auto_fix_available": False
            }
            
            response = client.post(
                "/api/ai/analyze-exception",
                json={"event_code": "EX001"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert "AI服务暂时不可用" in data["data"]["root_cause"]
