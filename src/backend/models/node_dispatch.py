from sqlalchemy import Column, Integer, String, JSON, DECIMAL, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class NodeDispatch(Base):
    """F005 节点调度明细表"""
    __tablename__ = "node_dispatches"
    __table_args__ = (
        Index("ix_node_dispatches_batch_phase", "dispatch_batch_id", "level_phase"),
        Index("ix_node_dispatches_vehicle_id", "vehicle_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    dispatch_code = Column(String(64), unique=True, nullable=False, index=True)
    dispatch_batch_id = Column(Integer, ForeignKey("dispatch_batches.id"), nullable=False)
    level_phase = Column(Integer, nullable=False)  # 0: L0→L1, 1: L1→L2
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    tasks = Column(JSON, nullable=False)
    total_distance = Column(DECIMAL(12, 3), nullable=False)
    total_time = Column(DECIMAL(12, 3), nullable=False)
    algorithm_type = Column(String(32), nullable=False, server_default="traditional")
    version = Column(Integer, nullable=False, server_default="1")
    parent_id = Column(Integer, ForeignKey("node_dispatches.id"), nullable=True)
    replan_reason = Column(String(500), nullable=True)
    is_replan = Column(Boolean, nullable=False, server_default="0")  # False
    assigned_at = Column(DateTime, nullable=False, server_default=func.now())
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    # T2-4 人工干预调度：撤销快照（记录干预前的 vehicle_id/driver_id/原因，支持撤销恢复）
    override_snapshot = Column(JSON, nullable=True)

    # 自关联：重规划版本链
    parent = relationship("NodeDispatch", remote_side=[id], backref="children")

    # 关联
    batch = relationship("DispatchBatch", back_populates="dispatches")
    vehicle = relationship("Vehicle", back_populates="dispatches")
    driver = relationship("Driver", back_populates="dispatches")
    packages = relationship("Package", back_populates="dispatch")
    routes = relationship("Route", back_populates="dispatch")
