"""Independent-session CAS concurrency tests for R2-01."""

from __future__ import annotations

from pathlib import Path
import uuid
from unittest.mock import patch

import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from core.error_codes import CODE_STATE_CONFLICT
from core.errors import DomainError
from models.base import Base
from models.registry import import_all_models
from models.ai_suggestion import AiSuggestion
from models.dispatch_batch import DispatchBatch
from models.exception_event import ExceptionEvent
from models.global_schedule import GlobalSchedule
from models.log_event import LogEvent
from models.package import Package
from models.user import User
from services.ai_suggestion_service import confirm_suggestion, create_suggestion, reject_suggestion
from services.arrival_confirm_service import ArrivalConfirmService
from services.schedule_service import ScheduleService


def _isolated_engine(prefix: str):
    import_all_models()
    db_dir = Path(__file__).resolve().parents[5] / "tmp"
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / f"{prefix}_{uuid.uuid4().hex}.db"
    engine = create_engine(
        f"sqlite:///{db_path.resolve().as_posix()}",
        connect_args={"check_same_thread": False, "timeout": 30},
        poolclass=NullPool,
    )
    with engine.begin() as connection:
        connection.execute(text("PRAGMA busy_timeout=30000"))
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, factory


@pytest.fixture
def test_db():
    engine, factory = _isolated_engine("r2_01_cas")
    yield engine, factory
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def _run_threaded(func, n: int):
    with ThreadPoolExecutor(max_workers=n) as pool:
        return list(pool.map(lambda _: func(), range(n)))


def _classify(results):
    successes = []
    conflicts = []
    others = []
    for item in results:
        if isinstance(item, DomainError):
            if item.code == CODE_STATE_CONFLICT:
                conflicts.append(item)
            else:
                others.append(item)
        elif isinstance(item, dict) and item.get("code") == 0:
            successes.append(item)
        elif isinstance(item, dict) and item.get("package_code") and item.get("status") in {"delivered", "exception"}:
            successes.append(item)
        else:
            others.append(item)
    return successes, conflicts, others


class TestScheduleConfirmCAS:
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.parametrize("concurrency", [20, 100])
    async def test_concurrent_confirm_has_single_winner(
        self, test_db, db_session, test_nodes, test_orders, test_goods, concurrency
    ):
        _engine, factory = test_db
        preview = await ScheduleService.create_global_schedule(
            order_codes=None,
            algorithm="traditional",
            db=db_session,
            preview=True,
        )
        assert preview["code"] == 0
        schedule_code = preview["data"]["schedule_code"]

        def worker():
            session = factory()
            try:
                return asyncio.run(ScheduleService.confirm_schedule(schedule_code, session))
            except DomainError as exc:
                return exc
            finally:
                session.close()

        successes, conflicts, others = _classify(_run_threaded(worker, concurrency))
        assert others == []
        assert len(successes) == 1
        assert len(conflicts) == concurrency - 1

        verify = factory()
        try:
            assert verify.query(GlobalSchedule).filter_by(schedule_code=schedule_code, status="active").count() == 1
            packages = verify.query(Package).all()
            assert len(packages) == successes[0]["data"]["package_count"]
            assert len({pkg.package_code for pkg in packages}) == len(packages)
            assert verify.query(DispatchBatch).count() == 0
        finally:
            verify.close()


