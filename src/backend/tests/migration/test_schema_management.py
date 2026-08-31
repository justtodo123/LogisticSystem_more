from pathlib import Path
import shutil
import sqlite3

import pytest
from alembic import command
from sqlalchemy import create_engine, text

from models.base import Base
from models.registry import import_all_models
from utils.schema_management import (
    SchemaKind,
    adopt_known_mixed_sqlite,
    alembic_config,
    migrate_managed_sqlite_copy,
    classify_sqlite,
    file_sha256,
    sqlite_database_url,
)


HEAD_REVISION = "r2_03_replan_task_claims"


def _upgrade(path: Path, revision: str = "head") -> None:
    command.upgrade(alembic_config(sqlite_database_url(path)), revision)


def _version(path: Path) -> str:
    with sqlite3.connect(path) as connection:
        row = connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchone()
    assert row is not None
    return row[0]


def _create_stamped_legacy_exception_db(path: Path, *, populated: bool) -> None:
    """构造历史 create_all + phase7 stamp 产生的异常事件表。"""
    _upgrade(path, "17b1974d0918")
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE exception_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_code VARCHAR(64) NOT NULL UNIQUE,
                exception_type VARCHAR(32) NOT NULL,
                exception_subtype VARCHAR(64),
                target_type VARCHAR(32),
                target_code VARCHAR(64),
                severity VARCHAR(32),
                recommended_action VARCHAR(32) NOT NULL,
                trigger_node_id INTEGER,
                related_route_id INTEGER,
                related_schedule_code VARCHAR(64),
                replan_batch_code VARCHAR(64),
                description TEXT NOT NULL,
                status VARCHAR(32) NOT NULL DEFAULT 'open',
                resolution_note TEXT,
                resolved_at DATETIME,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE UNIQUE INDEX ix_exception_events_event_code
                ON exception_events (event_code);
            """
        )
        if populated:
            connection.execute(
                """
                INSERT INTO exception_events (
                    event_code, exception_type, severity, recommended_action,
                    trigger_node_id, description, resolution_note
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "LEGACY-EVENT-001",
                    "node",
                    "high",
                    "redispatch",
                    7,
                    "legacy event",
                    "must be preserved",
                ),
            )
        connection.execute("DELETE FROM alembic_version")
        connection.execute(
            "INSERT INTO alembic_version (version_num) VALUES (?)",
            ("phase7_exception_fields",),
        )
        connection.commit()


def test_outbox_events_table_added_from_replan_tasks(tmp_path: Path):
    database = tmp_path / "outbox-events.db"
    _upgrade(database, "r2_03_replan_tasks")
    with sqlite3.connect(database) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert "outbox_events" not in tables

    _upgrade(database)
    with sqlite3.connect(database) as connection:
        columns = {
            item[1]
            for item in connection.execute("PRAGMA table_info(outbox_events)")
        }
        indexes = {
            item[1]: bool(item[2])
            for item in connection.execute("PRAGMA index_list(outbox_events)")
        }

    assert columns == {
        "id",
        "dedup_key",
        "event_type",
        "payload",
        "status",
        "retry_count",
        "last_error",
        "available_at",
        "claim_token",
        "claimed_by",
        "claimed_at",
        "lease_until",
        "delivered_at",
        "created_at",
        "updated_at",
    }
    assert indexes["uq_outbox_events_dedup_key"] is True
    assert indexes["ix_outbox_events_status_available_at"] is False
    assert indexes["ix_outbox_events_status_lease_until"] is False
    assert _version(database) == HEAD_REVISION

    command.downgrade(
        alembic_config(sqlite_database_url(database)),
        "r2_03_replan_tasks",
    )
    with sqlite3.connect(database) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    assert "outbox_events" not in tables
    assert _version(database) == "r2_03_replan_tasks"


