from sqlalchemy import Column, Integer, String, JSON, DECIMAL, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class Route(Base):
    """F006 路径规划结果表"""
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    route_code = Column(String(64), unique=True, nullable=False, index=True)
    dispatch_id = Column(Integer, ForeignKey("node_dispatches.id"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    route_segments = Column(JSON, nullable=False)
    total_distance = Column(DECIMAL(12, 3), nullable=False)
    total_time = Column(DECIMAL(12, 3), nullable=False)
    total_emission = Column(DECIMAL(12, 4), nullable=False)
    algorithm_type = Column(String(32), nullable=False, server_default="traditional")
    version = Column(Integer, nullable=False, server_default="1")
    parent_id = Column(Integer, ForeignKey("routes.id"), nullable=True)
    replan_reason = Column(String(500), nullable=True)
    is_replan = Column(Boolean, nullable=False, server_default="0")
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # 自关联：重规划版本链
    parent = relationship("Route", remote_side=[id], backref="children")

    # 关联
    dispatch = relationship("NodeDispatch", back_populates="routes")
    vehicle = relationship("Vehicle", back_populates="routes")
