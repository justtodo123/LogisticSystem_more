"""Add atomic claim leases to the R2-03 outbox.

Revision ID: r2_03_outbox_claims
Revises: r2_03_replan_task_refs
Create Date: 2026-08-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "r2_03_outbox_claims"
down_revision: Union[str, Sequence[str], None] = "r2_03_replan_task_refs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("outbox_events") as batch_op:
        batch_op.drop_constraint("ck_outbox_events_status", type_="check")
        batch_op.add_column(sa.Column("claim_token", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("claimed_by", sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column("claimed_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("lease_until", sa.DateTime(), nullable=True))
        batch_op.create_check_constraint(
            "ck_outbox_events_status",
            "status IN ('pending', 'retry', 'processing', 'delivered', 'dead-letter')",
        )
        batch_op.create_index(
            "ix_outbox_events_status_lease_until",
            ["status", "lease_until"],
            unique=False,
        )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE outbox_events SET status = 'retry', claim_token = NULL, "
            "claimed_by = NULL, claimed_at = NULL, lease_until = NULL "
            "WHERE status = 'processing'"
        )
    )
    with op.batch_alter_table("outbox_events") as batch_op:
        batch_op.drop_index("ix_outbox_events_status_lease_until")
        batch_op.drop_constraint("ck_outbox_events_status", type_="check")
        batch_op.drop_column("lease_until")
        batch_op.drop_column("claimed_at")
        batch_op.drop_column("claimed_by")
        batch_op.drop_column("claim_token")
        batch_op.create_check_constraint(
            "ck_outbox_events_status",
            "status IN ('pending', 'retry', 'delivered', 'dead-letter')",
        )
