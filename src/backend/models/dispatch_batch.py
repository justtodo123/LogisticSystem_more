from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class DispatchBatch(Base):
    """F005 调度批次表"""
    __tablename__ = "dispatch_batches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_code = Column(String(64), unique=True, nullable=False, index=True)
    global_schedule_id = Column(Integer, ForeignKey("global_schedules.id"), nullable=False)
    status = Column(String(32), nullable=False, server_default="pending")
    demo_mode = Column(Boolean, nullable=False, server_default="0")  # False
    l0_l1_dispatch_count = Column(Integer, nullable=False, server_default="0")
    l1_l2_dispatch_count = Column(Integer, nullable=False, server_default="0")
    unallocated_packages = Column(String(2000), nullable=True)  # JSON 字符串，存储未分配包裹编码列表
    algorithm_type = Column(String(32), nullable=False, server_default="traditional")
    version = Column(Integer, nullable=False, server_default="1")
    parent_id = Column(Integer, ForeignKey("dispatch_batches.id"), nullable=True)
    replan_reason = Column(String(500), nullable=True)
    is_replan = Column(Boolean, nullable=False, server_default="0")  # False
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # 自关联：重规划版本链
    parent = relationship("DispatchBatch", remote_side=[id], backref="children")

    # 关联：一个批次包含多个节点调度明细
    dispatches = relationship("NodeDispatch", back_populates="batch")
