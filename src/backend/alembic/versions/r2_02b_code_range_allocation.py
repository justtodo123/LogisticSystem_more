"""Add the R2-02B business code range table.

Revision ID: r2_02b_code_range_allocation
Revises: r2_02a_idempotency_state
Create Date: 2026-08-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "r2_02b_code_range_allocation"
down_revision: Union[str, Sequence[str], None] = "r2_02a_idempotency_state"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "code_ranges",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("resource", sa.String(length=32), nullable=False),
        sa.Column("prefix", sa.String(length=32), nullable=False),
        sa.Column("next_value", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.CheckConstraint("next_value >= 1", name="ck_code_ranges_next_value"),
        sa.CheckConstraint("width >= 1 AND width <= 8", name="ck_code_ranges_width"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_code_ranges_resource_prefix",
        "code_ranges",
        ["resource", "prefix"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("code_ranges")