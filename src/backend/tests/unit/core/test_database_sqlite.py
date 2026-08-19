import shutil
from pathlib import Path

from config.database import ensure_sqlite_parent_dir, sqlite_file_path

_TMP_DIR = Path(__file__).resolve().parent / "_tmp_sqlite_dir"


def test_sqlite_file_path_skips_memory_urls():
    assert sqlite_file_path("sqlite:///:memory:") is None
    assert sqlite_file_path("sqlite:///:memory:?cache=shared") is None
    assert sqlite_file_path("postgresql://localhost/db") is None


def test_ensure_sqlite_parent_dir_creates_missing_folder():
    db_path = _TMP_DIR / "nested" / "app.db"
    if _TMP_DIR.exists():
        shutil.rmtree(_TMP_DIR)
    try:
        ensure_sqlite_parent_dir("sqlite:///" + db_path.as_posix())
        assert db_path.parent.is_dir()
        assert not db_path.exists()
    finally:
        shutil.rmtree(_TMP_DIR, ignore_errors=True)


def test_ensure_sqlite_parent_dir_skips_memory():
    if _TMP_DIR.exists():
        shutil.rmtree(_TMP_DIR)
    _TMP_DIR.mkdir(parents=True)
    try:
        ensure_sqlite_parent_dir("sqlite:///:memory:")
        assert list(_TMP_DIR.iterdir()) == []
    finally:
        shutil.rmtree(_TMP_DIR, ignore_errors=True)