def test_replan_task_execution_claims_are_migrated(tmp_path: Path):
    database = tmp_path / "replan-task-claims.db"
    _upgrade(database, "r2_03_outbox_claims")

    with sqlite3.connect(database) as connection:
        before = {
            item[1]
            for item in connection.execute("PRAGMA table_info(replan_tasks)")
        }
    assert "claim_token" not in before

    _upgrade(database)
    with sqlite3.connect(database) as connection:
        columns = {
            item[1]
            for item in connection.execute("PRAGMA table_info(replan_tasks)")
        }
        indexes = {
            item[1]: bool(item[2])
            for item in connection.execute("PRAGMA index_list(replan_tasks)")
        }

    assert {"claim_token", "claimed_by", "claimed_step", "claimed_at", "lease_until"} <= columns
    assert indexes["ix_replan_tasks_status_lease_until"] is False
    assert _version(database) == HEAD_REVISION

    command.downgrade(
        alembic_config(sqlite_database_url(database)),
        "r2_03_outbox_claims",
    )
    with sqlite3.connect(database) as connection:
        after = {
            item[1]
            for item in connection.execute("PRAGMA table_info(replan_tasks)")
        }
    assert "claim_token" not in after
    assert _version(database) == "r2_03_outbox_claims"


def test_replan_tasks_table_added_from_r2_02b(tmp_path: Path):
    database = tmp_path / "replan-tasks.db"
    _upgrade(database, "r2_02b_code_range_allocation")
    with sqlite3.connect(database) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert "replan_tasks" not in tables

    _upgrade(database)
    with sqlite3.connect(database) as connection:
        columns = {
            item[1]
            for item in connection.execute("PRAGMA table_info(replan_tasks)")
        }
        indexes = {
            item[1]: bool(item[2])
            for item in connection.execute("PRAGMA index_list(replan_tasks)")
        }

    assert columns == {
        "id",
        "idempotency_key",
        "request_fingerprint",
        "operation_type",
        "original_resource_id",
        "original_resource_code",
        "new_schedule_id",
        "new_schedule_code",
        "dispatch_batch_id",
        "dispatch_batch_code",
        "new_route_id",
        "new_route_code",
        "status",
        "current_step",
        "retry_count",
        "last_error",
        "version",
        "manual_required",
        "claim_token",
        "claimed_by",
        "claimed_step",
        "claimed_at",
        "lease_until",
        "created_at",
        "updated_at",
    }
    assert indexes["uq_replan_tasks_idempotency_key"] is True
    assert indexes["ix_replan_tasks_status_step"] is False
    assert indexes["ix_replan_tasks_status_lease_until"] is False
    assert _version(database) == HEAD_REVISION

    command.downgrade(
        alembic_config(sqlite_database_url(database)),
        "r2_02b_code_range_allocation",
    )
    with sqlite3.connect(database) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    assert "replan_tasks" not in tables
    assert _version(database) == "r2_02b_code_range_allocation"


def test_code_ranges_table_added_from_r2_02a(tmp_path: Path):
    database = tmp_path / "code-ranges.db"
    _upgrade(database, "r2_02a_idempotency_state")
    with sqlite3.connect(database) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert "code_ranges" not in tables

    _upgrade(database)
    with sqlite3.connect(database) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        columns = {
            item[1]
            for item in connection.execute("PRAGMA table_info(code_ranges)")
        }
        indexes = {
            item[1]
            for item in connection.execute("PRAGMA index_list(code_ranges)")
        }

    assert "code_ranges" in tables
    assert columns == {"id", "resource", "prefix", "next_value", "width"}
    assert "uq_code_ranges_resource_prefix" in indexes
    assert _version(database) == HEAD_REVISION

    command.downgrade(alembic_config(sqlite_database_url(database)), "r2_02a_idempotency_state")
    with sqlite3.connect(database) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    assert "code_ranges" not in tables
    assert _version(database) == "r2_02a_idempotency_state"


def test_fresh_upgrade_has_one_head_and_no_metadata_drift(tmp_path: Path):
    db_path = tmp_path / "fresh.db"
    config = alembic_config(sqlite_database_url(db_path))

    _upgrade(db_path)
    command.check(config)
    _upgrade(db_path)

    assert _version(db_path) == HEAD_REVISION
    assert classify_sqlite(db_path).kind is SchemaKind.ALEMBIC_MANAGED


