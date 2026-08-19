"""时效要求自由文本最小约束（plan 04 方案 A）。"""
import pytest

from core.validators import (
    TIME_WINDOW_MAX_LEN,
    normalize_time_window_requirement,
    validate_time_window,
)


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("全天", "全天"),
        ("  全天  ", "全天"),
        ("2026-06-15 全天", "2026-06-15 全天"),
        ("2026-06-20 9:00-18:00", "2026-06-20 9:00-18:00"),
        ("9:00-18:00", "9:00-18:00"),
        ("09:00-12:00", "09:00-12:00"),
        ("08:00-18:00", "08:00-18:00"),
    ],
)
def test_accepted_display_samples(raw, expected):
    value, error = normalize_time_window_requirement(raw)
    assert error is None
    assert value == expected
    assert validate_time_window(raw) == (True, None)


@pytest.mark.parametrize(
    "raw",
    [None, "", "   ", "a" * (TIME_WINDOW_MAX_LEN + 1), "全天\n加行"],
)
def test_rejected_min_constraints(raw):
    value, error = normalize_time_window_requirement(raw)
    assert value is None
    assert error
    if raw is not None:
        ok, message = validate_time_window(raw)
        assert ok is False
        assert message
