from sqlalchemy import Column, Integer, ForeignKey, String, DECIMAL, JSON, DateTime
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
