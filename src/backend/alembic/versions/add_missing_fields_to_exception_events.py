"""add_missing_fields_to_exception_events

Revision ID: phase7_exception_fields
Revises: 17b1974d0918
Create Date: 2026-06-22

修复历史 fresh 链：父 revision 未创建 exception_events，本 revision 直接建立
与当前 ORM 一致的完整表。既有无版本/混合旧库必须由 R2-00A adoption
工具识别，禁止在历史 revision 中静默删除 trigger_node_id 数据。
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'phase7_exception_fields'
down_revision: Union[str, None] = '17b1974d0918'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """建立当前字段完整的异常事件表，修复 fresh migration 断链。"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "exception_events" in inspector.get_table_names():
        raise RuntimeError(
            "phase7_exception_fields 仅支持其父链中的 fresh schema；"
            "检测到既有 exception_events，请使用 R2-00A legacy adoption 工具分类处理"
        )

    op.create_table(
        "exception_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_code", sa.String(length=64), nullable=False),
        sa.Column("exception_type", sa.String(length=32), nullable=False),
        sa.Column("exception_subtype", sa.String(length=64), nullable=True),
        sa.Column("target_type", sa.String(length=32), nullable=True),
        sa.Column("target_code", sa.String(length=64), nullable=True),
        sa.Column("recommended_action", sa.String(length=32), nullable=False),
        sa.Column("related_schedule_code", sa.String(length=64), nullable=True),
        sa.Column("replan_batch_code", sa.String(length=64), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="open", nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_exception_events_event_code"),
        "exception_events",
        ["event_code"],
        unique=True,
    )


def downgrade() -> None:
    """移除由本 revision 建立的异常事件表。"""
    op.drop_index(op.f("ix_exception_events_event_code"), table_name="exception_events")
    op.drop_table("exception_events")
