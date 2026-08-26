from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from config.database_url import (
    engine_connect_args,
    ensure_sqlite_parent_dir,
    resolve_database_url,
)
from config.settings import settings
from models.base import Base
from models.registry import import_all_models

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

import_all_models()
target_metadata = Base.metadata

database_url = resolve_database_url(
    config.attributes.get("database_url", settings.DATABASE_URL)
)
config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))


def run_migrations_offline() -> None:
    """Run migrations without creating an Engine."""
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using the same database URL as the application."""
    ensure_sqlite_parent_dir(database_url)
    connectable = create_engine(
        database_url,
        connect_args=engine_connect_args(database_url),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=connection.dialect.name == "sqlite",
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
