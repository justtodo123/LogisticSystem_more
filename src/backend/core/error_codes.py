"""统一错误码与公开错误定义。"""

from dataclasses import dataclass
from http import HTTPStatus
from types import MappingProxyType
from typing import Mapping


# 通用错误码
CODE_SUCCESS = 0
CODE_PARAM_ERROR = 40000
CODE_UNAUTHORIZED = 40100
CODE_TOKEN_EXPIRED = 40101
CODE_FORBIDDEN = 40300
CODE_NOT_FOUND = 40400
CODE_CONFLICT = 40900
CODE_STATE_CONFLICT = 40901
CODE_IDEMPOTENCY_IN_PROGRESS = 40902
CODE_IDEMPOTENCY_PAYLOAD_MISMATCH = 40903
CODE_CODE_RANGE_EXHAUSTED = 40904
CODE_CODE_ALLOCATION_CONFLICT = 40905
CODE_INTERNAL_ERROR = 50000
CODE_DATABASE_ERROR = 50001
CODE_REQUEST_TIMEOUT = 50400
CODE_REQUEST_BODY_TOO_LARGE = 41300

# 业务错误码
CODE_ORDER_NOT_FOUND = 40001
CODE_ORDER_STATUS_NOT_ALLOWED = 40002
CODE_GOODS_NOT_FOUND = 40003
CODE_PACKAGE_NOT_FOUND = 40004
CODE_PACKAGE_STATUS_NOT_ALLOWED = 40005
CODE_VEHICLE_NOT_FOUND = 40006
CODE_VEHICLE_STATUS_NOT_ALLOWED = 40007
CODE_DRIVER_NOT_FOUND = 40008
CODE_DRIVER_STATUS_NOT_ALLOWED = 40009
CODE_NODE_NOT_FOUND = 40010
CODE_STORAGE_CENTER_NOT_FOUND = 40011
CODE_SORTING_CENTER_NOT_FOUND = 40012
CODE_ORDER_IMPORT_FAILED = 40013

# 幂等控制（T0-4 新增）
CODE_IDEMPOTENCY_KEY_INVALID = 40020
CODE_IDEMPOTENCY_KEY_MISSING = 40021

# 审计日志（T0-3 新增）
CODE_AUDIT_PERMISSION_DENIED = 40301


@dataclass(frozen=True, slots=True)
class ErrorDefinition:
    """可安全公开的错误定义。"""

    code: int
    http_status: int
    message: str
    owner: str
    callers: tuple[str, ...] = ()


def _definition(
    code: int,
    http_status: int,
    message: str,
    owner: str,
    *callers: str,
) -> ErrorDefinition:
    return ErrorDefinition(code, http_status, message, owner, callers)


