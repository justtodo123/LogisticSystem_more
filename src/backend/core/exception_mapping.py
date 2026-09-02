"""全局异常处理使用的安全映射工具。"""

from collections.abc import Mapping
from typing import Any

from core.error_codes import (
    CODE_TOKEN_EXPIRED,
    ErrorDefinition,
    get_default_error_definition,
    get_error_definition,
)
from core.errors import sanitize_meta
from core.request_context import context_as_dict, get_request_context


_SAFE_RESPONSE_HEADERS = frozenset(
    {
        "content-disposition",
        "www-authenticate",
        "retry-after",
        "x-request-id",
        "x-trace-id",
        "x-task-id",
    }
)
_MAX_VALIDATION_ERRORS = 20
_MAX_VALIDATION_TEXT = 256


def safe_response_headers(headers: Mapping[str, str] | None) -> dict[str, str]:
    """只保留协议相关且可安全返回的响应头。"""
    if not isinstance(headers, Mapping):
        return {}
    return {
        key: value
        for key, value in headers.items()
        if key.lower() in _SAFE_RESPONSE_HEADERS and isinstance(value, str)
    }


def resolve_legacy_http_error(
    status_code: int,
    detail: Any,
) -> tuple[ErrorDefinition, str, dict[str, Any]]:
    """将旧 HTTPException.detail 安全映射到 registry。"""
    definition = get_default_error_definition(status_code)
    meta: dict[str, Any] = {}

    if isinstance(detail, str):
        normalized = detail.lower()
        if status_code == 401 and ("过期" in detail or "expired" in normalized):
            definition = get_error_definition(CODE_TOKEN_EXPIRED)
        return definition, definition.message, meta

    if isinstance(detail, Mapping):
        candidate_code = detail.get("code")
        if isinstance(candidate_code, int):
            try:
                candidate = get_error_definition(candidate_code)
            except ValueError:
                candidate = None
            if candidate is not None and candidate.http_status == status_code:
                definition = candidate
        meta = sanitize_meta(detail.get("meta"))

    return definition, definition.message, meta


def validation_error_meta(errors: list[dict[str, Any]]) -> dict[str, Any]:
    """裁剪 Pydantic 错误，禁止回显 input/context。"""
    safe_errors: list[dict[str, str]] = []
    for error in errors[:_MAX_VALIDATION_ERRORS]:
        loc = ".".join(str(part) for part in error.get("loc", ()))
        error_type = str(error.get("type", "validation_error"))
        message = str(error.get("msg", "参数无效"))
        safe_errors.append(
            {
                "loc": loc[:_MAX_VALIDATION_TEXT],
                "type": error_type[:_MAX_VALIDATION_TEXT],
                "msg": message[:_MAX_VALIDATION_TEXT],
            }
        )
    return sanitize_meta({"errors": safe_errors})


def attach_request_meta(meta: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Merge request/trace/task IDs into public error meta without overwriting callers."""
    merged: dict[str, Any] = dict(meta or {})
    current = get_request_context()
    if current is None:
        return sanitize_meta(merged)
    merged.setdefault("request_id", current.request_id)
    merged.setdefault("trace_id", current.trace_id)
    if current.task_id:
        merged.setdefault("task_id", current.task_id)
    return sanitize_meta(merged)


def request_log_context(request: Any) -> dict[str, str]:
    """提取不含 query/body 的请求诊断上下文。"""
    context = {
        "method": str(getattr(request, "method", ""))[:16],
        "path": str(getattr(getattr(request, "url", None), "path", ""))[:256],
    }
    context.update(context_as_dict())
    headers = getattr(request, "headers", {})
    if isinstance(headers, Mapping):
        for header, key in (
            ("x-request-id", "request_id"),
            ("x-trace-id", "trace_id"),
            ("x-task-id", "task_id"),
        ):
            value = headers.get(header)
            if isinstance(value, str) and 0 < len(value) <= 256:
                context.setdefault(key, value)
    return context
