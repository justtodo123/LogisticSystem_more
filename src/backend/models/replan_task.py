from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Index, Integer, String, Text, func

from .base import Base


class ReplanTask(Base):
    """重规划 Saga 的持久化任务骨架。"""

    __tablename__ = "replan_tasks"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED')",
            name="ck_replan_tasks_status",
        ),
        CheckConstraint(
            "current_step IN ('F007', 'F021', 'F005', 'F006', 'NOTIFICATION', 'COMPLETED')",
            name="ck_replan_tasks_current_step",
        ),
        CheckConstraint("retry_count >= 0", name="ck_replan_tasks_retry_count"),
        CheckConstraint("version >= 1", name="ck_replan_tasks_version"),
        Index("uq_replan_tasks_idempotency_key", "idempotency_key", unique=True),
        Index("ix_replan_tasks_status_step", "status", "current_step"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    idempotency_key = Column(String(128), nullable=False)
    request_fingerprint = Column(String(64), nullable=True)
    operation_type = Column(String(16), nullable=True)
    original_resource_id = Column(Integer, nullable=True)
    original_resource_code = Column(String(64), nullable=True)
    new_schedule_id = Column(Integer, nullable=True)
    new_schedule_code = Column(String(64), nullable=True)
    dispatch_batch_id = Column(Integer, nullable=True)
    dispatch_batch_code = Column(String(64), nullable=True)
    new_route_id = Column(Integer, nullable=True)
    new_route_code = Column(String(64), nullable=True)
    status = Column(String(16), nullable=False, default="PENDING", server_default="PENDING")
    current_step = Column(String(16), nullable=False, default="F007", server_default="F007")
    retry_count = Column(Integer, nullable=False, default=0, server_default="0")
    last_error = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=1, server_default="1")
    manual_required = Column(Boolean, nullable=False, default=False, server_default="0")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
