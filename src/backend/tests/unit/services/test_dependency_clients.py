"""HTTP dependencies propagate trace headers and record call metrics."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from core.metrics import metrics
from core.request_context import RequestContext, bind_request_context, reset_request_context
from services.deepseek_service import DeepSeekService
from services.notification.wechat_work import WechatWorkChannel


def setup_function():
    metrics.reset()


@pytest.mark.asyncio
async def test_deepseek_post_propagates_trace_headers(monkeypatch):
    monkeypatch.setattr("services.deepseek_service.settings.DEEPSEEK_API_KEY", "secret-key")
    monkeypatch.setattr("services.deepseek_service.settings.DEEPSEEK_API_BASE", "https://api.deepseek.com")
    monkeypatch.setattr("services.deepseek_service.settings.DEEPSEEK_MODEL", "deepseek-chat")
    monkeypatch.setattr("services.deepseek_service.settings.DEEPSEEK_TIMEOUT_SECONDS", 1)

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "{}"}}]
    }
    mock_response.raise_for_status.return_value = None
    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    token = bind_request_context(
        RequestContext(request_id="req-ai-1", trace_id="trc-ai-1", task_id="task-ai-1")
    )
    try:
        with patch("services.deepseek_service.httpx.AsyncClient", return_value=mock_client):
            await DeepSeekService._post_chat("hello")
    finally:
        reset_request_context(token)

    kwargs = mock_client.post.await_args.kwargs
    assert kwargs["headers"]["X-Request-ID"] == "req-ai-1"
    assert kwargs["headers"]["X-Trace-ID"] == "trc-ai-1"
    assert kwargs["headers"]["X-Task-ID"] == "task-ai-1"
    assert kwargs["headers"]["Authorization"] == "Bearer secret-key"
    assert metrics.total("dependency_calls_total", dependency="deepseek", operation="chat", status="ok") == 1


@pytest.mark.asyncio
async def test_wechat_webhook_propagates_trace_headers_and_hides_failures():
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    token = bind_request_context(RequestContext(request_id="req-wx-1", trace_id="trc-wx-1"))
    try:
        with patch("services.notification.wechat_work.httpx.AsyncClient", return_value=mock_client):
            ok = await WechatWorkChannel(webhook_url="https://example.com/webhook").send(
                "subject", "body", {}
            )
    finally:
        reset_request_context(token)

    assert ok is True
    kwargs = mock_client.post.await_args.kwargs
    assert kwargs["headers"]["X-Request-ID"] == "req-wx-1"
    assert kwargs["headers"]["X-Trace-ID"] == "trc-wx-1"
    assert metrics.total("dependency_calls_total", dependency="wechat", operation="webhook", status="ok") == 1


@pytest.mark.asyncio
async def test_wechat_timeout_is_recorded_without_raising():
    mock_client = MagicMock()
    mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    with patch("services.notification.wechat_work.httpx.AsyncClient", return_value=mock_client):
        ok = await WechatWorkChannel(webhook_url="https://example.com/webhook").send(
            "subject", "body", {}
        )
    assert ok is False
    assert metrics.total("dependency_errors_total") == 1
