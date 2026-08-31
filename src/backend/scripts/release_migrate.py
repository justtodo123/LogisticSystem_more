"""发布前数据库迁移门禁：只自动创建 fresh 库，拒绝原地升级旧 SQLite。"""
from __future__ import annotations

from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from alembic import command
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine

from config.database_url import engine_create_kwargs, resolve_database_url, sqlite_file_path
from config.settings import settings
from utils.schema_management import (
    SchemaKind,
    alembic_config,
    classify_sqlite,
)


def _assert_at_unique_head(config, database_url: str) -> None:
    """Verify a non-SQLite database reached the unique Alembic head."""
    head = ScriptDirectory.from_config(config).get_current_head()
    if head is None:
        raise RuntimeError("Alembic 迁移图没有唯一 head")
    engine = create_engine(database_url, **engine_create_kwargs(database_url))
    try:
        with engine.connect() as connection:
            current = MigrationContext.configure(connection).get_current_revision()
    finally:
        engine.dispose()
    if current != head:
        raise RuntimeError(
            "PostgreSQL 未到达唯一 head: "
            f"current={current or '-'}, head={head}"
        )


def migrate_release_database(database_url: str) -> None:
    """迁移 fresh 数据库；现有数据库必须已安全迁移到当前 head。"""
    resolved_url = resolve_database_url(database_url)
    config = alembic_config(resolved_url)
    sqlite_path = sqlite_file_path(resolved_url)

    if sqlite_path is None:
        command.upgrade(config, "head")
        _assert_at_unique_head(config, resolved_url)
        return

    classification = classify_sqlite(sqlite_path)
    head = ScriptDirectory.from_config(config).get_current_head()
    if head is None:
        raise RuntimeError("Alembic 迁移图没有唯一 head")

    if classification.kind is SchemaKind.FRESH:
        command.upgrade(config, "head")
    elif not (
        classification.kind is SchemaKind.ALEMBIC_MANAGED
        and classification.revision == head
    ):
        raise RuntimeError(
            "现有 SQLite 不允许由发布门禁原地修改："
            f"kind={classification.kind.value}, "
            f"revision={classification.revision or '-'}, "
            f"reason={classification.reason or '-'}。"
            "请先停止写入，使用 migrate_sqlite.py classify 和 "
            "upgrade-copy/adopt-copy 生成已验证副本，再切换 DATABASE_URL。"
        )

    command.check(config)
    result = classify_sqlite(sqlite_path)
    if not (
        result.kind is SchemaKind.ALEMBIC_MANAGED
        and result.revision == head
    ):
        raise RuntimeError("发布后 schema/revision 校验失败")


def main() -> int:
    try:
        migrate_release_database(settings.DATABASE_URL)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print("database migration gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
