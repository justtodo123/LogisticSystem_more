"""
阶段0：工程初始化 - 健康检查接口测试

测试目标：
- GET /api/health 接口正常响应
- 响应格式符合统一响应规范 {code, message, data, meta}
- 响应内容正确（status: "ok"）
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestHealthCheck:
    """健康检查接口测试类"""

    def test_health_check_success(self):
        """测试健康检查接口成功响应"""
        response = client.get("/api/health")
        
        # 验证HTTP状态码
        assert response.status_code == 200
        
        # 验证响应格式符合统一规范
        data = response.json()
        assert "code" in data
        assert "message" in data
        assert "data" in data
        assert "meta" in data
        
        # 验证响应内容
        assert data["code"] == 0
        assert data["message"] == "success"
        assert data["data"]["status"] == "ok"
        assert data["meta"]["degraded"] == False
        assert data["meta"]["degraded_reason"] is None

    def test_health_check_response_structure(self):
        """测试健康检查响应结构完整性"""
        response = client.get("/api/health")
        data = response.json()
        
        # 验证data字段结构
        assert isinstance(data["data"], dict)
        assert "status" in data["data"]
        assert data["data"]["status"] == "ok"
        
        # 验证meta字段结构
        assert isinstance(data["meta"], dict)
        assert "degraded" in data["meta"]
        assert "degraded_reason" in data["meta"]

    def test_health_check_no_auth_required(self):
        """测试健康检查接口不需要认证"""
        # 不带Token访问
        response = client.get("/api/health")
        
        # 应该成功响应（不需要认证）
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
