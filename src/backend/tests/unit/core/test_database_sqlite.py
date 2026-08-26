from pathlib import Path

import pytest
from sqlalchemy import create_engine

from config.database_url import (
    engine_connect_args,
    ensure_sqlite_parent_dir,
    redact_database_url,
    resolve_database_url,
    sqlite_file_path,
)


def test_sqlite_file_path_skips_memory_urls():
    assert sqlite_file_path("sqlite:///:memory:") is None
    assert sqlite_file_path("sqlite:///:memory:?cache=shared") is None
    assert sqlite_file_path("postgresql://localhost/db") is None


def test_ensure_sqlite_parent_dir_creates_missing_folder(tmp_path: Path):
    db_path = tmp_path / "nested" / "app.db"

    ensure_sqlite_parent_dir("sqlite:///" + db_path.as_posix())

    assert db_path.parent.is_dir()
    assert not db_path.exists()


def test_ensure_sqlite_parent_dir_skips_memory(tmp_path: Path):
    ensure_sqlite_parent_dir("sqlite:///:memory:")

    assert list(tmp_path.iterdir()) == []


def test_engine_connect_args_are_sqlite_only():
    assert engine_connect_args("sqlite:///app.db") == {"check_same_thread": False}
    assert engine_connect_args("postgresql://user:secret@db.example/app") == {}


def test_database_url_requires_non_empty_value():
    with pytest.raises(ValueError, match="DATABASE_URL"):
        resolve_database_url("  ")


def test_database_url_redaction_hides_password():
    redacted = redact_database_url("postgresql://user:p%40ss@db.example/app")

    assert "p%40ss" not in redacted
    assert "***" in redacted
    assert redacted.endswith("@db.example/app")


def test_sqlite_engine_accepts_resolved_connect_args(tmp_path: Path):
    database_url = resolve_database_url(f"sqlite:///{(tmp_path / 'engine.db').as_posix()}")
    engine = create_engine(database_url, connect_args=engine_connect_args(database_url))

    with engine.connect() as connection:
        assert connection.dialect.name == "sqlite"
