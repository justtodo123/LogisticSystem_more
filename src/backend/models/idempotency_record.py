"""
幂等记录模型

通过 X-Idempotency-Key 请求头实现写操作幂等：
已处理的 key 在 TTL 内返回缓存响应，避免重复执行。
"""
from sqlalchemy import CheckConstraint, Column, DateTime, Index, Integer, JSON, LargeBinary, String
from sqlalchemy.sql import func
from .base import Base


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PROCESSING', 'SUCCEEDED', 'FAILED', 'EXPIRED')",
            name="ck_idempotency_records_status",
        ),
        Index("ix_idempotency_records_status_expires_at", "status", "expires_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    idempotency_key = Column(String(128), unique=True, nullable=False, index=True)
    status = Column(String(16), nullable=False, default="PROCESSING")
    payload_hash = Column(String(64), nullable=True)
    claim_token = Column(String(36), nullable=True)
    http_status = Column(Integer, nullable=True)
    response_body = Column(LargeBinary, nullable=True)
    response_media_type = Column(String(255), nullable=True)
    response_headers = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)
