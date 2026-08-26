from unittest.mock import Mock
import logging

import pytest

from config import database


def test_get_db_normal_path_closes_without_rollback(monkeypatch):
    session = Mock()
    monkeypatch.setattr(database, "SessionLocal", Mock(return_value=session))
    dependency = database.get_db()

    assert next(dependency) is session
    with pytest.raises(StopIteration):
        next(dependency)

    session.rollback.assert_not_called()
    session.close.assert_called_once_with()


def test_get_db_rolls_back_reraises_original_and_closes(monkeypatch):
    session = Mock()
    monkeypatch.setattr(database, "SessionLocal", Mock(return_value=session))
    dependency = database.get_db()
    next(dependency)
    original = RuntimeError("handler failed")

    with pytest.raises(RuntimeError) as caught:
        dependency.throw(original)

    assert caught.value is original
    session.rollback.assert_called_once_with()
    session.close.assert_called_once_with()
    assert session.method_calls.index(("rollback", (), {})) < session.method_calls.index(("close", (), {}))


def test_get_db_preserves_original_when_rollback_fails(monkeypatch, caplog):
    caplog.set_level(logging.ERROR, logger="config.database")
    session = Mock()
    session.rollback.side_effect = RuntimeError("rollback secret")
    monkeypatch.setattr(database, "SessionLocal", Mock(return_value=session))
    dependency = database.get_db()
    next(dependency)
    original = ValueError("original handler failure")

    with pytest.raises(ValueError) as caught:
        dependency.throw(original)

    assert caught.value is original
    session.close.assert_called_once_with()
    assert "数据库会话回滚失败" in caplog.text
    assert "rollback secret" not in caplog.text
