from sqlalchemy import Column, Integer, ForeignKey, DECIMAL, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class StorageCenter(Base):
    __tablename__ = "storage_centers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), unique=True, nullable=False)
    capacity = Column(DECIMAL(12, 2), nullable=False)
    inventory = Column(Integer, nullable=False, server_default="0")  # NOT NULL DEFAULT 0
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # 关系
    node = relationship("Node", back_populates="storage_center")