def test_idempotency_legacy_rows_expire_and_downgrade_preserves_payload(
    tmp_path: Path,
):
    database = tmp_path / "idempotency-legacy.db"
    _upgrade(database, "r2_00a_schema_convergence")
    legacy_payload = '{"code": 0, "data": {"legacy": true}}'
    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            INSERT INTO idempotency_records (
                idempotency_key, response_data, expires_at
            ) VALUES (?, ?, ?)
            """,
            ("legacy-key", legacy_payload, "2099-01-01 00:00:00"),
        )
        connection.commit()

    _upgrade(database)
    with sqlite3.connect(database) as connection:
        row = connection.execute(
            """
            SELECT status, payload_hash, claim_token, http_status,
                   response_body, response_data
            FROM idempotency_records
            WHERE idempotency_key = ?
            """,
            ("legacy-key",),
        ).fetchone()
        indexes = {
            item[1]
            for item in connection.execute("PRAGMA index_list(idempotency_records)")
        }

    assert row == ("EXPIRED", None, None, None, None, legacy_payload)
    assert "ix_idempotency_records_status_expires_at" in indexes

    command.downgrade(
        alembic_config(sqlite_database_url(database)),
        "r2_00a_schema_convergence",
    )
    with sqlite3.connect(database) as connection:
        columns = {
            item[1]
            for item in connection.execute("PRAGMA table_info(idempotency_records)")
        }
        preserved = connection.execute(
            "SELECT response_data FROM idempotency_records WHERE idempotency_key = ?",
            ("legacy-key",),
        ).fetchone()

    assert columns == {
        "id",
        "idempotency_key",
        "response_data",
        "created_at",
        "expires_at",
    }
    assert preserved == (legacy_payload,)


def test_managed_legacy_upgrade_preserves_seed_data(tmp_path: Path):
    db_path = tmp_path / "managed-legacy.db"
    _upgrade(db_path, "c78f9b436833")

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO users (
                username, password_hash, role, display_name, is_active
            ) VALUES (?, ?, ?, ?, ?)
            """,
            ("migration-user", "redacted", "viewer", "Migration User", 1),
        )
        connection.commit()

    _upgrade(db_path)

    with sqlite3.connect(db_path) as connection:
        username = connection.execute(
            "SELECT username FROM users WHERE username = ?",
            ("migration-user",),
        ).fetchone()
    assert username == ("migration-user",)
    assert _version(db_path) == HEAD_REVISION


def test_managed_legacy_is_upgraded_on_copy_and_source_is_unchanged(
    tmp_path: Path,
):
    source = tmp_path / "managed-source.db"
    target = tmp_path / "managed-upgraded.db"
    _upgrade(source, "c78f9b436833")
    with sqlite3.connect(source) as connection:
        connection.execute(
            """
            INSERT INTO users (
                username, password_hash, role, display_name, is_active
            ) VALUES (?, ?, ?, ?, ?)
            """,
            ("copy-user", "redacted", "viewer", "Copy User", 1),
        )
        connection.commit()
    source_hash = file_sha256(source)

    result = migrate_managed_sqlite_copy(source, target)

    assert result.kind is SchemaKind.ALEMBIC_MANAGED
    assert result.revision == HEAD_REVISION
    assert file_sha256(source) == source_hash
    assert _version(source) == "c78f9b436833"
    assert _version(target) == HEAD_REVISION
    with sqlite3.connect(target) as connection:
        username = connection.execute(
            "SELECT username FROM users WHERE username = 'copy-user'"
        ).fetchone()
    assert username == ("copy-user",)


def test_managed_copy_upgrade_rejects_unsafe_source_without_target(
    tmp_path: Path,
):
    source = tmp_path / "unsafe-source.db"
    target = tmp_path / "unsafe-target.db"
    _create_stamped_legacy_exception_db(source, populated=True)
    source_hash = file_sha256(source)

    with pytest.raises(ValueError, match="alembic_managed"):
        migrate_managed_sqlite_copy(source, target)

    assert not target.exists()
    assert file_sha256(source) == source_hash


def test_copy_operations_reject_source_as_target(tmp_path: Path):
    managed = tmp_path / "managed-same.db"
    _upgrade(managed, "c78f9b436833")
    managed_hash = file_sha256(managed)

    with pytest.raises(ValueError, match="目标必须与源"):
        migrate_managed_sqlite_copy(managed, managed)

    assert file_sha256(managed) == managed_hash
    assert _version(managed) == "c78f9b436833"

    mixed = tmp_path / "mixed-same.db"
    import_all_models()
    engine = create_engine(sqlite_database_url(mixed))
    Base.metadata.create_all(engine)
    engine.dispose()
    mixed_hash = file_sha256(mixed)

    with pytest.raises(ValueError, match="目标必须与源"):
        adopt_known_mixed_sqlite(mixed, mixed)

    assert file_sha256(mixed) == mixed_hash
    assert classify_sqlite(mixed).kind is SchemaKind.KNOWN_MIXED


