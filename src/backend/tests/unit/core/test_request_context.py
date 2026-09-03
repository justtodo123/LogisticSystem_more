"""Unit tests for request-scoped ID helpers."""

from core.request_context import (
    RequestContext,
    bind_request_context,
    context_as_dict,
    generate_id,
    get_request_context,
    normalize_id,
    reset_request_context,
    update_request_context,
)


def test_normalize_id_accepts_safe_tokens_and_rejects_junk():
    assert normalize_id("req-1_abc.DEF") == "req-1_abc.DEF"
    assert normalize_id("bad id") is None
    assert normalize_id("has/slash") is None
    assert normalize_id("") is None
    assert normalize_id("x" * 129) is None
    assert normalize_id(None) is None


def test_bind_and_update_context_then_reset():
    token = bind_request_context(
        RequestContext(request_id="r1", trace_id="t1", task_id="7")
    )
    try:
        assert get_request_context().request_id == "r1"
        updated = update_request_context(user_id="9", role="dispatcher", parent_request_id="req-parent")
        assert updated.user_id == "9"
        assert context_as_dict()["task_id"] == "7"
        assert context_as_dict()["role"] == "dispatcher"
        assert context_as_dict()["parent_request_id"] == "req-parent"
    finally:
        reset_request_context(token)
    assert get_request_context() is None


def test_generate_id_is_hex():
    value = generate_id()
    assert len(value) == 32
    int(value, 16)
