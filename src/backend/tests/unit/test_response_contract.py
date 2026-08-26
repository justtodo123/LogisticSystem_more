from utils.response import error_response, success_response


def test_error_response_has_exact_shape_and_null_data():
    response = error_response(
        40000,
        "参数校验失败",
        {"legacy": "must not leak"},
        meta={"errors": []},
    )

    assert set(response) == {"code", "message", "data", "meta"}
    assert response["data"] is None
    assert response["meta"] == {"errors": []}
    assert "legacy" not in str(response)


def test_success_response_remains_backward_compatible():
    assert success_response({"id": 1}) == {
        "code": 0,
        "message": "success",
        "data": {"id": 1},
        "meta": {"degraded": False, "degraded_reason": None},
    }
