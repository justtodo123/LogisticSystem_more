import pytest

from core.error_codes import CODE_STATE_CONFLICT
from core.errors import DomainError, sanitize_meta


def test_domain_error_uses_registered_contract_and_hides_internal_fields():
    cause = RuntimeError("postgresql://user:secret@db/internal")
    error = DomainError(
        CODE_STATE_CONFLICT,
        meta={"request_id": "req-1", "secret": "hidden"},
        cause=cause,
        log_context={"operation": "confirm"},
    )

    assert error.http_status == 409
    assert error.public_message == "资源状态已变化，当前操作不能继续"
    assert error.meta == {"request_id": "req-1"}
    assert "secret" not in repr(error)
    assert "postgresql" not in repr(error)


def test_domain_error_rejects_unknown_code():
    with pytest.raises(ValueError):
        DomainError(99999)


def test_unsafe_or_overlong_public_message_falls_back_to_registry():
    error = DomainError(CODE_STATE_CONFLICT, message="x" * 300)
    assert error.public_message == "资源状态已变化，当前操作不能继续"


def test_meta_sanitizer_bounds_validation_errors():
    errors = [
        {"loc": f"body.items.{index}", "type": "value_error", "msg": "invalid", "input": "secret"}
        for index in range(30)
    ]
    meta = sanitize_meta({"errors": errors, "token": "secret"})

    assert len(meta["errors"]) == 20
    assert set(meta["errors"][0]) == {"loc", "type", "msg"}
    assert "token" not in meta


def test_meta_sanitizer_keeps_degraded_flag():
    meta = sanitize_meta(
        {
            "degraded": True,
            "degraded_reason": "redis",
            "retry_after": 9,
            "secret": "hidden",
        }
    )
    assert meta == {
        "degraded": True,
        "degraded_reason": "redis",
        "retry_after": 9,
    }
