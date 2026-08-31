"""
初始化log_events表脚本
log_events表用于存储系统日志事件（如用户登出）
此脚本可用于清空log_events表（用于测试）
"""
from sqlalchemy import create_engine, text
from config.database import settings
from config.database_url import engine_create_kwargs, ensure_sqlite_parent_dir, resolve_database_url


def clear_log_events():
    """清空log_events表（用于测试）"""
    database_url = resolve_database_url(settings.DATABASE_URL)
    ensure_sqlite_parent_dir(database_url)
    engine = create_engine(database_url, **engine_create_kwargs(database_url))
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM log_events"))
        conn.commit()
        print("已清空log_events表")


if __name__ == "__main__":
    clear_log_events()