def test_stamped_phase7_with_empty_legacy_columns_converges(tmp_path: Path):
    db_path = tmp_path / "phase7-empty-legacy.db"
    _create_stamped_legacy_exception_db(db_path, populated=False)

    _upgrade(db_path)

    with sqlite3.connect(db_path) as connection:
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(exception_events)")
        }
    assert not {
        "trigger_node_id",
        "related_route_id",
        "severity",
        "resolution_note",
    } & columns
    assert _version(db_path) == HEAD_REVISION


def test_stamped_phase7_with_populated_legacy_columns_fails_closed(
    tmp_path: Path,
):
    db_path = tmp_path / "phase7-populated-legacy.db"
    _create_stamped_legacy_exception_db(db_path, populated=True)
    original_hash = file_sha256(db_path)

    classification = classify_sqlite(db_path)

    assert classification.kind is SchemaKind.UNKNOWN
    assert classification.revision == "phase7_exception_fields"
    assert classification.reason is not None
    assert "遗留列含数据" in classification.reason
    assert _version(db_path) == "phase7_exception_fields"
    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT trigger_node_id, severity, resolution_note
            FROM exception_events WHERE event_code = ?
            """,
            ("LEGACY-EVENT-001",),
        ).fetchone()
    assert row == (7, "high", "must be preserved")
    assert file_sha256(db_path) == original_hash


def test_unversioned_current_schema_is_adopted_on_copy(tmp_path: Path):
    source = tmp_path / "mixed.db"
    target = tmp_path / "adopted.db"
    import_all_models()
    engine = create_engine(sqlite_database_url(source))
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO users (
                    username, password_hash, role, display_name, is_active
                ) VALUES (
                    'mixed-user', 'redacted', 'viewer', 'Mixed User', 1
                )
                """
            )
        )
    engine.dispose()
    source_hash = file_sha256(source)

    assert classify_sqlite(source).kind is SchemaKind.KNOWN_MIXED

    result = adopt_known_mixed_sqlite(source, target)

    assert result.kind is SchemaKind.ALEMBIC_MANAGED
    assert result.revision == HEAD_REVISION
    assert file_sha256(source) == source_hash
    with sqlite3.connect(target) as connection:
        username = connection.execute(
            "SELECT username FROM users WHERE username = 'mixed-user'"
        ).fetchone()
    assert username == ("mixed-user",)