class TestArrivalConfirmCAS:
    def _seed_in_transit_package(self, factory):
        from models.node import Node
        from models.storage_center import StorageCenter

        db_session = factory()
        n1 = Node(node_code="SC001", name="a", location="x", latitude=1, longitude=1, node_type="storage_center")
        n2 = Node(node_code="SO001", name="b", location="x", latitude=1, longitude=1, node_type="storage_center")
        db_session.add_all([n1, n2])
        db_session.flush()
        db_session.add(StorageCenter(node_id=n1.id, capacity=1, inventory=0))
        schedule = GlobalSchedule(
            schedule_code="GS_ARRIVAL_CAS",
            order_codes=[],
            total_distance=0.0,
            total_time=0.0,
            total_goods=0,
            score=0.0,
            algorithm_type="traditional",
            version=1,
            is_replan=False,
            goods_schedules=[],
        )
        db_session.add(schedule)
        db_session.flush()
        package = Package(
            package_code="PKG_ARRIVAL_CAS",
            from_node_id=n1.id,
            to_node_id=n2.id,
            weight=10.0,
            volume=0.5,
            status="in_transit",
            schedule_id=schedule.id,
            goods_items=[],
        )
        db_session.add(package)
        db_session.commit()
        code = package.package_code
        db_session.close()
        return code

    def _confirm(self, session, package_code, is_normal):
        return ArrivalConfirmService.confirm_arrival(
            db=session,
            schedule_code="GS_ARRIVAL_CAS",
            package_code=package_code,
            is_normal=is_normal,
            exception_subtype=None if is_normal else "damaged",
        )

    @pytest.mark.unit
    def test_in_transit_to_delivered_second_is_40901(self):
        engine, factory = _isolated_engine("arrival_seq")
        package_code = self._seed_in_transit_package(factory)
        try:
            first = factory()
            result = self._confirm(first, package_code, True)
            first.commit()
            first.close()
            assert result["status"] == "delivered"

            second = factory()
            with pytest.raises(DomainError) as caught:
                self._confirm(second, package_code, True)
            second.rollback()
            second.close()
            assert caught.value.code == CODE_STATE_CONFLICT
        finally:
            engine.dispose()

    @pytest.mark.unit
    def test_delivered_to_exception_first_succeeds(self):
        engine, factory = _isolated_engine("arrival_exc_ok")
        package_code = self._seed_in_transit_package(factory)
        try:
            delivered = factory()
            self._confirm(delivered, package_code, True)
            delivered.commit()
            delivered.close()

            marked = factory()
            result = self._confirm(marked, package_code, False)
            marked.commit()
            marked.close()
            assert result["status"] == "exception"

            verify = factory()
            assert verify.query(Package).filter_by(package_code=package_code, status="exception").count() == 1
            assert verify.query(ExceptionEvent).filter_by(target_code=package_code).count() == 1
            verify.close()
        finally:
            engine.dispose()

    @pytest.mark.unit
    def test_exception_to_exception_conflicts(self):
        engine, factory = _isolated_engine("arrival_exc_conflict")
        package_code = self._seed_in_transit_package(factory)
        try:
            first = factory()
            self._confirm(first, package_code, False)
            first.commit()
            first.close()

            second = factory()
            with pytest.raises(DomainError) as caught:
                self._confirm(second, package_code, False)
            second.rollback()
            second.close()
            assert caught.value.code == CODE_STATE_CONFLICT

            verify = factory()
            assert verify.query(ExceptionEvent).filter_by(target_code=package_code).count() == 1
            verify.close()
        finally:
            engine.dispose()

    @pytest.mark.unit
    @pytest.mark.parametrize("concurrency", [20, 100])
    def test_concurrent_arrival_has_single_winner(self, concurrency):
        engine, factory = _isolated_engine("arrival")
        package_code = self._seed_in_transit_package(factory)

        def worker():
            session = factory()
            try:
                result = self._confirm(session, package_code, True)
                session.commit()
                return result
            except DomainError as exc:
                session.rollback()
                return exc
            finally:
                session.close()

        with patch("services.notification.send_notification_fire_and_forget") as notify:
            successes, conflicts, others = _classify(_run_threaded(worker, concurrency))
        assert others == []
        assert len(successes) == 1
        assert len(conflicts) == concurrency - 1
        assert notify.call_count == 0

        verify = factory()
        try:
            assert verify.query(Package).filter_by(package_code=package_code, status="delivered").count() == 1
            assert verify.query(Package).count() == 1
            assert verify.query(ExceptionEvent).count() == 0
            assert verify.query(LogEvent).count() == 0
        finally:
            verify.close()
            engine.dispose()

    @pytest.mark.unit
    @pytest.mark.parametrize("concurrency", [20, 100])
    def test_concurrent_exception_has_single_winner(self, concurrency):
        engine, factory = _isolated_engine("arrival_exc")
        package_code = self._seed_in_transit_package(factory)

        def worker():
            session = factory()
            try:
                result = self._confirm(session, package_code, False)
                session.commit()
                return result
            except DomainError as exc:
                session.rollback()
                return exc
            finally:
                session.close()

        successes, conflicts, others = _classify(_run_threaded(worker, concurrency))
        assert others == []
        assert len(successes) == 1
        assert len(conflicts) == concurrency - 1

        verify = factory()
        try:
            assert verify.query(Package).filter_by(package_code=package_code, status="exception").count() == 1
            assert verify.query(Package).count() == 1
            assert verify.query(ExceptionEvent).count() == 1
            assert verify.query(LogEvent).count() == 0
        finally:
            verify.close()
            engine.dispose()


class TestAiSuggestionCAS:
    def _seed_pending(self, db_session, test_users):
        user = test_users["dispatcher"]
        return create_suggestion(
            db=db_session,
            level="info",
            source="explain",
            title="cas",
            content="cas",
            user_id=user.id,
            role=user.role,
        )

    @pytest.mark.unit
    @pytest.mark.parametrize("concurrency", [20, 100])
    def test_concurrent_confirm_has_single_winner(self, test_db, db_session, test_users, concurrency):
        _engine, factory = test_db
        suggestion = self._seed_pending(db_session, test_users)
        user = db_session.query(User).filter_by(username="dispatcher").one()

        def worker():
            session = factory()
            try:
                return asyncio.run(confirm_suggestion(session, suggestion.id, user))
            except DomainError as exc:
                return exc
            finally:
                session.close()

        successes, conflicts, others = _classify(_run_threaded(worker, concurrency))
        assert others == []
        assert len(successes) == 1
        assert len(conflicts) == concurrency - 1
        verify = factory()
        try:
            stored = verify.query(AiSuggestion).filter_by(id=suggestion.id).one()
            assert stored.status == "confirmed"
            assert verify.query(LogEvent).filter(LogEvent.event_name.like("%ai%")).count() <= 1
            assert verify.query(LogEvent).count() == 1
        finally:
            verify.close()

    @pytest.mark.unit
    def test_concurrent_reject_has_single_winner(self, test_db, db_session, test_users):
        _engine, factory = test_db
        suggestion = self._seed_pending(db_session, test_users)
        user = db_session.query(User).filter_by(username="dispatcher").one()

        def worker():
            session = factory()
            try:
                return reject_suggestion(session, suggestion.id, user)
            except DomainError as exc:
                return exc
            finally:
                session.close()

        successes, conflicts, others = _classify(_run_threaded(worker, 20))
        assert others == []
        assert len(successes) == 1
        assert len(conflicts) == 19