_ERROR_DEFINITIONS = (
    _definition(CODE_PARAM_ERROR, HTTPStatus.UNPROCESSABLE_ENTITY, "参数校验失败", "core"),
    _definition(CODE_UNAUTHORIZED, HTTPStatus.UNAUTHORIZED, "未登录或 Token 无效", "auth"),
    _definition(CODE_TOKEN_EXPIRED, HTTPStatus.UNAUTHORIZED, "Token 已过期，请重新登录", "auth"),
    _definition(CODE_FORBIDDEN, HTTPStatus.FORBIDDEN, "权限不足", "auth"),
    _definition(CODE_NOT_FOUND, HTTPStatus.NOT_FOUND, "资源不存在", "core"),
    _definition(CODE_CONFLICT, HTTPStatus.CONFLICT, "资源冲突", "core"),
    _definition(
        CODE_STATE_CONFLICT,
        HTTPStatus.CONFLICT,
        "资源状态已变化，当前操作不能继续",
        "R2-01",
        "schedule",
        "arrival",
        "ai_suggestion",
    ),
    _definition(
        CODE_IDEMPOTENCY_IN_PROGRESS,
        HTTPStatus.CONFLICT,
        "相同幂等请求正在处理，请稍后重试",
        "R2-02",
        "idempotency_middleware",
    ),
    _definition(
        CODE_IDEMPOTENCY_PAYLOAD_MISMATCH,
        HTTPStatus.CONFLICT,
        "幂等键已用于不同请求",
        "R2-02",
        "idempotency_middleware",
    ),
    _definition(
        CODE_CODE_RANGE_EXHAUSTED,
        HTTPStatus.CONFLICT,
        "业务编号号段已耗尽",
        "R2-02",
        "code_allocation",
        "schedule",
        "packaging",
        "route",
        "dispatch",
    ),
    _definition(
        CODE_CODE_ALLOCATION_CONFLICT,
        HTTPStatus.CONFLICT,
        "业务编号分配冲突，请稍后重试",
        "R2-02",
        "code_allocation",
        "schedule",
        "packaging",
        "route",
        "dispatch",
    ),
    _definition(CODE_INTERNAL_ERROR, HTTPStatus.INTERNAL_SERVER_ERROR, "服务器内部错误", "core"),
    _definition(CODE_DATABASE_ERROR, HTTPStatus.INTERNAL_SERVER_ERROR, "数据库服务暂时不可用", "core"),
    _definition(CODE_REQUEST_TIMEOUT, HTTPStatus.GATEWAY_TIMEOUT, "请求超时，请稍后重试", "core"),
    _definition(
        CODE_REQUEST_BODY_TOO_LARGE,
        HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
        "请求体超过允许大小",
        "idempotency",
        "idempotency_middleware",
    ),
    _definition(CODE_ORDER_NOT_FOUND, HTTPStatus.NOT_FOUND, "订单不存在", "orders"),
    _definition(CODE_ORDER_STATUS_NOT_ALLOWED, HTTPStatus.CONFLICT, "订单状态不允许当前操作", "orders"),
    _definition(CODE_GOODS_NOT_FOUND, HTTPStatus.NOT_FOUND, "货物不存在", "goods"),
    _definition(CODE_PACKAGE_NOT_FOUND, HTTPStatus.NOT_FOUND, "包裹不存在", "packages"),
    _definition(CODE_PACKAGE_STATUS_NOT_ALLOWED, HTTPStatus.CONFLICT, "包裹状态不允许当前操作", "packages"),
    _definition(CODE_VEHICLE_NOT_FOUND, HTTPStatus.NOT_FOUND, "车辆不存在", "vehicles"),
    _definition(CODE_VEHICLE_STATUS_NOT_ALLOWED, HTTPStatus.CONFLICT, "车辆状态不允许当前操作", "vehicles"),
    _definition(CODE_DRIVER_NOT_FOUND, HTTPStatus.NOT_FOUND, "司机不存在", "drivers"),
    _definition(CODE_DRIVER_STATUS_NOT_ALLOWED, HTTPStatus.CONFLICT, "司机状态不允许当前操作", "drivers"),
    _definition(CODE_NODE_NOT_FOUND, HTTPStatus.NOT_FOUND, "节点不存在", "nodes"),
    _definition(CODE_STORAGE_CENTER_NOT_FOUND, HTTPStatus.NOT_FOUND, "仓储中心不存在", "nodes"),
    _definition(CODE_SORTING_CENTER_NOT_FOUND, HTTPStatus.NOT_FOUND, "分拣中心不存在", "nodes"),
    _definition(CODE_ORDER_IMPORT_FAILED, HTTPStatus.BAD_REQUEST, "订单导入失败", "orders"),
    _definition(CODE_IDEMPOTENCY_KEY_INVALID, HTTPStatus.BAD_REQUEST, "幂等键格式无效", "idempotency"),
    _definition(CODE_IDEMPOTENCY_KEY_MISSING, HTTPStatus.BAD_REQUEST, "缺少幂等键", "idempotency"),
    _definition(CODE_AUDIT_PERMISSION_DENIED, HTTPStatus.FORBIDDEN, "无权查看审计日志", "audit"),
)

ERROR_REGISTRY: Mapping[int, ErrorDefinition] = MappingProxyType(
    {definition.code: definition for definition in _ERROR_DEFINITIONS}
)

if len(ERROR_REGISTRY) != len(_ERROR_DEFINITIONS):
    raise RuntimeError("错误码 registry 存在重复 code")


_STATUS_DEFAULT_CODES: Mapping[int, int] = MappingProxyType(
    {
        HTTPStatus.BAD_REQUEST: CODE_PARAM_ERROR,
        HTTPStatus.UNAUTHORIZED: CODE_UNAUTHORIZED,
        HTTPStatus.FORBIDDEN: CODE_FORBIDDEN,
        HTTPStatus.NOT_FOUND: CODE_NOT_FOUND,
        HTTPStatus.CONFLICT: CODE_CONFLICT,
        HTTPStatus.UNPROCESSABLE_ENTITY: CODE_PARAM_ERROR,
        HTTPStatus.REQUEST_ENTITY_TOO_LARGE: CODE_REQUEST_BODY_TOO_LARGE,
        HTTPStatus.INTERNAL_SERVER_ERROR: CODE_INTERNAL_ERROR,
        HTTPStatus.GATEWAY_TIMEOUT: CODE_REQUEST_TIMEOUT,
    }
)


def get_error_definition(code: int) -> ErrorDefinition:
    """按业务错误码返回定义；未知错误码 fail closed。"""
    try:
        return ERROR_REGISTRY[code]
    except KeyError as exc:
        raise ValueError(f"未登记的错误码: {code}") from exc


def get_default_error_definition(http_status: int) -> ErrorDefinition:
    """按 HTTP status 返回安全默认定义。"""
    code = _STATUS_DEFAULT_CODES.get(http_status, CODE_INTERNAL_ERROR)
    return ERROR_REGISTRY[code]
