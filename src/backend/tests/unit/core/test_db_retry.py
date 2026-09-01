from sqlalchemy.exc import OperationalError

from core.db_retry import is_transient_pg, pgcode_of, retry_transient_pg
from core.error_codes import CODE_DATABASE_ERROR
from core.errors import DomainError


def _error(pgcode: str) -> OperationalError:
    orig = type("Orig", (), {"pgcode": pgcode})()
    return OperationalError("SELECT 1", {}, orig)


def test_only_deadlock_and_serialization_are_retryable():
    assert is_transient_pg(_error("40P01")) is True
    assert is_transient_pg(_error("40001")) is True
    assert is_transient_pg(_error("08006")) is False
    assert is_transient_pg(RuntimeError("nope")) is False
    assert pgcode_of(_error("40P01")) == "40P01"


def test_retry_then_succeed():
    calls = {"n": 0}

    def operation():
        calls["n"] += 1
        if calls["n"] < 3:
            raise _error("40001")
        return "ok"

    assert retry_transient_pg(operation, attempts=3, backoff_seconds=0) == "ok"
    assert calls["n"] == 3


def test_non_transient_operational_error_is_not_retried():
    calls = {"n": 0}

    def operation():
        calls["n"] += 1
        raise _error("08006")

    try:
        retry_transient_pg(operation, attempts=3, backoff_seconds=0)
        raise AssertionError("should have raised")
    except OperationalError as exc:
        assert pgcode_of(exc) == "08006"
    assert calls["n"] == 1


def test_retries_exhausted_raise_stable_database_error():
    def operation():
        raise _error("40P01")

    try:
        retry_transient_pg(operation, attempts=2, backoff_seconds=0)
        raise AssertionError("should have raised")
    except DomainError as exc:
        assert exc.code == CODE_DATABASE_ERROR
