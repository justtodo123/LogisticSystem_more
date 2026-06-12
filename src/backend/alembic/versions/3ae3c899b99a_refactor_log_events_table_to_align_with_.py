"""refactor_log_events_table_to_align_with_architecture

Revision ID: 3ae3c899b99a
Revises: 65b9652fc218
Create Date: 2026-06-12 21:36:35.282595

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ae3c899b99a'
down_revision: Union[str, Sequence[str], None] = '65b9652fc218'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: rebuild log_events with new columns."""
    # SQLite 不支持 ALTER TABLE DROP COLUMN，使用重建策略
    # 1. 创建新表（使用原始 SQL 确保 AUTOINCREMENT）
    op.execute("""
        CREATE TABLE log_events_new (
            id              INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            event_name      VARCHAR(64) NOT NULL,
            user_id         BIGINT NOT NULL,
            role            VARCHAR(32) NOT NULL,
            event_data      JSON,
            created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    # 2. 迁移旧数据（将旧字段映射到新字段）
    op.execute("""
        INSERT INTO log_events_new (id, event_name, user_id, role, event_data, created_at)
        SELECT
            id,
            event_type AS event_name,
            (SELECT id FROM users WHERE username = log_events.username LIMIT 1) AS user_id,
            COALESCE((SELECT role FROM users WHERE username = log_events.username LIMIT 1), 'dispatcher') AS role,
            NULL AS event_data,
            created_at
        FROM log_events
    """)
    # 3. 删除旧表
    op.drop_table('log_events')
    # 4. 重命名新表
    op.rename_table('log_events_new', 'log_events')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema: revert to old log_events columns."""
    op.execute("""
        CREATE TABLE log_events_old (
            id              INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            event_type      VARCHAR(32) NOT NULL,
            username        VARCHAR(64),
            description     TEXT,
            created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("""
        INSERT INTO log_events_old (id, event_type, username, description, created_at)
        SELECT
            id,
            event_name AS event_type,
            (SELECT username FROM users WHERE id = log_events.user_id LIMIT 1) AS username,
            NULL AS description,
            created_at
        FROM log_events
    """)
    op.drop_table('log_events')
    op.rename_table('log_events_old', 'log_events')
    # ### end Alembic commands ###
