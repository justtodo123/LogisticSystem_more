from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""
    DATABASE_URL: str = "sqlite:///./data/logistics.db"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


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
