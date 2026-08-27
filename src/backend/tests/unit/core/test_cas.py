"""CAS helper tests."""

import pytest
from sqlalchemy.orm import Session

from core.cas import claim_status
from core.error_codes import CODE_STATE_CONFLICT
from core.errors import DomainError
from models.global_schedule import GlobalSchedule
from models.package import Package


def _draft(db: Session) -> GlobalSchedule:
    gs = GlobalSchedule(
        schedule_code="GS_CAS_001",
        order_codes=["O001"],
        goods_schedules=[],
        total_distance=1,
        total_time=1,
        total_goods=1,
        score=1,
        status="draft",
        version=1,
        is_replan=False,
    )
    db.add(gs)
    db.commit()
    db.refresh(gs)
    return gs


def _in_transit_package(db: Session, test_nodes) -> Package:
    pkg = Package(
        package_code="PKG_CAS_001",
        from_node_id=test_nodes["SC001"].id,
        to_node_id=test_nodes["SO001"].id,
        weight=10.0,
        volume=0.5,
        status="in_transit",
        goods_items=[],
    )
    db.add(pkg)
    db.commit()
    db.refresh(pkg)
    return pkg


def test_claim_status_updates_one_row(db_session):
    gs = _draft(db_session)

    affected = claim_status(
        db_session,
        GlobalSchedule,
        identity=GlobalSchedule.id == gs.id,
        from_statuses="draft",
        to_status="active",
        increment_version=True,
    )
    db_session.commit()
    db_session.refresh(gs)

    assert affected == 1
    assert gs.status == "active"
    assert gs.version == 2


def test_claim_status_conflict_raises_registered_error(db_session):
    gs = _draft(db_session)
    claim_status(
        db_session,
        GlobalSchedule,
        identity=GlobalSchedule.id == gs.id,
        from_statuses="draft",
        to_status="active",
    )
    db_session.commit()

    with pytest.raises(DomainError) as caught:
        claim_status(
            db_session,
            GlobalSchedule,
            identity=GlobalSchedule.id == gs.id,
            from_statuses="draft",
            to_status="active",
        )

    assert caught.value.code == CODE_STATE_CONFLICT
    assert caught.value.http_status == 409


def test_claim_in_transit_to_delivered_second_is_40901(db_session, test_nodes):
    pkg = _in_transit_package(db_session, test_nodes)

    affected = claim_status(
        db_session,
        Package,
        identity=Package.id == pkg.id,
        from_statuses="in_transit",
        to_status="delivered",
    )
    db_session.commit()
    db_session.refresh(pkg)

    assert affected == 1
    assert pkg.status == "delivered"

    with pytest.raises(DomainError) as caught:
        claim_status(
            db_session,
            Package,
            identity=Package.id == pkg.id,
            from_statuses="in_transit",
            to_status="delivered",
        )

    assert caught.value.code == CODE_STATE_CONFLICT
    assert caught.value.http_status == 409


def test_claim_delivered_to_exception_succeeds(db_session, test_nodes):
    pkg = _in_transit_package(db_session, test_nodes)
    claim_status(
        db_session,
        Package,
        identity=Package.id == pkg.id,
        from_statuses="in_transit",
        to_status="delivered",
    )
    db_session.commit()

    affected = claim_status(
        db_session,
        Package,
        identity=Package.id == pkg.id,
        from_statuses=("in_transit", "delivered"),
        to_status="exception",
    )
    db_session.commit()
    db_session.refresh(pkg)

    assert affected == 1
    assert pkg.status == "exception"


def test_claim_exception_to_exception_conflicts(db_session, test_nodes):
    pkg = _in_transit_package(db_session, test_nodes)
    claim_status(
        db_session,
        Package,
        identity=Package.id == pkg.id,
        from_statuses=("in_transit", "delivered"),
        to_status="exception",
    )
    db_session.commit()

    with pytest.raises(DomainError) as caught:
        claim_status(
            db_session,
            Package,
            identity=Package.id == pkg.id,
            from_statuses=("in_transit", "delivered"),
            to_status="exception",
        )

    assert caught.value.code == CODE_STATE_CONFLICT
    db_session.refresh(pkg)
    assert pkg.status == "exception"
