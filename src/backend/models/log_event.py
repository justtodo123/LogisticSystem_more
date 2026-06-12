from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from .base import Base


class LogEvent(Base):
    __tablename__ = "log_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_name = Column(String(64), nullable=False)  # login, logout, etc.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(32), nullable=False)  # dispatcher / manager
    event_data = Column(JSON, nullable=True)  # 事件附加数据
    created_at = Column(DateTime, nullable=False, server_default=func.now())
