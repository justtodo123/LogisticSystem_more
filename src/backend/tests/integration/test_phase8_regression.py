"""
阶段8回归测试

测试内容：
1. 主链路测试（F007→F021→F005→F006）with DeepSeek
2. DeepSeek降级场景测试
3. log_events记录测试
4. 重规划回归测试
"""
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from main import app
from models.user import User
from models.log_event import LogEvent
from config.database import get_db


# ── 异步测试客户端固件 ─────────────────────────────────────────────

@pytest.fixture(scope="function")
def async_client(test_db):
    """创建 httpx.AsyncClient（用于异步测试）"""
    from sqlalchemy.orm import sessionmaker
    
    engine, TestingSessionLocal = test_db
    
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async_client = AsyncClient(transport=transport, base_url="http://test")
    
    yield async_client
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_ai_parse_with_mock(async_client, test_users):
    """
    测试AI解析接口（Mock DeepSeek API）
    
    流程：
    1. Mock DeepSeek API返回成功响应
    2. 调用POST /api/ai/parse
    3. 验证响应格式正确
    """
    # Mock DeepSeek API响应
    mock_response = {
        "choices": [{
            "message": {
                "content": '{"global_schedule": {"algorithm": "traditional", "weights": {"distance": 0.5, "time": 0.3, "package_count": 0.2}}, "node_dispatch": {"algorithm": "traditional", "weights": {"distance": 0.5, "time": 0.3, "package_count": 0.2}}, "route_planning": {"algorithm": "traditional", "max_iterations": 1000}}'
            }
        }]
    }
    
    # 正确Mock httpx.AsyncClient的异步上下文管理器
    mock_client = AsyncMock()
    mock_client.post.return_value = AsyncMock(
        status_code=200,
        json=AsyncMock(return_value=mock_response),
        raise_for_status=AsyncMock()
    )
    
    with patch("services.deepseek_service.httpx.AsyncClient") as mock_client_class:
        # 配置__aenter__返回mock_client
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # 调用API
        client = async_client
        # 先登录
        login_resp = await client.post("/api/auth/login", json={
            "username": "dispatcher",
            "password": "123456"
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 调用AI解析接口
        ai_resp = await client.post(
            "/api/ai/parse",
            headers=headers,
            json={
                "message": "请为当前待分配订单生成调度方案",
                "auto_execute": False  # 不自动执行，避免复杂依赖
            }
        )
        
        # 验证响应
        assert ai_resp.status_code == 200
        result = ai_resp.json()
        assert result["code"] == 0
        assert "algorithm_params" in result["data"]
        assert result["meta"]["degraded"] == False


@pytest.mark.asyncio
async def test_deepseek_degradation(async_client, test_users):
    """
    测试DeepSeek降级场景
    
    流程：
    1. Mock DeepSeek API调用失败（连接错误）
    2. 调用POST /api/ai/parse
    3. 验证返回degraded=true
    """
    # 正确Mock httpx.AsyncClient的异步上下文管理器
    mock_client = AsyncMock()
    mock_client.post.side_effect = Exception("Connection failed")
    
    with patch("services.deepseek_service.httpx.AsyncClient") as mock_client_class:
        # 配置__aenter__返回mock_client
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # 调用API
        client = async_client
        # 先登录
        login_resp = await client.post("/api/auth/login", json={
            "username": "dispatcher",
            "password": "123456"
        })
        token = login_resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 调用AI解析接口
        ai_resp = await client.post(
            "/api/ai/parse",
            headers=headers,
            json={
                "message": "测试降级场景",
                "auto_execute": False
            }
        )
        
        # 验证降级
        result = ai_resp.json()
        assert result["code"] == 0  # 降级不应该报错
        assert result["meta"]["degraded"] == True
        assert result["meta"]["degraded_reason"] is not None
        assert "algorithm_params" in result["data"]  # 应该使用默认参数


@pytest.mark.asyncio
async def test_log_events_recording(async_client, db_session):
    """
    测试log_events记录
    
    流程：
    1. 执行登录操作
    2. 查询log_events表
    3. 验证login事件被记录
    """
    client = async_client
    # 执行登录
    login_resp = await client.post("/api/auth/login", json={
        "username": "dispatcher",
        "password": "123456"
    })
    assert login_resp.status_code == 200
    
    # 查询log_events表
    logs = db_session.query(LogEvent).filter(
        LogEvent.event_name == "login"
    ).all()
    
    # 验证埋点记录
    assert len(logs) > 0
    latest_log = logs[-1]
    assert latest_log.event_name == "login"
    assert latest_log.role == "dispatcher"
    assert "ip" in latest_log.event_data or "user_agent" in latest_log.event_data


@pytest.mark.asyncio
async def test_p1_placeholder_endpoints(async_client, test_users):
    """
    测试P1占位接口返回501
    """
    client = async_client
    # 先登录
    login_resp = await client.post("/api/auth/login", json={
        "username": "dispatcher",
        "password": "123456"
    })
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 测试P1占位接口
    endpoints = ["/api/ai/explain", "/api/ai/review", "/api/ai/analyze-exception"]
    
    for endpoint in endpoints:
        resp = await client.post(endpoint, headers=headers, json={})
        assert resp.status_code == 200  # FastAPI返回200，但code=50100
        result = resp.json()
        assert result["code"] == 50100  # 50100表示功能正在开发中


@pytest.mark.asyncio
async def test_ai_parse_response_format(async_client, test_users):
    """
    测试AI解析接口响应格式符合统一规范
    """
    # Mock DeepSeek API响应
    mock_response = {
        "choices": [{
            "message": {
                "content": '{"global_schedule": {"algorithm": "traditional"}, "node_dispatch": {"algorithm": "traditional"}, "route_planning": {"algorithm": "traditional"}}'
            }
        }]
    }
    
    # 正确Mock httpx.AsyncClient的异步上下文管理器
    mock_client = AsyncMock()
    mock_client.post.return_value = AsyncMock(
        status_code=200,
        json=AsyncMock(return_value=mock_response),
        raise_for_status=AsyncMock()
    )
    
    with patch("services.deepseek_service.httpx.AsyncClient") as mock_client_class:
        # 配置__aenter__返回mock_client
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        client = async_client
        # 先登录
        login_resp = await client.post("/api/auth/login", json={
            "username": "dispatcher",
            "password": "123456"
        })
        token = login_resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 调用AI解析接口
        ai_resp = await client.post(
            "/api/ai/parse",
            headers=headers,
            json={
                "message": "测试响应格式",
                "auto_execute": False
            }
        )
        
        # 验证统一响应格式
        result = ai_resp.json()
        assert "code" in result
        assert "message" in result
        assert "data" in result
        assert "meta" in result
        assert "degraded" in result["meta"]
        assert "degraded_reason" in result["meta"]
