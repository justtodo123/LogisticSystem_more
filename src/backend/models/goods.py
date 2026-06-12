from sqlalchemy import Column, Integer, ForeignKey, String, DECIMAL, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class Goods(Base):
    __tablename__ = "goods"

    id = Column(Integer, primary_key=True, autoincrement=True)
    goods_code = Column(String(64), unique=True, nullable=False, index=True)
    goods_name = Column(String(128), nullable=False)
    goods_type = Column(String(64), nullable=False)
    weight = Column(DECIMAL(10, 3), nullable=False)
    volume = Column(DECIMAL(10, 3), nullable=False)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    status = Column(String(32), nullable=False, server_default="pending_pack")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # 关系
    node = relationship("Node")
    order = relationship("Order", back_populates="goods")
