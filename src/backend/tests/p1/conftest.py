"""P1 PostgreSQL/Redis fixtures. Local pytest skips unless P1_* env vars are set."""
import os

import pytest
from sqlalchemy.engine import make_url


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
