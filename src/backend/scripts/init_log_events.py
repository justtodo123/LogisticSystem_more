"""
初始化log_events表脚本
log_events表用于存储系统日志事件（如用户登出）
此脚本可用于清空log_events表（用于测试）
"""
from sqlalchemy import create_engine, text
from config.database import settings


def clear_log_events():
    """清空log_events表（用于测试）"""
    engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM log_events"))
        conn.commit()
        print("已清空log_events表")


if __name__ == "__main__":
    clear_log_events()
