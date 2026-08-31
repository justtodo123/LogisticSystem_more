"""Add leased execution claims to R2-03 replan tasks.

Revision ID: r2_03_replan_task_claims
Revises: r2_03_outbox_claims
Create Date: 2026-08-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "r2_03_replan_task_claims"
down_revision: Union[str, Sequence[str], None] = "r2_03_outbox_claims"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("replan_tasks") as batch_op:
        batch_op.add_column(sa.Column("claim_token", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("claimed_by", sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column("claimed_step", sa.String(length=16), nullable=True))
        batch_op.add_column(sa.Column("claimed_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("lease_until", sa.DateTime(), nullable=True))
        batch_op.create_index(
            "ix_replan_tasks_status_lease_until",
            ["status", "lease_until"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("replan_tasks") as batch_op:
        batch_op.drop_index("ix_replan_tasks_status_lease_until")
        batch_op.drop_column("lease_until")
        batch_op.drop_column("claimed_at")
        batch_op.drop_column("claimed_step")
        batch_op.drop_column("claimed_by")
        batch_op.drop_column("claim_token")
