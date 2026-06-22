from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class ExceptionEvent(Base):
    """异常事件表"""
    __tablename__ = "exception_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_code = Column(String(64), unique=True, nullable=False, index=True)
    exception_type = Column(String(32), nullable=False)  # road, package, node
    exception_subtype = Column(String(64), nullable=True)  # congestion / damage / capacity_limit
    target_type = Column(String(32), nullable=True)  # node / package / route
    target_code = Column(String(64), nullable=True)  # 关联对象业务编号
    severity = Column(String(32), nullable=False)  # low, medium, high
    recommended_action = Column(String(32), nullable=False)  # reroute, redispatch
    trigger_node_id = Column(Integer, ForeignKey("nodes.id"), nullable=True)
    related_route_id = Column(Integer, ForeignKey("routes.id"), nullable=True)
    related_schedule_code = Column(String(64), nullable=True)  # 关联调度方案
    replan_batch_code = Column(String(64), nullable=True)  # 触发后新批次编号
    description = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, server_default="open")  # open, resolved
    resolution_note = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # 关联
    trigger_node = relationship("Node", back_populates="exception_events")
    related_route = relationship("Route", back_populates="exception_events")
