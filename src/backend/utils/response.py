from typing import Any


def success_response(data: Any = None, meta: dict | None = None) -> dict:
    """成功响应"""
    return {
        "code": 0,
        "message": "success",
        "data": data,
        "meta": meta or {"degraded": False, "degraded_reason": None},
    }


def error_response(
    code: int,
    message: str,
    data: Any = None,
    *,
    meta: dict | None = None,
) -> dict:
    """错误响应；data 参数仅为旧调用方兼容，异常契约固定为 null。"""
    return {
        "code": code,
        "message": message,
        "data": None,
        "meta": meta or {},
    }
