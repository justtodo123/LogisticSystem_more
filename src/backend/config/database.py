from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import declarative_base, sessionmaker

from config.settings import settings  # noqa: F401  # 向后兼容：其他模块通过 from config.database import settings 使用

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
        DispatchBatch, NodeDispatch, Route, ExceptionEvent,
        IdempotencyRecord
    )
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    # ── Phase 1 数据库迁移（T1-1/T1-2/T1-3 新增字段）──
    _run_phase1_migrations(engine)
    
    # 安全检查：JWT_SECRET 使用默认值时发出警告（仅限演示环境）
    if settings.JWT_SECRET == "default-secret-key-change-in-env":
        import warnings
        warnings.warn(
            "⚠️  JWT_SECRET 仍为默认值 'default-secret-key-change-in-env'，"
            "请在生产部署前通过 .env 文件设置 JWT_SECRET 为随机字符串。",
            RuntimeWarning,
        )


def _run_phase1_migrations(engine):
    """Phase 1 数据库迁移：为已有表添加新列（幂等操作，列已存在则跳过）"""
    inspector = inspect(engine)
    
    with engine.connect() as conn:
        # T1-1: orders 表 status 默认值更新（仅新纪录生效，旧数据需手动处理）
        # T1-2: vehicles 表新增字段
        if "vehicles" in inspector.get_table_names():
            veh_cols = [c["name"] for c in inspector.get_columns("vehicles")]
            veh_migrations = [
                ("plate_number", "VARCHAR(20)"),
                ("time_window_start", "TIME"),
                ("time_window_end", "TIME"),
                ("route_limit", "INTEGER DEFAULT 5"),
                ("cost_per_km", "FLOAT DEFAULT 5.0"),
                ("load_rate_max", "FLOAT DEFAULT 0.9"),
            ]
            for col_name, col_def in veh_migrations:
                if col_name not in veh_cols:
                    conn.execute(text(f"ALTER TABLE vehicles ADD COLUMN {col_name} {col_def}"))
                    conn.commit()
        
        # T1-2: drivers 表新增字段
        if "drivers" in inspector.get_table_names():
            drv_cols = [c["name"] for c in inspector.get_columns("drivers")]
            drv_migrations = [
                ("shift_start", "TIME"),
                ("shift_end", "TIME"),
                ("max_drive_hours", "FLOAT DEFAULT 8.0"),
                ("max_continuous_hours", "FLOAT DEFAULT 4.0"),
            ]
            for col_name, col_def in drv_migrations:
                if col_name not in drv_cols:
                    conn.execute(text(f"ALTER TABLE drivers ADD COLUMN {col_name} {col_def}"))
                    conn.commit()
        
        # T1-3: log_events 表新增字段（T0-3 遗漏）
        if "log_events" in inspector.get_table_names():
            log_cols = [c["name"] for c in inspector.get_columns("log_events")]
            log_migrations = [
                ("ip_address", "VARCHAR(45)"),
                ("user_agent", "VARCHAR(512)"),
            ]
            for col_name, col_def in log_migrations:
                if col_name not in log_cols:
                    conn.execute(text(f"ALTER TABLE log_events ADD COLUMN {col_name} {col_def}"))
                    conn.commit()
        
        # T0-4: idempotency_records 表由 create_all 创建，无需手动迁移
