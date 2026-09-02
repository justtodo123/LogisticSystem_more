"""领域错误类型；不依赖 FastAPI，响应由全局 handler 渲染。"""

from collections.abc import Mapping
from typing import Any

from core.error_codes import ErrorDefinition, get_error_definition


_SAFE_META_KEYS = frozenset({"errors", "retry_after", "request_id", "trace_id", "task_id", "degraded", "degraded_reason"})
_MAX_META_ITEMS = 20
_MAX_TEXT_LENGTH = 256


def _safe_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value or len(value) > _MAX_TEXT_LENGTH:
        return None
    return value


def sanitize_meta(meta: Mapping[str, Any] | None) -> dict[str, Any]:
    """保留有限、JSON 友好的公开错误元数据。"""
    if not isinstance(meta, Mapping):
        return {}
    result: dict[str, Any] = {}
    for key in _SAFE_META_KEYS:
        if key not in meta:
            continue
        value = meta[key]
        if key == "errors":
            if not isinstance(value, list):
                continue
            safe_errors = []
            for item in value[:_MAX_META_ITEMS]:
                if not isinstance(item, Mapping):
                    continue
                safe_item = {
                    field: _safe_text(item.get(field))
                    for field in ("loc", "type", "msg")
                    if _safe_text(item.get(field)) is not None
                }
                if safe_item:
                    safe_errors.append(safe_item)
            if safe_errors:
                result[key] = safe_errors
        elif key == "retry_after":
            if isinstance(value, (int, float)) and value >= 0:
                result[key] = value
        elif key == "degraded":
            if isinstance(value, bool):
                result[key] = value
        else:
            safe_value = _safe_text(value)
            if safe_value is not None:
                result[key] = safe_value
    return result


class DomainError(Exception):
    """带有登记业务码的领域异常。"""

    def __init__(
        self,
        code: int,
        *,
        message: str | None = None,
        meta: Mapping[str, Any] | None = None,
        cause: BaseException | None = None,
        log_context: Mapping[str, Any] | None = None,
    ) -> None:
        definition: ErrorDefinition = get_error_definition(code)
        public_message = _safe_text(message) or definition.message
        self.definition = definition
        self.code = definition.code
        self.http_status = definition.http_status
        self.public_message = public_message
        self.meta = sanitize_meta(meta)
        self.cause = cause
        self.log_context = dict(log_context or {})
        super().__init__(public_message)

    def __repr__(self) -> str:
        return f"DomainError(code={self.code}, http_status={self.http_status})"
