from sqlalchemy import CheckConstraint, Column, Index, Integer, String
from .base import Base


class CodeRange(Base):
    """业务编号号段；按 resource + prefix 条件更新抢号。"""

    __tablename__ = "code_ranges"
    __table_args__ = (
        Index("uq_code_ranges_resource_prefix", "resource", "prefix", unique=True),
        CheckConstraint("next_value >= 1", name="ck_code_ranges_next_value"),
        CheckConstraint("width >= 1 AND width <= 8", name="ck_code_ranges_width"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    resource = Column(String(32), nullable=False)
    prefix = Column(String(32), nullable=False)
    next_value = Column(Integer, nullable=False)
    width = Column(Integer, nullable=False)