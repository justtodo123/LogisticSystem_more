"""Unit tests for R2-02B code range allocation."""

from __future__ import annotations

from datetime import datetime
import inspect

import pytest

from algorithms.global_schedule import _generate_schedule_code
from algorithms.node_dispatch import _generate_batch_code, _generate_dispatch_code
from algorithms.packaging import _generate_package_code
from algorithms.route_planning import _generate_route_code
from core.code_allocation import (
    MAX_UNIQUE_RETRIES,
    RESOURCE_DISPATCH_BATCH,
    RESOURCE_GLOBAL_SCHEDULE,
    RESOURCE_NODE_DISPATCH,
    RESOURCE_PACKAGE,
    RESOURCE_ROUTE,
    allocate_code,
    seed_next_value,
)
from core.error_codes import CODE_CODE_ALLOCATION_CONFLICT, CODE_CODE_RANGE_EXHAUSTED
from core.errors import DomainError
from models.code_range import CodeRange
from models.global_schedule import GlobalSchedule
from models.package import Package


NOW = datetime(2026, 8, 28, 12, 0, 0)


def _schedule(code: str) -> GlobalSchedule:
    return GlobalSchedule(
        schedule_code=code,
        order_codes=["O001"],
        goods_schedules=[],
        total_distance=1,
        total_time=1,
        total_goods=1,
        score=1,
        algorithm_type="traditional",
        status="draft",
        version=1,
        is_replan=False,
    )


def test_unknown_resource_fails_closed(db_session):
    with pytest.raises(ValueError, match="未知编号资源"):
        allocate_code(db_session, "unknown")


@pytest.mark.parametrize(
    ("resource", "expected"),
    [
        (RESOURCE_GLOBAL_SCHEDULE, "GS20260828001"),
        (RESOURCE_PACKAGE, "PKG202608280001"),
        (RESOURCE_ROUTE, "ROUTE20260828001"),
        (RESOURCE_DISPATCH_BATCH, "BATCH20260828001"),
        (RESOURCE_NODE_DISPATCH, "DISP20260828001"),
    ],
)
def test_allocate_code_keeps_external_format(db_session, resource, expected):
    assert allocate_code(db_session, resource, now=NOW) == expected
    db_session.expire_all()
    row = db_session.query(CodeRange).filter_by(resource=resource).one()
    suffix = 4 if resource == RESOURCE_PACKAGE else 3
    assert row.prefix == expected[:-suffix]
    assert row.next_value == 2


def test_sequential_allocations_are_unique_and_contiguous(db_session):
    codes = [
        allocate_code(db_session, RESOURCE_GLOBAL_SCHEDULE, now=NOW)
        for _ in range(20)
    ]
    assert codes == [f"GS20260828{i:03d}" for i in range(1, 21)]
    assert len(set(codes)) == 20
    db_session.expire_all()
    row = db_session.query(CodeRange).one()
    assert row.next_value == 21


def test_seeds_next_value_from_existing_max(db_session):
    db_session.add(_schedule("GS20260828007"))
    db_session.flush()

    code = allocate_code(db_session, RESOURCE_GLOBAL_SCHEDULE, now=NOW)

    assert code == "GS20260828008"
    db_session.expire_all()
    assert db_session.query(CodeRange).one().next_value == 9


def test_skips_occupied_code_then_returns_next(db_session, monkeypatch):
    db_session.add(
        CodeRange(
            resource=RESOURCE_GLOBAL_SCHEDULE,
            prefix="GS20260828",
            next_value=1,
            width=3,
        )
    )
    db_session.add(_schedule("GS20260828001"))
    db_session.flush()

    calls = {"n": 0}
    original = seed_next_value

    def wrapped(*args, **kwargs):
        calls["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr("core.code_allocation.seed_next_value", wrapped)

    code = allocate_code(db_session, RESOURCE_GLOBAL_SCHEDULE, now=NOW)

    assert code == "GS20260828002"
    assert calls["n"] == 0


def test_unique_retry_exhaustion_uses_registered_code(db_session, monkeypatch):
    db_session.add(
        CodeRange(
            resource=RESOURCE_GLOBAL_SCHEDULE,
            prefix="GS20260828",
            next_value=1,
            width=3,
        )
    )
    db_session.flush()
    monkeypatch.setattr("core.code_allocation._code_taken", lambda *args, **kwargs: True)

    with pytest.raises(DomainError) as caught:
        allocate_code(db_session, RESOURCE_GLOBAL_SCHEDULE, now=NOW)

    assert caught.value.code == CODE_CODE_ALLOCATION_CONFLICT
    assert caught.value.http_status == 409
    db_session.expire_all()
    assert db_session.query(CodeRange).one().next_value == 1 + MAX_UNIQUE_RETRIES


def test_range_exhaustion_uses_registered_code(db_session):
    db_session.add(
        CodeRange(
            resource=RESOURCE_GLOBAL_SCHEDULE,
            prefix="GS20260828",
            next_value=1000,
            width=3,
        )
    )
    db_session.flush()

    with pytest.raises(DomainError) as caught:
        allocate_code(db_session, RESOURCE_GLOBAL_SCHEDULE, now=NOW)

    assert caught.value.code == CODE_CODE_RANGE_EXHAUSTED
    assert caught.value.http_status == 409
    assert caught.value.public_message == "业务编号号段已耗尽"


def test_seed_exhaustion_when_existing_codes_fill_width(db_session):
    db_session.add(_schedule("GS20260828999"))
    db_session.flush()

    with pytest.raises(DomainError) as caught:
        allocate_code(db_session, RESOURCE_GLOBAL_SCHEDULE, now=NOW)

    assert caught.value.code == CODE_CODE_RANGE_EXHAUSTED


def test_same_session_package_codes_do_not_collide(db_session, test_nodes):
    codes = [
        allocate_code(db_session, RESOURCE_PACKAGE, now=NOW)
        for _ in range(5)
    ]
    for code in codes:
        db_session.add(
            Package(
                package_code=code,
                weight=1,
                volume=1,
                status="packed",
                from_node_id=test_nodes["SC001"].id,
                to_node_id=test_nodes["SO001"].id,
                goods_items=[],
            )
        )
    db_session.flush()
    assert codes == [f"PKG20260828{i:04d}" for i in range(1, 6)]
    assert {pkg.package_code for pkg in db_session.query(Package).all()} == set(codes)


@pytest.mark.parametrize(
    "func",
    [
        _generate_schedule_code,
        _generate_package_code,
        _generate_route_code,
        _generate_batch_code,
        _generate_dispatch_code,
    ],
)
def test_generators_delegate_to_allocator_without_max_scan(func):
    source = inspect.getsource(func)
    assert "allocate_code" in source
    assert ".like(" not in source
    assert "max + 1" not in source
    assert "_schedule_seq" not in source


def test_volume_200_has_no_duplicates(db_session):
    codes = [
        allocate_code(db_session, RESOURCE_PACKAGE, now=NOW)
        for _ in range(200)
    ]
    assert len(codes) == 200
    assert len(set(codes)) == 200
    assert codes[0] == "PKG202608280001"
    assert codes[-1] == "PKG202608280200"
    assert db_session.query(CodeRange).one().next_value == 201