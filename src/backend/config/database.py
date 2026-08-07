from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""
    DATABASE_URL: str = "sqlite:///./data/logistics.db"
    JWT_SECRET: str = "default-secret-key-change-in-env"
    JWT_EXPIRE_SECONDS: int = 86400
    
    # DeepSeek 配置
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # 允许.env文件中的额外字段


settings = Settings()

# 创建SQLAlchemy引擎
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite需要此配置
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建Base类用于声明式模型
Base = declarative_base()


def get_db():
    """数据库会话依赖函数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库，创建所有表"""
    # 导入所有模型以确保它们被注册到Base.metadata
    from models import (  # noqa: F401
        User, LogEvent, Node, StorageCenter, SortingCenter,
        Order, Goods, Package, Vehicle, Driver, GlobalSchedule,
        DispatchBatch, NodeDispatch, Route, ExceptionEvent
    )
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    # 安全检查：JWT_SECRET 使用默认值时发出警告（仅限演示环境）
    if settings.JWT_SECRET == "default-secret-key-change-in-env":
        import warnings
        warnings.warn(
            "⚠️  JWT_SECRET 仍为默认值 'default-secret-key-change-in-env'，"
            "请在生产部署前通过 .env 文件设置 JWT_SECRET 为随机字符串。",
            RuntimeWarning,
        )
