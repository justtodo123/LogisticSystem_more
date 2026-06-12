from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_code = Column(String(64), unique=True, nullable=False, index=True)
    destination_node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    time_window = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False, server_default="pending")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # 关系
    destination_node = relationship("Node")
    goods = relationship("Goods", back_populates="order")
