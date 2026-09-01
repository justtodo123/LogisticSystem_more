"""P1 PostgreSQL/Redis fixtures. Local pytest skips unless P1_* env vars are set."""
import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from config.database_url import engine_create_kwargs
from models.registry import import_all_models


def _env(name: str) -> str:
    return os.environ.get(name, "").strip()


@pytest.fixture(scope="session")
def p1_database_url() -> str:
    url = _env("P1_DATABASE_URL") or _env("DATABASE_URL")
    if not url or not make_url(url).drivername.startswith("postgresql"):
        pytest.skip("requires P1_DATABASE_URL PostgreSQL")
    from config.database_url import resolve_database_url
    return resolve_database_url(url)


@pytest.fixture(scope="session")
def p1_redis_url() -> str:
    url = _env("P1_REDIS_URL") or _env("REDIS_URL")
    if not url.startswith("redis://"):
        pytest.skip("requires P1_REDIS_URL Redis")
    return url


@pytest.fixture
def p1_postgres(p1_database_url: str):
    """Use the migrated P1 schema with isolated rows and independent sessions."""
    import_all_models()
    engine = create_engine(
        p1_database_url,
        **engine_create_kwargs(p1_database_url, pool_size=10, max_overflow=20),
    )
    factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        bind=engine,
    )

    try:
        yield engine, factory
    finally:
        engine.dispose()


def _delete_rows(factory, *models, filters) -> None:
    if not filters or any(model not in filters for model in models):
        raise ValueError("P1 cleanup requires an explicit filter for every model")

    session = factory()
    try:
        for model in models:
            (
                session.query(model)
                .filter(filters[model])
                .delete(synchronize_session=False)
            )
        session.commit()
    finally:
        session.close()


@pytest.fixture
def p1_row_cleanup(p1_postgres):
    """Register scenario-owned ORM rows for deletion after a P1 test."""
    _engine, factory = p1_postgres
    registrations = []

    def register(*models, filters) -> None:
        if not models or any(model not in filters for model in models):
            raise ValueError("P1 cleanup requires an explicit filter for every model")
        registrations.append((models, filters))

    try:
        yield register
    finally:
        for models, filters in reversed(registrations):
            _delete_rows(factory, *models, filters=filters)
