from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.database_url import (
    engine_connect_args,
    ensure_sqlite_parent_dir,
    resolve_database_url,
    sqlite_file_path,
)
from config.settings import settings  # noqa: F401  # 向后兼容：其他模块通过 from config.database import settings 使用
from models.base import Base


DATABASE_URL = resolve_database_url(settings.DATABASE_URL)

# 创建 SQLAlchemy 引擎；方言专属参数由统一解析器提供。
ensure_sqlite_parent_dir(DATABASE_URL)
engine = create_engine(
    DATABASE_URL,
    connect_args=engine_connect_args(DATABASE_URL),
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """数据库会话依赖函数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """仅供隔离测试按 ORM metadata 建表；部署和应用启动必须使用 Alembic。"""
    ensure_sqlite_parent_dir(str(engine.url))
    from models.registry import import_all_models

    import_all_models()
    Base.metadata.create_all(bind=engine)

    if settings.JWT_SECRET == "default-secret-key-change-in-env":
        import warnings
        warnings.warn(
            "⚠️  JWT_SECRET 仍为默认值 'default-secret-key-change-in-env'，"
            "请在生产部署前通过 .env 文件设置 JWT_SECRET 为随机字符串。",
            RuntimeWarning,
        )
