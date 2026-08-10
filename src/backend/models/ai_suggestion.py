"""
AI 建议确认闸门模型（T6-2）

记录 AI 产生的调度建议及其确认/拒绝状态：
- level: info（仅展示）/ suggestion（需人工确认）/ action（自动执行）
- status: pending → confirmed / rejected
- confirm 时通过 applied_schedule_code 关联实际生效的调度方案
"""
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime
from sqlalchemy.sql import func
from .base import Base


class AiSuggestion(Base):
    __tablename__ = "ai_suggestions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    suggestion_code = Column(String(64), unique=True, nullable=False, index=True)
    level = Column(String(16), nullable=False, server_default="info")   # info / suggestion / action
    source = Column(String(32), nullable=False)                          # parse / explain / review / analyze
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False, default="")
    payload = Column(JSON, nullable=True)                                # 确认后要执行的参数（如算法参数）
    related_schedule_code = Column(String(64), nullable=True)            # 关联的 draft 调度方案
    status = Column(String(16), nullable=False, server_default="pending")  # pending / confirmed / rejected
    applied_schedule_code = Column(String(64), nullable=True)            # 确认后实际生效的调度方案
    created_by_user_id = Column(Integer, nullable=False)
    created_by_role = Column(String(32), nullable=False)
    decided_at = Column(DateTime, nullable=True)
    decision_note = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
