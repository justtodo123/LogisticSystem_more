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
    severity = Column(String(32), nullable=False)  # low, medium, high
    recommended_action = Column(String(32), nullable=False)  # reroute, redispatch
    trigger_node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    related_route_id = Column(Integer, ForeignKey("routes.id"), nullable=True)
    description = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, server_default="open")  # open, resolved
    resolution_note = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # 关联
    trigger_node = relationship("Node", back_populates="exception_events")
    related_route = relationship("Route", back_populates="exception_events")
