"""Add the R2-03 transactional outbox table.

Revision ID: r2_03_outbox_events
Revises: r2_03_replan_tasks
Create Date: 2026-08-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "r2_03_outbox_events"
down_revision: Union[str, Sequence[str], None] = "r2_03_replan_tasks"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "outbox_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("dedup_key", sa.String(length=128), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=16), server_default="pending", nullable=False),
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("available_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('pending', 'retry', 'delivered', 'dead-letter')",
            name="ck_outbox_events_status",
        ),
        sa.CheckConstraint("retry_count >= 0", name="ck_outbox_events_retry_count"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_outbox_events_dedup_key",
        "outbox_events",
        ["dedup_key"],
        unique=True,
    )
    op.create_index(
        "ix_outbox_events_status_available_at",
        "outbox_events",
        ["status", "available_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("outbox_events")
