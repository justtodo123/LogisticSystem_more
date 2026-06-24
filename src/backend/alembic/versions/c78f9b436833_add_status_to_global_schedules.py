"""Add status field to global_schedules

Revision ID: c78f9b436833
Revises: 17b1974d0918
Create Date: 2026-06-24 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c78f9b436833'
down_revision: Union[str, Sequence[str], None] = '17b1974d0918'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. 新增 status 字段，默认 'active'（兼容已有数据）
    op.add_column(
        'global_schedules',
        sa.Column(
            'status',
            sa.String(length=20),
            nullable=False,
            server_default='active',
        ),
    )
    # 2. 创建索引（按状态查询优化）
    op.create_index(
        'idx_global_schedules_status',
        'global_schedules',
        ['status'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_global_schedules_status', table_name='global_schedules')
    op.drop_column('global_schedules', 'status')
