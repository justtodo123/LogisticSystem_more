import pytest

from core.error_codes import (
    CODE_CODE_ALLOCATION_CONFLICT,
    CODE_CODE_RANGE_EXHAUSTED,
    CODE_IDEMPOTENCY_IN_PROGRESS,
    CODE_IDEMPOTENCY_PAYLOAD_MISMATCH,
    CODE_STATE_CONFLICT,
    ERROR_REGISTRY,
    get_default_error_definition,
    get_error_definition,
)


def test_registry_codes_are_unique_and_valid():
    assert len(ERROR_REGISTRY) == len(set(ERROR_REGISTRY))
    for code, definition in ERROR_REGISTRY.items():
        assert definition.code == code
        assert 400 <= definition.http_status <= 599
        assert definition.message
        assert definition.owner


@pytest.mark.parametrize(
    ("code", "owner"),
    [
        (CODE_STATE_CONFLICT, "R2-01"),
        (CODE_IDEMPOTENCY_IN_PROGRESS, "R2-02"),
        (CODE_IDEMPOTENCY_PAYLOAD_MISMATCH, "R2-02"),
        (CODE_CODE_RANGE_EXHAUSTED, "R2-02"),
        (CODE_CODE_ALLOCATION_CONFLICT, "R2-02"),
    ],
)
def test_frozen_conflict_codes_are_registered(code, owner):
    definition = get_error_definition(code)
    assert definition.http_status == 409
    assert definition.owner == owner
    assert definition.callers


def test_unknown_code_fails_closed():
    with pytest.raises(ValueError, match="未登记"):
        get_error_definition(99999)


def test_unknown_http_status_uses_internal_error():
    assert get_default_error_definition(599).http_status == 500
