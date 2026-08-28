"""Add the R2-02A database idempotency state machine.

Revision ID: r2_02a_idempotency_state
Revises: r2_00a_schema_convergence
Create Date: 2026-08-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "r2_02a_idempotency_state"
down_revision: Union[str, Sequence[str], None] = "r2_00a_schema_convergence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_STATUS_CHECK = "status IN ('PROCESSING', 'SUCCEEDED', 'FAILED', 'EXPIRED')"


def upgrade() -> None:
    """Make legacy cache rows non-replayable, then add protocol constraints."""
    with op.batch_alter_table("idempotency_records") as batch_op:
        batch_op.add_column(
            sa.Column(
                "status",
                sa.String(length=16),
                server_default="EXPIRED",
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("payload_hash", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("claim_token", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("http_status", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("response_body", sa.LargeBinary(), nullable=True))
        batch_op.add_column(
            sa.Column("response_media_type", sa.String(length=255), nullable=True)
        )
        batch_op.add_column(sa.Column("response_headers", sa.JSON(), nullable=True))

    # Existing rows have no trustworthy request fingerprint. Keep their historical
    # payload for downgrade, but never present them as replayable successes.
    op.execute(
        sa.text(
            "UPDATE idempotency_records "
            "SET status = 'EXPIRED', payload_hash = NULL, claim_token = NULL, "
            "http_status = NULL, response_body = NULL, response_media_type = NULL, "
            "response_headers = NULL"
        )
    )

    with op.batch_alter_table("idempotency_records") as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=sa.String(length=16),
            nullable=False,
            server_default=None,
        )
        batch_op.create_check_constraint(
            "ck_idempotency_records_status",
            _STATUS_CHECK,
        )
        batch_op.create_index(
            "ix_idempotency_records_status_expires_at",
            ["status", "expires_at"],
            unique=False,
        )


def downgrade() -> None:
    """Restore the R2-00A table shape without deleting legacy response_data."""
    with op.batch_alter_table("idempotency_records") as batch_op:
        batch_op.drop_index("ix_idempotency_records_status_expires_at")
        batch_op.drop_constraint(
            "ck_idempotency_records_status",
            type_="check",
        )
        batch_op.drop_column("response_headers")
        batch_op.drop_column("response_media_type")
        batch_op.drop_column("response_body")
        batch_op.drop_column("http_status")
        batch_op.drop_column("claim_token")
        batch_op.drop_column("payload_hash")
        batch_op.drop_column("status")
