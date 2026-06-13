from sqlalchemy import Column, Integer, BigInteger, ForeignKey, String, DECIMAL, JSON, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class Package(Base):
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    package_code = Column(String(64), unique=True, nullable=False, index=True)
    weight = Column(DECIMAL(10, 3), nullable=False)
    volume = Column(DECIMAL(10, 3), nullable=False)
    status = Column(String(32), nullable=False, server_default="pending_pack")
    from_node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    to_node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    from_longitude = Column(DECIMAL(10, 6), nullable=True)
    from_latitude = Column(DECIMAL(10, 6), nullable=True)
    to_longitude = Column(DECIMAL(10, 6), nullable=True)
    to_latitude = Column(DECIMAL(10, 6), nullable=True)
    goods_items = Column(JSON, nullable=False)  # [{"goods_code": "G001", "order_code": "O001"}]
    schedule_id = Column(Integer, ForeignKey("global_schedules.id"), nullable=True)  # 阶段3新增
    dispatch_id = Column(Integer, ForeignKey("node_dispatches.id"), nullable=True)  # 阶段4添加
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # 关系
    from_node = relationship("Node", foreign_keys=[from_node_id], back_populates="packages_from")
    to_node = relationship("Node", foreign_keys=[to_node_id], back_populates="packages_to")
    global_schedule = relationship("GlobalSchedule", back_populates="packages")
    dispatch = relationship("NodeDispatch", back_populates="packages")  # 阶段4已实现
