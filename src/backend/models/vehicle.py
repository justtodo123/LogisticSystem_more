from sqlalchemy import Column, Integer, ForeignKey, String, DECIMAL, JSON, DateTime, Float, Time
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_code = Column(String(64), unique=True, nullable=False, index=True)
    model = Column(String(64), nullable=False)
    capacity = Column(DECIMAL(10, 3), nullable=False)
    energy_type = Column(String(16), nullable=False)  # fuel / electric
    vehicle_type = Column(String(32), nullable=False, server_default="normal")  # normal / cold_chain (P1)
    capability_tags = Column(JSON, nullable=True)  # e.g. ["cold_chain"] (P1)
    plate_number = Column(String(20), nullable=True)  # 车牌号
    time_window_start = Column(Time, nullable=True)  # 可用时段-开始
    time_window_end = Column(Time, nullable=True)  # 可用时段-结束
    route_limit = Column(Integer, nullable=False, server_default="5")  # 单日最大路径数
    cost_per_km = Column(Float, nullable=False, server_default="5.0")  # 每公里运营成本(元)
    load_rate_max = Column(Float, nullable=False, server_default="0.9")  # 最大装载率(0~1)
    last_arrived_node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    last_arrived_longitude = Column(DECIMAL(10, 6), nullable=True)
    last_arrived_latitude = Column(DECIMAL(10, 6), nullable=True)
    status = Column(String(32), nullable=False, server_default="idle")
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # 关系
    last_arrived_node = relationship("Node", foreign_keys=[last_arrived_node_id], back_populates="vehicles_at_node")
    node = relationship("Node", foreign_keys=[node_id], back_populates="vehicles")
    dispatches = relationship("NodeDispatch", back_populates="vehicle")
    routes = relationship("Route", back_populates="vehicle")
