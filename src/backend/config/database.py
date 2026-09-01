import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.database_url import (
    engine_create_kwargs,
    ensure_sqlite_parent_dir,
    resolve_database_url,
)
from config.settings import settings  # noqa: F401  # 向后兼容：其他模块通过 from config.database import settings 使用
from models.base import Base


logger = logging.getLogger(__name__)

DATABASE_URL = resolve_database_url(settings.DATABASE_URL)

# 创建 SQLAlchemy 引擎；方言专属参数由统一解析器提供。
ensure_sqlite_parent_dir(DATABASE_URL)
engine = create_engine(
    DATABASE_URL,
    **engine_create_kwargs(
        DATABASE_URL,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
    ),
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """提供数据库会话；异常路径回滚并保留原异常。"""
    db = SessionLocal()
    try:
        yield db
    except BaseException:
        try:
            db.rollback()
        except Exception as rollback_error:
            logger.error(
                "数据库会话回滚失败: exception=%s",
                type(rollback_error).__name__,
            )
        raise
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
