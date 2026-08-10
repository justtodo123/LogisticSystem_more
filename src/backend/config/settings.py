"""
集中配置模块

按 ENV 环境变量加载对应 .env.{env} 文件：
  - dev  → .env.dev
  - staging → .env.staging
  - prod → .env.prod
未设置 ENV 时回退到 .env（向后兼容）。

所有环境变量通过 pydantic-settings 自动映射为 Settings 实例属性。
"""
import os
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类
    
    按 ENV 环境变量加载对应 .env 文件；
    环境变量 > .env 文件 > 默认值（优先级由高到低）。
    """

    # ── 运行环境 ──
    ENV: str = "dev"

    # ── 数据库 ──
    DATABASE_URL: str = "sqlite:///./data/logistics.db"

    # ── JWT 认证 ──
    JWT_SECRET: str = "default-secret-key-change-in-env"
    JWT_EXPIRE_HOURS: int = 24
    JWT_EXPIRE_SECONDS: int = 86400  # 默认由 HOURS×3600 自动计算

    # ── DeepSeek AI ──
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # ── CORS ──
    CORS_ORIGINS: str = "http://localhost:5173"

    # ── 请求控制 ──
    REQUEST_TIMEOUT_SECONDS: int = 30
    IDEMPOTENCY_TTL_HOURS: int = 24
    DEEPSEEK_TIMEOUT_SECONDS: int = 15

    # ── 消息通知（T3-2）──
    NOTIFICATION_CHANNELS: str = "console"  # 逗号分隔：console,email,wechat_work
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    EMAIL_RECIPIENTS: str = ""  # 逗号分隔的收件人
    WECHAT_WORK_WEBHOOK: str = ""

    # ── Redis 缓存（T4-3）──
    # REDIS_ENABLED=false 或 REDIS_URL 为空时，utils/cache 自动降级到进程内内存缓存（dev 友好）
    REDIS_ENABLED: bool = False
    REDIS_URL: str = ""
    REDIS_CACHE_TTL: int = 300

    @model_validator(mode="after")
    def _sync_jwt_expiry(self) -> "Settings":
        """当未显式设置 JWT_EXPIRE_SECONDS 时，从 JWT_EXPIRE_HOURS 自动计算"""
        if "JWT_EXPIRE_SECONDS" not in self.model_fields_set:
            object.__setattr__(self, "JWT_EXPIRE_SECONDS", self.JWT_EXPIRE_HOURS * 3600)
        return self

    # pydantic v2 配置风格
    model_config = SettingsConfigDict(
        env_file=f".env.{os.getenv('ENV', 'dev')}" if os.path.exists(
            f".env.{os.getenv('ENV', 'dev')}"
        ) else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# 单例 — 其余模块通过 from config.settings import settings 使用
settings = Settings()
