"""
业务级校验规则

提供输入校验函数，在路由层或服务层注入，
对请求参数进行业务级验证（超出 Pydantic 类型校验范围）。
"""
import re
from typing import Optional, List, Tuple


# ── 编码格式 ──

_CODE_PATTERNS = {
    "order_code": re.compile(r"^O\d{8,}$"),
    "goods_code": re.compile(r"^G\d{8,}$"),
    "package_code": re.compile(r"^PKG\d{8,}$"),
    "vehicle_code": re.compile(r"^V\d{8,}$"),
    "driver_code": re.compile(r"^D\d{8,}$"),
    "node_code": re.compile(r"^(SC|SO)\d{3,}$"),
    "schedule_code": re.compile(r"^GS\d{8,}$"),
    "batch_code": re.compile(r"^DB\d{8,}$"),
    "route_code": re.compile(r"^RT\d{8,}$"),
    "event_code": re.compile(r"^EE\d{8,}$"),
}


def validate_code(
    code: str, code_type: str, allow_none: bool = False
) -> Tuple[bool, Optional[str]]:
    """校验业务编码格式

    Args:
        code: 业务编码
        code_type: 编码类型（order_code/goods_code/...）
        allow_none: 是否允许空值

    Returns:
        (is_valid, error_message)
    """
    if not code:
        return (False, f"{code_type} 不能为空") if not allow_none else (True, None)

    pattern = _CODE_PATTERNS.get(code_type)
    if pattern is None:
        return True, None  # 未知类型跳过校验

    if not pattern.match(code):
        return False, f"{code_type} '{code}' 格式无效"
    return True, None


def validate_page_params(page: int, page_size: int) -> List[str]:
    """校验分页参数"""
    errors = []
    if page < 1:
        errors.append("page 必须 >= 1")
    if page_size < 1:
        errors.append("page_size 必须 >= 1")
    if page_size > 200:
        errors.append("page_size 不能超过 200")
    return errors


TIME_WINDOW_MAX_LEN = 32


def normalize_time_window_requirement(value) -> Tuple[Optional[str], Optional[str]]:
    """时效要求：自由文本最小约束，不解析起止时间。

    允许「全天」、带日期前缀、``9:00-18:00`` 等展示文本。
    只做 strip、非空、控制字符和长度（对齐 orders.time_window VARCHAR(32)）。
    """
    if value is None:
        return None, "时效要求不能为空"
    text = str(value).strip()
    if not text:
        return None, "时效要求不能为空"
    if any(ord(ch) < 32 for ch in text):
        return None, "时效要求不能包含控制字符"
    if len(text) > TIME_WINDOW_MAX_LEN:
        return None, f"时效要求不能超过 {TIME_WINDOW_MAX_LEN} 个字符"
    return text, None


def validate_time_window(time_window: str) -> Tuple[bool, Optional[str]]:
    """兼容旧名。订单时效要求按自由文本校验，不再要求 HH:MM-HH:MM。"""
    _, error = normalize_time_window_requirement(time_window)
    return error is None, error


def validate_idempotency_key(key: str) -> Tuple[bool, Optional[str]]:
    """校验幂等键格式"""
    if not key:
        return False, "X-Idempotency-Key 不能为空"
    if len(key) > 128:
        return False, "X-Idempotency-Key 长度不能超过 128 字符"
    if not re.match(r"^[a-zA-Z0-9\-_]+$", key):
        return False, "X-Idempotency-Key 只能包含字母、数字、短横线和下划线"
    return True, None
