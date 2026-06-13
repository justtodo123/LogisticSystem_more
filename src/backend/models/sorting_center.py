from sqlalchemy import Column, Integer, ForeignKey, SmallInteger, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class SortingCenter(Base):
    __tablename__ = "sorting_centers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), unique=True, nullable=False)
    level = Column(SmallInteger, nullable=False, server_default="0")  # 0=0级, 1=1级
    capacity = Column(Integer, nullable=True)  # 0级可空
    max_storage_time = Column(Integer, nullable=True)  # 0级可空
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # 关系
    node = relationship("Node", back_populates="sorting_center")
