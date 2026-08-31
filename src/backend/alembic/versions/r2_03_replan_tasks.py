"""Add the R2-03 replan task state skeleton.

Revision ID: r2_03_replan_tasks
Revises: r2_02b_code_range_allocation
Create Date: 2026-08-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "r2_03_replan_tasks"
down_revision: Union[str, Sequence[str], None] = "r2_02b_code_range_allocation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "replan_tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=16), server_default="PENDING", nullable=False),
        sa.Column("current_step", sa.String(length=16), server_default="F007", nullable=False),
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("manual_required", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED')",
            name="ck_replan_tasks_status",
        ),
        sa.CheckConstraint(
            "current_step IN ('F007', 'F021', 'F005', 'F006', 'NOTIFICATION', 'COMPLETED')",
            name="ck_replan_tasks_current_step",
        ),
        sa.CheckConstraint("retry_count >= 0", name="ck_replan_tasks_retry_count"),
        sa.CheckConstraint("version >= 1", name="ck_replan_tasks_version"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_replan_tasks_idempotency_key",
        "replan_tasks",
        ["idempotency_key"],
        unique=True,
    )
    op.create_index(
        "ix_replan_tasks_status_step",
        "replan_tasks",
        ["status", "current_step"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("replan_tasks")