def test_unknown_schema_is_not_mutated_or_stamped(tmp_path: Path):
    db_path = tmp_path / "unknown.db"
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE manual_data (id INTEGER PRIMARY KEY, value TEXT)")
        connection.execute("INSERT INTO manual_data (value) VALUES ('keep-me')")
        connection.commit()
    original_hash = file_sha256(db_path)

    result = classify_sqlite(db_path)

    assert result.kind is SchemaKind.UNKNOWN
    assert file_sha256(db_path) == original_hash
    with sqlite3.connect(db_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        value = connection.execute("SELECT value FROM manual_data").fetchone()
    assert "alembic_version" not in tables
    assert value == ("keep-me",)

    with pytest.raises(ValueError, match="known_mixed"):
        adopt_known_mixed_sqlite(db_path, tmp_path / "should-not-exist.db")
    assert not (tmp_path / "should-not-exist.db").exists()
    assert file_sha256(db_path) == original_hash


def test_unknown_revision_is_rejected_without_mutation(tmp_path: Path):
    db_path = tmp_path / "unknown-revision.db"
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE alembic_version (version_num VARCHAR(64) NOT NULL)")
        connection.execute(
            "INSERT INTO alembic_version (version_num) VALUES ('manual_revision')"
        )
        connection.execute("CREATE TABLE manual_data (id INTEGER PRIMARY KEY)")
        connection.commit()
    original_hash = file_sha256(db_path)

    result = classify_sqlite(db_path)

    assert result.kind is SchemaKind.UNKNOWN
    assert result.revision == "manual_revision"
    assert file_sha256(db_path) == original_hash


def test_empty_or_multiple_version_rows_are_rejected_without_mutation(
    tmp_path: Path,
):
    for name, versions in (
        ("empty", ()),
        ("multiple", ("17b1974d0918", "c78f9b436833")),
    ):
        db_path = tmp_path / f"{name}-versions.db"
        with sqlite3.connect(db_path) as connection:
            connection.execute(
                "CREATE TABLE alembic_version (version_num VARCHAR(64) NOT NULL)"
            )
            connection.execute("CREATE TABLE manual_data (id INTEGER PRIMARY KEY)")
            connection.executemany(
                "INSERT INTO alembic_version (version_num) VALUES (?)",
                [(version,) for version in versions],
            )
            connection.commit()
        original_hash = file_sha256(db_path)

        result = classify_sqlite(db_path)

        assert result.kind is SchemaKind.UNKNOWN
        assert result.reason == "alembic_version 必须且只能包含一行"
        assert file_sha256(db_path) == original_hash


def test_current_schema_with_extra_column_is_unknown_and_not_mutated(
    tmp_path: Path,
):
    db_path = tmp_path / "extra-column.db"
    import_all_models()
    engine = create_engine(sqlite_database_url(db_path))
    Base.metadata.create_all(engine)
    engine.dispose()
    with sqlite3.connect(db_path) as connection:
        connection.execute("ALTER TABLE users ADD COLUMN manual_note TEXT")
        connection.commit()
    original_hash = file_sha256(db_path)

    result = classify_sqlite(db_path)

    assert result.kind is SchemaKind.UNKNOWN
    assert result.reason is not None
    assert "ORM" in result.reason
    assert file_sha256(db_path) == original_hash


def test_current_schema_with_missing_index_is_unknown_and_not_mutated(
    tmp_path: Path,
):
    db_path = tmp_path / "missing-index.db"
    import_all_models()
    engine = create_engine(sqlite_database_url(db_path))
    Base.metadata.create_all(engine)
    engine.dispose()
    with sqlite3.connect(db_path) as connection:
        connection.execute("DROP INDEX ix_orders_created_at")
        connection.commit()
    original_hash = file_sha256(db_path)

    result = classify_sqlite(db_path)

    assert result.kind is SchemaKind.UNKNOWN
    assert file_sha256(db_path) == original_hash


def test_managed_revision_with_schema_drift_is_unknown(tmp_path: Path):
    database = tmp_path / "managed-drift.db"
    _upgrade(database, "head")
    engine = create_engine(sqlite_database_url(database))
    try:
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "ALTER TABLE users ADD COLUMN manual_note VARCHAR(32)"
            )
    finally:
        engine.dispose()

    before_hash = file_sha256(database)
    result = classify_sqlite(database)

    assert result.kind is SchemaKind.UNKNOWN
    assert result.revision == HEAD_REVISION
    assert "revision" in (result.reason or "")
    assert file_sha256(database) == before_hash


def test_managed_schema_with_unmanaged_trigger_is_unknown(
    tmp_path: Path,
):
    database = tmp_path / "trigger-drift.db"
    _upgrade(database, "head")
    with sqlite3.connect(database) as connection:
        connection.executescript(
            """
            CREATE TRIGGER manual_users_trigger AFTER INSERT ON users
            BEGIN
                UPDATE users SET display_name = 'tampered' WHERE id = NEW.id;
            END;
            """
        )
        connection.commit()
    before_hash = file_sha256(database)

    result = classify_sqlite(database)

    assert result.kind is SchemaKind.UNKNOWN
    assert result.revision == HEAD_REVISION
    assert "revision" in (result.reason or "")
    assert file_sha256(database) == before_hash


