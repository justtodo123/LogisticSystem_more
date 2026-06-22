"""add_missing_fields_to_exception_events

Revision ID: phase7_exception_fields
Revises: 17b1974d0918
Create Date: 2026-06-22

添加 exception_events 表缺失字段（阶段7）：
- exception_subtype: 异常子类型
- target_type: 关联对象类型
- target_code: 关联对象业务编号
- related_schedule_code: 关联调度方案
- replan_batch_code: 触发后新批次编号
- resolved_at: 解决时间

同时修改 trigger_node_id 为 nullable=True。
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
    """添加缺失字段到 exception_events 表"""
    # 使用 batch mode 支持 SQLite ALTER TABLE
    with op.batch_alter_table('exception_events') as batch_op:
        batch_op.add_column(sa.Column('exception_subtype', sa.String(64), nullable=True))
        batch_op.add_column(sa.Column('target_type', sa.String(32), nullable=True))
        batch_op.add_column(sa.Column('target_code', sa.String(64), nullable=True))
        batch_op.add_column(sa.Column('related_schedule_code', sa.String(64), nullable=True))
        batch_op.add_column(sa.Column('replan_batch_code', sa.String(64), nullable=True))
        batch_op.add_column(sa.Column('resolved_at', sa.DateTime, nullable=True))
        # 修改 trigger_node_id 为 nullable=True
        batch_op.alter_column('trigger_node_id', nullable=True)


def downgrade() -> None:
    """回滚：移除添加的字段"""
    with op.batch_alter_table('exception_events') as batch_op:
        batch_op.drop_column('resolved_at')
        batch_op.drop_column('replan_batch_code')
        batch_op.drop_column('related_schedule_code')
        batch_op.drop_column('target_code')
        batch_op.drop_column('target_type')
        batch_op.drop_column('exception_subtype')
        # 恢复 trigger_node_id 为 nullable=False（如果表中有 NULL 值会失败）
        batch_op.alter_column('trigger_node_id', nullable=False)
