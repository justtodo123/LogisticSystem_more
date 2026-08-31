from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

from config.database_url import engine_create_kwargs
from scripts.release_migrate import migrate_release_database
from utils.schema_management import alembic_config


def test_postgres_release_migrate_reaches_unique_head(p1_database_url: str):
    migrate_release_database(p1_database_url)

    config = alembic_config(p1_database_url)
    head = ScriptDirectory.from_config(config).get_current_head()
    engine = create_engine(p1_database_url, **engine_create_kwargs(p1_database_url))
    try:
        with engine.connect() as connection:
            current = MigrationContext.configure(connection).get_current_revision()
            version = connection.execute(text("SELECT version()")).scalar_one()
    finally:
        engine.dispose()

    assert head is not None
    assert current == head
    assert "PostgreSQL" in version
