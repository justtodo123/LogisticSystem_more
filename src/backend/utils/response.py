from typing import Any


def success_response(data: Any = None, meta: dict | None = None) -> dict:
    """成功响应"""
    return {
        "code": 0,
        "message": "success",
        "data": data,
        "meta": meta or {"degraded": False, "degraded_reason": None},
    }


def error_response(code: int, message: str, data: Any = None) -> dict:
    """错误响应"""
    return {
        "code": code,
        "message": message,
        "data": data,
        "meta": {"degraded": False, "degraded_reason": None},
    }
