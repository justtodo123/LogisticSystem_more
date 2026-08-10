from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Float, Time
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    driver_code = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(64), nullable=False)
    phone = Column(String(32), nullable=False)
    license_type = Column(String(8), nullable=False)  # C1/C2/B1/B2/A1/A2
    shift = Column(String(64), nullable=False)
    shift_start = Column(Time, nullable=True)  # 排班开始时间
    shift_end = Column(Time, nullable=True)  # 排班结束时间
    max_drive_hours = Column(Float, nullable=False, server_default="8.0")  # 单日最大驾驶时长(小时)
    max_continuous_hours = Column(Float, nullable=False, server_default="4.0")  # 连续驾驶最大时长(小时)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    status = Column(String(32), nullable=False, server_default="idle")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # 关系
    node = relationship("Node", back_populates="drivers")
    dispatches = relationship("NodeDispatch", back_populates="driver")
