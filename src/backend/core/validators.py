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


def validate_time_window(time_window: str) -> Tuple[bool, Optional[str]]:
    """校验时间窗口格式（如 '08:00-12:00'）"""
    if not time_window:
        return True, None
    parts = time_window.split("-")
    if len(parts) != 2:
        return False, f"时间窗口 '{time_window}' 格式无效，应为 HH:MM-HH:MM"
    time_pattern = re.compile(r"^\d{2}:\d{2}$")
    if not (time_pattern.match(parts[0]) and time_pattern.match(parts[1])):
        return False, f"时间窗口 '{time_window}' 格式无效，应为 HH:MM-HH:MM"
    return True, None


def validate_idempotency_key(key: str) -> Tuple[bool, Optional[str]]:
    """校验幂等键格式"""
    if not key:
        return False, "X-Idempotency-Key 不能为空"
    if len(key) > 128:
        return False, "X-Idempotency-Key 长度不能超过 128 字符"
    if not re.match(r"^[a-zA-Z0-9\-_]+$", key):
        return False, "X-Idempotency-Key 只能包含字母、数字、短横线和下划线"
    return True, None
