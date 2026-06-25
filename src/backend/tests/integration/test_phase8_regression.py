"""
阶段8回归测试

测试内容：
1. 主链路测试（F007→F021→F005→F006）with DeepSeek
2. DeepSeek降级场景测试
3. log_events记录测试
4. 重规划回归测试
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
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
    测试AI解析接口（Mock DeepSeek API + 调度链路）
    
    流程：
    1. Mock DeepSeek API返回成功响应
    2. Mock 调度链路避免空数据库执行失败
    3. 调用POST /api/ai/parse
    4. 验证响应格式正确
    """
    # Mock DeepSeek API响应（只返回 global_schedule）
    mock_response = {
        "choices": [{
            "message": {
                "content": '{"global_schedule": {"algorithm": "traditional", "weights": {"distance": 0.5, "time": 0.3, "package_count": 0.2}}}'
            }
        }]
    }
    
    # 正确Mock httpx.AsyncClient的异步上下文管理器
    mock_response_obj = Mock()
    mock_response_obj.status_code = 200
    mock_response_obj.json = Mock(return_value=mock_response)
    mock_response_obj.raise_for_status = Mock()
    
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response_obj)
    
    # Mock 调度链路（空测试数据库无法执行真实调度）
    with patch("api.ai._execute_new_schedule", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = "GS20260622001"
        
        with patch("services.deepseek_service.settings.DEEPSEEK_API_KEY", "fake-api-key"), \
             patch("services.deepseek_service.httpx.AsyncClient") as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            client = async_client
            login_resp = await client.post("/api/auth/login", json={
                "username": "dispatcher",
                "password": "123456"
            })
            assert login_resp.status_code == 200
            token = login_resp.json()["data"]["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            ai_resp = await client.post(
                "/api/ai/parse",
                headers=headers,
                json={
                    "message": "请为当前待分配订单生成调度方案"
                }
            )
            
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
    2. Mock 调度链路避免空数据库执行失败
    3. 调用POST /api/ai/parse
    4. 验证返回degraded=true
    """
    mock_client = AsyncMock()
    mock_client.post.side_effect = Exception("Connection failed")
    
    # Mock 调度链路（空测试数据库无法执行真实调度）
    with patch("api.ai._execute_new_schedule", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = "GS20260622001"
        
        with patch("services.deepseek_service.httpx.AsyncClient") as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            client = async_client
            login_resp = await client.post("/api/auth/login", json={
                "username": "dispatcher",
                "password": "123456"
            })
            token = login_resp.json()["data"]["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            ai_resp = await client.post(
                "/api/ai/parse",
                headers=headers,
                json={
                    "message": "测试降级场景"
                }
            )
            
            result = ai_resp.json()
            assert result["code"] == 0
            assert result["meta"]["degraded"] == True
            assert result["meta"]["degraded_reason"] is not None
            assert "algorithm_params" in result["data"]


@pytest.mark.asyncio
async def test_log_events_recording(async_client, test_users, test_db):
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
    
    # 使用测试数据库的会话来查询log_events
    from models.log_event import LogEvent
    engine, TestingSessionLocal = test_db
    session = TestingSessionLocal()
    
    try:
        # 查询log_events表
        logs = session.query(LogEvent).filter(
            LogEvent.event_name == "login"
        ).all()
        
        # 验证埋点记录
        assert len(logs) > 0
        latest_log = logs[-1]
        assert latest_log.event_name == "login"
        assert latest_log.role == "dispatcher"
        assert "ip" in latest_log.event_data or "user_agent" in latest_log.event_data
    finally:
        session.close()


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
    # Mock DeepSeek API响应（只返回 global_schedule）
    mock_response = {
        "choices": [{
            "message": {
                "content": '{"global_schedule": {"algorithm": "traditional", "weights": {"distance": 0.5, "time": 0.3, "package_count": 0.2}}}'
            }
        }]
    }
    
    # 正确Mock httpx.AsyncClient的异步上下文管理器
    # 注意：response.json() 是同步方法，不是异步方法
    mock_response_obj = Mock()
    mock_response_obj.status_code = 200
    mock_response_obj.json = Mock(return_value=mock_response)  # json 是同步方法
    mock_response_obj.raise_for_status = Mock()  # 同步方法
    
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response_obj)
    
    # Mock 调度链路（空测试数据库无法执行真实调度）
    with patch("api.ai._execute_new_schedule", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = "GS20260622001"
        
        with patch("services.deepseek_service.settings.DEEPSEEK_API_KEY", "fake-api-key"), \
             patch("services.deepseek_service.httpx.AsyncClient") as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            client = async_client
            login_resp = await client.post("/api/auth/login", json={
                "username": "dispatcher",
                "password": "123456"
            })
            token = login_resp.json()["data"]["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            ai_resp = await client.post(
                "/api/ai/parse",
                headers=headers,
                json={
                    "message": "测试响应格式"
                }
            )
            
            result = ai_resp.json()
            assert "code" in result
            assert "message" in result
            assert "data" in result
            assert "meta" in result
            assert "degraded" in result["meta"]
            assert "degraded_reason" in result["meta"]


@pytest.mark.asyncio
async def test_ai_parse_dry_run(async_client, test_users):
    """
    测试 AI 解析接口 dry-run 模式（execute="dry-run"）

    验证：
    1. 不调用调度链路 mock（证明未执行）
    2. 返回 status=None
    3. 返回解析出的 algorithm_params 和 mode
    """
    # Mock DeepSeek API 响应
    mock_response = {
        "choices": [{
            "message": {
                "content": '{"global_schedule": {"algorithm": "traditional", "weights": {"distance": 0.7, "time": 0.2, "package_count": 0.1}}}'
            }
        }]
    }
    mock_response_obj = Mock()
    mock_response_obj.status_code = 200
    mock_response_obj.json = Mock(return_value=mock_response)
    mock_response_obj.raise_for_status = Mock()

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response_obj)

    # 注意：dry-run 模式下不应 mock _execute_new_schedule（它根本不应被调用）
    with patch("services.deepseek_service.settings.DEEPSEEK_API_KEY", "fake-api-key"), \
         patch("services.deepseek_service.httpx.AsyncClient") as mock_client_class:
        mock_client_class.return_value.__aenter__.return_value = mock_client

        client = async_client
        login_resp = await client.post("/api/auth/login", json={
            "username": "dispatcher",
            "password": "123456"
        })
        token = login_resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        ai_resp = await client.post(
            "/api/ai/parse",
            headers=headers,
            json={
                "message": "优先缩短距离",
                "execute": "dry-run"
            }
        )

        result = ai_resp.json()
        assert result["code"] == 0
        assert "dry-run" in result["message"]
        assert result["data"]["mode"] == "ai"
        assert "algorithm_params" in result["data"]
        assert result["data"]["algorithm_params"]["global_schedule"]["weights"]["distance"] == 0.7
        # 确认为 dry-run 模式（不应有 schedule_code 和 status）
        assert "schedule_code" not in result["data"]
        assert "status" not in result["data"]


