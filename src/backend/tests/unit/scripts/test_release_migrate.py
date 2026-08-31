from pathlib import Path
import sqlite3

import pytest
from alembic import command

from scripts.release_migrate import migrate_release_database
from utils.schema_management import alembic_config, file_sha256, sqlite_database_url


HEAD_REVISION = "r2_04b_token_version"


def _version(path: Path) -> str:
    with sqlite3.connect(path) as connection:
        row = connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchone()
    assert row is not None
    return row[0]


def test_release_gate_creates_fresh_database(tmp_path: Path):
    database = tmp_path / "fresh.db"

    migrate_release_database(sqlite_database_url(database))

    assert _version(database) == HEAD_REVISION


def test_release_gate_accepts_current_head(tmp_path: Path):
    database = tmp_path / "head.db"
    database_url = sqlite_database_url(database)
    command.upgrade(alembic_config(database_url), "head")
    before_hash = file_sha256(database)

    migrate_release_database(database_url)

    assert _version(database) == HEAD_REVISION
    assert file_sha256(database) == before_hash


def test_release_gate_rejects_legacy_without_mutation(tmp_path: Path):
    database = tmp_path / "legacy.db"
    database_url = sqlite_database_url(database)
    command.upgrade(alembic_config(database_url), "c78f9b436833")
    before_hash = file_sha256(database)

    with pytest.raises(RuntimeError, match="不允许由发布门禁原地修改"):
        migrate_release_database(database_url)

    assert _version(database) == "c78f9b436833"
    assert file_sha256(database) == before_hash


def test_release_gate_rejects_head_revision_with_schema_drift(
    tmp_path: Path,
):
    database = tmp_path / "drift.db"
    database_url = sqlite_database_url(database)
    command.upgrade(alembic_config(database_url), "head")
    with sqlite3.connect(database) as connection:
        connection.execute("ALTER TABLE users ADD COLUMN manual_note TEXT")
        connection.commit()
    before_hash = file_sha256(database)

    with pytest.raises(RuntimeError, match="不允许由发布门禁原地修改"):
        migrate_release_database(database_url)

    assert _version(database) == HEAD_REVISION
    assert file_sha256(database) == before_hash
