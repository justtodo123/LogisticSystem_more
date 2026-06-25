from sqlalchemy import Column, Integer, String, DECIMAL, JSON, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class GlobalSchedule(Base):
    """F007 全局调度方案表"""
    __tablename__ = "global_schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    schedule_code = Column(String(64), unique=True, nullable=False, index=True)
    order_codes = Column(JSON, nullable=False)          # ["O001", "O002"]
    goods_schedules = Column(JSON, nullable=False)       # [{"goods_code":"G001","order_code":"O001","path":["SC001","SO001","SO027"]}]
    total_distance = Column(DECIMAL(12, 3), nullable=False)   # 公里
    total_time = Column(DECIMAL(12, 3), nullable=False)       # 小时
    total_goods = Column(Integer, nullable=False)
    score = Column(DECIMAL(12, 4), nullable=False)            # 越小越好
    algorithm_type = Column(String(32), nullable=False, server_default="traditional")
    version = Column(Integer, nullable=False, server_default="1")
    parent_id = Column(Integer, ForeignKey("global_schedules.id"), nullable=True)
    replan_reason = Column(String(500), nullable=True)
    is_replan = Column(Boolean, nullable=False, server_default="0")  # False
    status = Column(String(20), nullable=False, server_default="active")
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # 自关联：重规划版本链
    parent = relationship("GlobalSchedule", remote_side=[id], backref="children")
    # 关联 packages
    packages = relationship("Package", back_populates="global_schedule")