def test_wal_source_copy_preserves_committed_rows(tmp_path: Path):
    source = tmp_path / "wal-source.db"
    main_file_only = tmp_path / "main-file-only.db"
    target = tmp_path / "wal-target.db"
    import_all_models()
    keeper = sqlite3.connect(source)
    try:
        assert keeper.execute("PRAGMA journal_mode=WAL").fetchone() == ("wal",)
        keeper.execute("PRAGMA wal_autocheckpoint=0")
        engine = create_engine(sqlite_database_url(source))
        try:
            Base.metadata.create_all(engine)
        finally:
            engine.dispose()
        keeper.execute(
            "INSERT INTO users "
            "(username, password_hash, role, is_active) "
            "VALUES ('wal-user', 'redacted', 'admin', 1)"
        )
        keeper.commit()

        wal_path = Path(f"{source}-wal")
        assert wal_path.exists()
        assert wal_path.stat().st_size > 0
        shutil.copy2(source, main_file_only)
        with sqlite3.connect(main_file_only) as connection:
            try:
                main_file_row = connection.execute(
                    "SELECT username FROM users WHERE username = 'wal-user'"
                ).fetchone()
            except sqlite3.OperationalError:
                main_file_row = None
        assert main_file_row is None

        result = adopt_known_mixed_sqlite(source, target)
    finally:
        keeper.close()

    assert result.kind is SchemaKind.ALEMBIC_MANAGED
    with sqlite3.connect(target) as connection:
        assert connection.execute(
            "SELECT username FROM users WHERE username = 'wal-user'"
        ).fetchone() == ("wal-user",)


def test_classification_does_not_checkpoint_closed_wal_source(
    tmp_path: Path,
):
    source = tmp_path / "closed-wal.db"
    keeper = sqlite3.connect(source)
    try:
        keeper.execute("PRAGMA journal_mode=WAL")
        keeper.execute("PRAGMA wal_autocheckpoint=0")
        keeper.execute("CREATE TABLE manual_data (id INTEGER PRIMARY KEY)")
        keeper.execute("INSERT INTO manual_data DEFAULT VALUES")
        keeper.commit()
        wal_path = Path(f"{source}-wal")
        shm_path = Path(f"{source}-shm")
        assert wal_path.exists()
        before_main = source.read_bytes()
        before_wal = wal_path.read_bytes()
        assert shm_path.exists()

        result = classify_sqlite(source)

        assert result.kind is SchemaKind.UNKNOWN
        assert source.read_bytes() == before_main
        assert wal_path.read_bytes() == before_wal
        assert shm_path.exists()
    finally:
        keeper.close()




@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_missing_main_file_with_orphan_sidecar_is_unknown(
    tmp_path: Path,
    suffix: str,
):
    database = tmp_path / "missing-main.db"
    sidecar = Path(f"{database}{suffix}")
    original = b"orphan-sidecar-evidence"
    sidecar.write_bytes(original)

    result = classify_sqlite(database)

    assert result.kind is SchemaKind.UNKNOWN
    assert result.reason == "主 SQLite 文件不存在，但检测到孤立 journal/WAL sidecar"
    assert not database.exists()
    assert sidecar.read_bytes() == original

@pytest.mark.parametrize(
    "revision",
    (
        "65b9652fc218",
        "3ae3c899b99a",
        "17b1974d0918",
        "c78f9b436833",
        "phase7_exception_fields",
        "r2_00a_schema_convergence",
        "r2_02a_idempotency_state",
        HEAD_REVISION,
    ),
)
def test_each_supported_revision_matches_its_known_schema(
    tmp_path: Path,
    revision: str,
):
    database = tmp_path / f"{revision}.db"
    _upgrade(database, revision)

    result = classify_sqlite(database)

    assert result.kind is SchemaKind.ALEMBIC_MANAGED
    assert result.revision == revision


def test_adoption_removes_target_when_post_stamp_validation_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    source = tmp_path / "post-stamp-source.db"
    target = tmp_path / "post-stamp-target.db"
    import_all_models()
    engine = create_engine(sqlite_database_url(source))
    try:
        Base.metadata.create_all(engine)
    finally:
        engine.dispose()
    source_hash = file_sha256(source)

    import utils.schema_management as schema_management

    original_classify = schema_management.classify_sqlite

    def fail_target_validation(path: Path):
        if path.resolve() == target.resolve():
            return schema_management.SchemaClassification(
                SchemaKind.UNKNOWN,
                reason="injected post-stamp validation failure",
            )
        return original_classify(path)

    monkeypatch.setattr(
        schema_management,
        "classify_sqlite",
        fail_target_validation,
    )

    with pytest.raises(RuntimeError, match="未进入 Alembic managed"):
        adopt_known_mixed_sqlite(source, target)

    assert not target.exists()
    assert file_sha256(source) == source_hash
