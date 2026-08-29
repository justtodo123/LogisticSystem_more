from sqlalchemy import CheckConstraint, Column, DateTime, Index, Integer, JSON, String, Text, func

from .base import Base


class OutboxEvent(Base):
    """事务消息 outbox；业务事务只入队，独立 worker 负责投递。"""

    __tablename__ = "outbox_events"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'retry', 'delivered', 'dead-letter')",
            name="ck_outbox_events_status",
        ),
        CheckConstraint("retry_count >= 0", name="ck_outbox_events_retry_count"),
        Index("uq_outbox_events_dedup_key", "dedup_key", unique=True),
        Index("ix_outbox_events_status_available_at", "status", "available_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    dedup_key = Column(String(128), nullable=False)
    event_type = Column(String(64), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String(16), nullable=False, default="pending", server_default="pending")
    retry_count = Column(Integer, nullable=False, default=0, server_default="0")
    last_error = Column(Text, nullable=True)
    available_at = Column(DateTime, nullable=False, server_default=func.now())
    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
