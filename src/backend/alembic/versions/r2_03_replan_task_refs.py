"""Persist R2-03 replan inputs and produced resource references.

Revision ID: r2_03_replan_task_refs
Revises: r2_03_outbox_events
Create Date: 2026-08-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "r2_03_replan_task_refs"
down_revision: Union[str, Sequence[str], None] = "r2_03_outbox_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_COLUMNS = (
    sa.Column("request_fingerprint", sa.String(length=64), nullable=True),
    sa.Column("operation_type", sa.String(length=16), nullable=True),
    sa.Column("original_resource_id", sa.Integer(), nullable=True),
    sa.Column("original_resource_code", sa.String(length=64), nullable=True),
    sa.Column("new_schedule_id", sa.Integer(), nullable=True),
    sa.Column("new_schedule_code", sa.String(length=64), nullable=True),
    sa.Column("dispatch_batch_id", sa.Integer(), nullable=True),
    sa.Column("dispatch_batch_code", sa.String(length=64), nullable=True),
    sa.Column("new_route_id", sa.Integer(), nullable=True),
    sa.Column("new_route_code", sa.String(length=64), nullable=True),
)


def upgrade() -> None:
    with op.batch_alter_table("replan_tasks") as batch_op:
        for column in _COLUMNS:
            batch_op.add_column(column)


def downgrade() -> None:
    with op.batch_alter_table("replan_tasks") as batch_op:
        for column in reversed(_COLUMNS):
            batch_op.drop_column(column.name)
