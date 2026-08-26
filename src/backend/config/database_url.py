"""数据库 URL 与 SQLAlchemy 引擎配置的单一解析入口。"""

from pathlib import Path

from sqlalchemy.engine import URL, make_url


def resolve_database_url(configured_url: str) -> str:
    """校验并规范化配置的数据库 URL，供运行时和 Alembic 共用。"""
    value = configured_url.strip()
    if not value:
        raise ValueError("DATABASE_URL 不能为空")
    return make_url(value).render_as_string(hide_password=False)


def sqlite_file_path(database_url: str) -> Path | None:
    """解析 SQLite 文件路径；内存库和非 SQLite URL 返回 None。"""
    url = make_url(database_url)
    if not url.drivername.startswith("sqlite") or not url.database:
        return None
    if url.database == ":memory:" or url.query.get("mode") == "memory":
        return None
    return Path(url.database)


def ensure_sqlite_parent_dir(database_url: str) -> None:
    """SQLite 不会自动创建父目录，创建引擎或迁移前补齐。"""
    path = sqlite_file_path(database_url)
    if path is None:
        return
    parent = path.parent
    if parent and str(parent) != ".":
        parent.mkdir(parents=True, exist_ok=True)


def engine_connect_args(database_url: str) -> dict[str, object]:
    """只为 SQLite 返回方言专属连接参数。"""
    url = make_url(database_url)
    if url.drivername.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def redact_database_url(database_url: str) -> str:
    """生成可安全写入日志的 URL，隐藏口令。"""
    url: URL = make_url(database_url)
    return url.render_as_string(hide_password=True)


__all__ = [
    "engine_connect_args",
    "ensure_sqlite_parent_dir",
    "redact_database_url",
    "resolve_database_url",
    "sqlite_file_path",
]
