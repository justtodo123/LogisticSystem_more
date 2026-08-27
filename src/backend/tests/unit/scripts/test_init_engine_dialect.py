"""Init scripts must not pass SQLite connect_args to other dialects."""

import pytest

from scripts.init_log_events import clear_log_events
from scripts.init_users import init_users


class _StopBeforeDb(RuntimeError):
    pass


def _capture_engine(monkeypatch, module, url: str) -> dict:
    captured: dict = {}

    def fake_create_engine(engine_url, *args, **kwargs):
        captured["url"] = engine_url
        captured["connect_args"] = kwargs.get("connect_args")
        raise _StopBeforeDb("stop-before-db")

    monkeypatch.setattr(module, "create_engine", fake_create_engine)
    monkeypatch.setattr(module.settings, "DATABASE_URL", url)
    return captured


def test_init_users_postgres_connect_args_empty(monkeypatch):
    import scripts.init_users as module

    captured = _capture_engine(monkeypatch, module, "postgresql://user:secret@localhost/app")
    with pytest.raises(_StopBeforeDb, match="stop-before-db"):
        init_users()
    assert captured["connect_args"] == {}


def test_init_users_sqlite_keeps_check_same_thread(monkeypatch):
    import scripts.init_users as module

    captured = _capture_engine(monkeypatch, module, "sqlite:///:memory:")
    with pytest.raises(_StopBeforeDb, match="stop-before-db"):
        init_users()
    assert captured["connect_args"] == {"check_same_thread": False}


def test_init_log_events_postgres_connect_args_empty(monkeypatch):
    import scripts.init_log_events as module

    captured = _capture_engine(monkeypatch, module, "postgresql://user:secret@localhost/app")
    with pytest.raises(_StopBeforeDb, match="stop-before-db"):
        clear_log_events()
    assert captured["connect_args"] == {}


def test_init_log_events_sqlite_keeps_check_same_thread(monkeypatch):
    import scripts.init_log_events as module

    captured = _capture_engine(monkeypatch, module, "sqlite:///:memory:")
    with pytest.raises(_StopBeforeDb, match="stop-before-db"):
        clear_log_events()
    assert captured["connect_args"] == {"check_same_thread": False}
