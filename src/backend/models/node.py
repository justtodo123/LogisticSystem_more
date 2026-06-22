from sqlalchemy import Column, Integer, String, DECIMAL, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_code = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    location = Column(String(255), nullable=False)
    latitude = Column(DECIMAL(10, 6), nullable=False)
    longitude = Column(DECIMAL(10, 6), nullable=False)
    node_type = Column(String(32), nullable=False)  # storage_center / sorting_center
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # 关系
    storage_center = relationship("StorageCenter", back_populates="node", uselist=False, cascade="all, delete-orphan")
    sorting_center = relationship("SortingCenter", back_populates="node", uselist=False, cascade="all, delete-orphan")
    vehicles_at_node = relationship("Vehicle", foreign_keys="Vehicle.last_arrived_node_id", back_populates="last_arrived_node")
    vehicles = relationship("Vehicle", foreign_keys="Vehicle.node_id", back_populates="node")
    drivers = relationship("Driver", back_populates="node")
    packages_from = relationship("Package", foreign_keys="Package.from_node_id", back_populates="from_node")
    packages_to = relationship("Package", foreign_keys="Package.to_node_id", back_populates="to_node")
