from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from .base import Base


class ExceptionEvent(Base):
    """异常事件表 - 严格按架构文档§5.4.4定义"""
    __tablename__ = "exception_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_code = Column(String(64), unique=True, nullable=False, index=True)
    exception_type = Column(String(32), nullable=False)  # road, package, node
    exception_subtype = Column(String(64), nullable=True)  # congestion / damage / capacity_limit
    target_type = Column(String(32), nullable=True)  # node / package / route
    target_code = Column(String(64), nullable=True)  # 关联对象业务编号
    recommended_action = Column(String(32), nullable=False)  # reroute, redispatch
    related_schedule_code = Column(String(64), nullable=True)  # 关联调度方案
    replan_batch_code = Column(String(64), nullable=True)  # 触发后新批次编号
    description = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, server_default="open")  # open, resolved
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
