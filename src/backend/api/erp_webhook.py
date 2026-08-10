"""
ERP 对接 Webhook（T5-1）：外部系统订单推送

- POST /api/erp/orders — 接收 ERP/WMS 推送的 JSON 订单，返回 201 + 内部订单号

认证策略（verify_erp_auth）：
- 配置了 settings.ERP_API_KEY 时，要求 X-ERP-API-Key 请求头匹配（机器对机器）
- 未配置时回退到标准 Bearer JWT（dispatcher 角色），便于本地联调
"""
from typing import List, Optional

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config.database import get_db, settings
from core.error_codes import CODE_SUCCESS
from schemas.order import GoodsCreate, OrderCreate
from services.order_service import OrderService

router = APIRouter(prefix="/api/erp", tags=["ERP 对接"])

# auto_error=False：允许无 Authorization 头（API Key 模式下不要求 JWT）
_security = HTTPBearer(auto_error=False)


class ErpOrderCreate(BaseModel):
    """ERP 推送订单模型"""
    erp_order_no: str                     # ERP 侧订单号（外部关联用）
    destination_node_code: str            # 目的地 0 级分拣中心编码
    time_window: str                      # 时效要求
    storage_center_code: Optional[str] = None  # 可选：货物起点存储中心
    goods: List[GoodsCreate]


async def verify_erp_auth(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
    x_erp_api_key: Optional[str] = Header(default=None, alias="X-ERP-API-Key"),
) -> None:
    """ERP 对接认证：API Key 优先，未配置时回退 JWT"""
    if settings.ERP_API_KEY:
        if not x_erp_api_key or x_erp_api_key != settings.ERP_API_KEY:
            raise HTTPException(status_code=401, detail="ERP API Key 无效")
        return

    # 回退：标准 JWT 认证
    if credentials is None:
        raise HTTPException(status_code=401, detail="未登录或缺少认证")
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET, algorithms=["HS256"])
        if not payload.get("sub"):
            raise HTTPException(status_code=401, detail="未登录或 Token 无效")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已过期，请重新登录")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="未登录或 Token 无效")


@router.post("/orders", summary="ERP 推送订单")
async def erp_push_orders(
    order: ErpOrderCreate,
    db: Session = Depends(get_db),
    _auth: None = Depends(verify_erp_auth),
):
    """接收 ERP/WMS 推送订单，创建订单并返回 201 + 内部订单号。

    请求体字段：
    - erp_order_no：ERP 侧订单号（原样回传便于外部关联）
    - destination_node_code：目的地 0 级分拣中心编码
    - time_window：时效要求
    - storage_center_code：可选，货物起点存储中心编码（缺省自动分配）
    - goods：货物列表（goods_name / goods_type / weight / volume）
    """
    order_create = OrderCreate(
        destination_node_code=order.destination_node_code,
        storage_center_code=order.storage_center_code,
        time_window=order.time_window,
        goods=order.goods,
    )
    result = await OrderService.create_order(order_create, db)

    if result.get("code") != CODE_SUCCESS:
        # 业务校验失败（目的地节点不存在 / 非 0 级分拣中心 / 存储中心不存在等）→ 400
        return JSONResponse(status_code=400, content=result)

    result["data"]["erp_order_no"] = order.erp_order_no
    return JSONResponse(status_code=201, content=result)
