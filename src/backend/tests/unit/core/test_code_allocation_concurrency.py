"""Independent-session concurrency tests for R2-02B code ranges."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from core.code_allocation import RESOURCE_GLOBAL_SCHEDULE, allocate_code
from core.errors import DomainError
from models.base import Base
from models.code_range import CodeRange
from models.global_schedule import GlobalSchedule
from models.registry import import_all_models


NOW = datetime(2026, 8, 28, 12, 0, 0)


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


@pytest.mark.unit
@pytest.mark.parametrize("concurrency", [20, 100])
def test_concurrent_allocate_codes_are_unique(concurrency):
    engine, factory = _isolated_engine("r2_02b_alloc")

    def worker():
        session = factory()
        try:
            code = allocate_code(session, RESOURCE_GLOBAL_SCHEDULE, now=NOW)
            session.add(_schedule(code))
            session.commit()
            return code
        except DomainError as exc:
            session.rollback()
            return exc
        except Exception as exc:
            session.rollback()
            return exc
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        results = list(pool.map(lambda _: worker(), range(concurrency)))

    errors = [item for item in results if not isinstance(item, str)]
    codes = [item for item in results if isinstance(item, str)]
    assert errors == []
    assert len(codes) == concurrency
    assert len(set(codes)) == concurrency
    assert set(codes) == {f"GS20260828{i:03d}" for i in range(1, concurrency + 1)}

    verify = factory()
    try:
        stored = [row.schedule_code for row in verify.query(GlobalSchedule).all()]
        assert len(stored) == concurrency
        assert len(set(stored)) == concurrency
        row = verify.query(CodeRange).one()
        assert row.resource == RESOURCE_GLOBAL_SCHEDULE
        assert row.prefix == "GS20260828"
        assert row.next_value == concurrency + 1
    finally:
        verify.close()
        engine.dispose()