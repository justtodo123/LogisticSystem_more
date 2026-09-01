from config.database_url import engine_create_kwargs, resolve_database_url


def test_resolve_database_url_rewrites_legacy_postgres_driver():
    resolved = resolve_database_url("postgresql://user:secret@db.example/app")

    assert resolved.startswith("postgresql+psycopg://")
    assert "user:secret@" in resolved
    assert resolved.endswith("/app")


def test_resolve_database_url_keeps_psycopg_driver():
    source = "postgresql+psycopg://user:secret@db.example/app"
    assert resolve_database_url(source) == source


def test_engine_create_kwargs_sqlite_has_no_pool_override():
    kwargs = engine_create_kwargs("sqlite:///app.db")
    assert kwargs == {"connect_args": {"check_same_thread": False}}


def test_engine_create_kwargs_postgres_enables_pool_pre_ping():
    kwargs = engine_create_kwargs(
        "postgresql+psycopg://user:secret@db.example/app",
        pool_size=8,
        max_overflow=2,
    )
    assert kwargs["connect_args"] == {}
    assert kwargs["pool_pre_ping"] is True
    assert kwargs["pool_size"] == 8
    assert kwargs["max_overflow"] == 2
    assert kwargs["pool_timeout"] == 30
