"""
初始化种子账号脚本
创建dispatcher和manager账号，密码bcrypt哈希存储
"""
import sys
from pathlib import Path

# 添加项目根目录到sys.path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.database import Base, settings
from models.user import User
from services.auth_service import get_password_hash


def init_users():
    """初始化种子账号"""
    # 创建数据库引擎和会话
    engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 检查dispatcher账号是否存在
        dispatcher = db.query(User).filter(User.username == "dispatcher").first()
        if not dispatcher:
            dispatcher = User(
                username="dispatcher",
                password_hash=get_password_hash("123456"),
                role="dispatcher",
                display_name="调度员",
                is_active=True,
            )
            db.add(dispatcher)
            print("创建dispatcher账号")

        # 检查manager账号是否存在
        manager = db.query(User).filter(User.username == "manager").first()
        if not manager:
            manager = User(
                username="manager",
                password_hash=get_password_hash("123456"),
                role="manager",
                display_name="物流管理者",
                is_active=True,
            )
            db.add(manager)
            print("创建manager账号")

        db.commit()
        print("种子账号初始化完成")

    finally:
        db.close()


if __name__ == "__main__":
    init_users()
