"""SQLite schema 分类、校验与受控采用工具。"""

from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
import shutil
import sqlite3
from tempfile import TemporaryDirectory

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.util import CommandError
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import URL

from config.database_url import engine_connect_args
from models.base import Base
from models.registry import import_all_models


BACKEND_ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_INI = BACKEND_ROOT / "alembic.ini"


class SchemaKind(StrEnum):
    FRESH = "fresh"
    ALEMBIC_MANAGED = "alembic_managed"
    KNOWN_MIXED = "known_mixed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class SchemaClassification:
    kind: SchemaKind
    revision: str | None = None
    reason: str | None = None


def sqlite_database_url(path: Path) -> str:
    """为绝对文件路径生成跨平台 SQLite URL。"""
    return URL.create("sqlite", database=str(path.resolve())).render_as_string(
        hide_password=False
    )


def file_sha256(path: Path) -> str:
    """计算迁移证据所需的文件 SHA-256。"""
    digest = sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _snapshot_sqlite(source: Path, target: Path) -> None:
    """通过 SQLite backup API 生成一致副本，包含已提交的 WAL 数据。"""
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with closing(
            sqlite3.connect(
                f"file:{source.resolve().as_posix()}?mode=ro",
                uri=True,
            )
        ) as source_connection:
            with closing(sqlite3.connect(target)) as target_connection:
                source_connection.backup(target_connection)
    except Exception as exc:
        try:
            _remove_sqlite_files(target)
        except OSError as cleanup_exc:
            exc.add_note(f"清理失败的 SQLite 目标时发生错误：{cleanup_exc}")
        raise


def _remove_sqlite_files(path: Path) -> None:
    """清理失败目标及其 SQLite journal/WAL sidecar。"""
    for candidate in (
        path,
        Path(f"{path}-wal"),
        Path(f"{path}-shm"),
        Path(f"{path}-journal"),
    ):
        candidate.unlink(missing_ok=True)


def _verified_source_snapshot(source: Path) -> tuple[str, Path, TemporaryDirectory[str]]:
    """创建只读一致快照，并确认分类期间源数据库未发生变化。"""
    directory = TemporaryDirectory(prefix="logistics-sqlite-snapshot-")
    snapshot = Path(directory.name) / source.name
    try:
        _snapshot_sqlite(source, snapshot)
        snapshot_hash = file_sha256(snapshot)
        verification = Path(directory.name) / f"verify-{source.name}"
        _snapshot_sqlite(source, verification)
        if file_sha256(verification) != snapshot_hash:
            raise RuntimeError("分类期间源 SQLite 发生变化，请停止写入后重试")
        verification.unlink(missing_ok=True)
    except Exception:
        directory.cleanup()
        raise
    return snapshot_hash, snapshot, directory


def alembic_config(database_url: str) -> Config:
    """构造显式绑定数据库 URL 的 Alembic 配置。"""
    config = Config(str(ALEMBIC_INI))
    config.attributes["database_url"] = database_url
    return config


def _metadata_differences(database_url: str) -> list[object]:
    import_all_models()
    engine = create_engine(
        database_url,
        connect_args=engine_connect_args(database_url),
    )
    try:
        with engine.connect() as connection:
            context = MigrationContext.configure(
                connection,
                opts={
                    "compare_type": True,
                    "compare_server_default": True,
                },
            )
            return compare_metadata(context, Base.metadata)
    finally:
        engine.dispose()


def _schema_signature(database_url: str, *, ignore_phase7_legacy: bool = False) -> dict[str, object]:
    """生成与数据和 SQLite 自动索引名称无关的 schema 签名。"""
    engine = create_engine(
        database_url,
        connect_args=engine_connect_args(database_url),
    )
    try:
        inspector = inspect(engine)
        signature: dict[str, object] = {}
        for table_name in sorted(inspector.get_table_names()):
            ignored_columns = (
                {
                    "trigger_node_id",
                    "related_route_id",
                    "severity",
                    "resolution_note",
                }
                if ignore_phase7_legacy and table_name == "exception_events"
                else set()
            )
            columns = tuple(
                sorted(
                    (
                        column["name"],
                        str(column["type"]).upper(),
                        bool(column.get("nullable", True)),
                        column.get("default"),
                        int(column.get("primary_key", 0)),
                    )
                    for column in inspector.get_columns(table_name)
                    if column["name"] not in ignored_columns
                )
            )
            primary_key = tuple(
                column
                for column in (
                    inspector.get_pk_constraint(table_name).get(
                        "constrained_columns"
                    )
                    or ()
                )
                if column not in ignored_columns
            )
            foreign_keys = tuple(
                sorted(
                    (
                        tuple(foreign_key.get("constrained_columns") or ()),
                        foreign_key.get("referred_table"),
                        tuple(foreign_key.get("referred_columns") or ()),
                        tuple(sorted((foreign_key.get("options") or {}).items())),
                    )
                    for foreign_key in inspector.get_foreign_keys(table_name)
                    if not (set(foreign_key.get("constrained_columns") or ()) & ignored_columns)
                )
            )
            unique_constraints = tuple(
                sorted(
                    tuple(constraint.get("column_names") or ())
                    for constraint in inspector.get_unique_constraints(table_name)
                    if not (set(constraint.get("column_names") or ()) & ignored_columns)
                )
            )
            indexes = tuple(
                sorted(
                    (
                        index.get("name"),
                        tuple(index.get("column_names") or ()),
                        bool(index.get("unique", False)),
                    )
                    for index in inspector.get_indexes(table_name)
                    if not (set(index.get("column_names") or ()) & ignored_columns)
                )
            )
            check_constraints = tuple(
                sorted(
                    (
                        constraint.get("name"),
                        constraint.get("sqltext"),
                    )
                    for constraint in inspector.get_check_constraints(table_name)
                )
            )
            signature[table_name] = (
                columns,
                primary_key,
                foreign_keys,
                unique_constraints,
                indexes,
                check_constraints,
            )
        with engine.connect() as connection:
            schema_objects = tuple(
                connection.exec_driver_sql(
                    "SELECT type, name, tbl_name, sql FROM sqlite_master "
                    "WHERE type IN ('trigger', 'view') ORDER BY type, name"
                ).fetchall()
            )
        signature["__schema_objects__"] = schema_objects
        return signature
    finally:
        engine.dispose()


def _matches_revision_schema(path: Path, revision: str) -> bool:
    """仅接受与该 revision 已知结构一致的 Alembic managed schema。"""
    with TemporaryDirectory(prefix="logistics-revision-reference-") as directory:
        reference = Path(directory) / "reference.db"
        reference_url = sqlite_database_url(reference)
        command.upgrade(alembic_config(reference_url), revision)
        ignore_phase7_legacy = revision == "phase7_exception_fields"
        return _schema_signature(
            sqlite_database_url(path),
            ignore_phase7_legacy=ignore_phase7_legacy,
        ) == _schema_signature(reference_url)


def _unsafe_legacy_exception_reason(engine, tables: set[str]) -> str | None:
    """识别不能自动丢弃的历史异常事件数据。"""
    if "exception_events" not in tables:
        return None

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("exception_events")}
    legacy_columns = columns & {
        "trigger_node_id",
        "related_route_id",
        "severity",
        "resolution_note",
    }
    if not legacy_columns:
        return None

    populated = []
    with engine.connect() as connection:
        for column_name in sorted(legacy_columns):
            row = connection.exec_driver_sql(
                f'SELECT 1 FROM "exception_events" '
                f'WHERE "{column_name}" IS NOT NULL LIMIT 1'
            ).first()
            if row is not None:
                populated.append(column_name)
    if not populated:
        return None

    return (
        "历史 exception_events 遗留列含数据，需人工映射/归档："
        + ", ".join(populated)
    )


def _classify_sqlite_snapshot(path: Path) -> SchemaClassification:
    """分类一致快照中的 SQLite schema；不识别的结构一律 fail closed。"""
    if not path.exists():
        return SchemaClassification(SchemaKind.FRESH)
    if not path.is_file():
        return SchemaClassification(
            SchemaKind.UNKNOWN,
            reason="目标不是普通文件",
        )

    database_url = sqlite_database_url(path)
    engine = create_engine(
        database_url,
        connect_args=engine_connect_args(database_url),
    )
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        user_tables = tables - {"alembic_version"}
        if not user_tables:
            return SchemaClassification(SchemaKind.FRESH)

        if "alembic_version" in tables:
            with engine.connect() as connection:
                rows = connection.exec_driver_sql(
                    "SELECT version_num FROM alembic_version"
                ).fetchall()
            if len(rows) != 1:
                return SchemaClassification(
                    SchemaKind.UNKNOWN,
                    reason="alembic_version 必须且只能包含一行",
                )
            revision = rows[0][0]
            script = ScriptDirectory.from_config(alembic_config(database_url))
            try:
                known_revision = script.get_revision(revision)
            except CommandError:
                known_revision = None
            if known_revision is None:
                return SchemaClassification(
                    SchemaKind.UNKNOWN,
                    revision=revision,
                    reason="数据库 revision 不属于当前迁移图",
                )
            unsafe_reason = _unsafe_legacy_exception_reason(engine, tables)
            if unsafe_reason is not None:
                return SchemaClassification(
                    SchemaKind.UNKNOWN,
                    revision=revision,
                    reason=unsafe_reason,
                )
            if not _matches_revision_schema(path, revision):
                return SchemaClassification(
                    SchemaKind.UNKNOWN,
                    revision=revision,
                    reason="schema 与已登记 revision 的已知结构不一致",
                )
            return SchemaClassification(
                SchemaKind.ALEMBIC_MANAGED,
                revision=revision,
            )
    finally:
        engine.dispose()

    differences = _metadata_differences(database_url)
    schema_objects = _schema_signature(database_url).get("__schema_objects__")
    if not differences and not schema_objects:
        return SchemaClassification(SchemaKind.KNOWN_MIXED)
    return SchemaClassification(
        SchemaKind.UNKNOWN,
        reason=f"未版本化 schema 与 ORM 存在 {len(differences)} 项差异",
    )


def classify_sqlite(path: Path) -> SchemaClassification:
    """通过 SQLite backup API 的一致快照分类，避免恢复/WAL checkpoint 源库。"""
    if not path.exists():
        sidecars = tuple(
            candidate
            for candidate in (
                Path(f"{path}-wal"),
                Path(f"{path}-shm"),
                Path(f"{path}-journal"),
            )
            if candidate.exists()
        )
        if sidecars:
            return SchemaClassification(
                SchemaKind.UNKNOWN,
                reason="主 SQLite 文件不存在，但检测到孤立 journal/WAL sidecar",
            )
        return SchemaClassification(SchemaKind.FRESH)
    if not path.is_file():
        return SchemaClassification(
            SchemaKind.UNKNOWN,
            reason="目标不是普通文件",
        )

    _, snapshot, snapshot_directory = _verified_source_snapshot(path)
    try:
        return _classify_sqlite_snapshot(snapshot)
    finally:
        snapshot_directory.cleanup()


def adopt_known_mixed_sqlite(source: Path, target: Path) -> SchemaClassification:
    """复制并采用与当前 ORM 完全一致的未版本化 SQLite，保留原文件不变。"""
    if source.resolve() == target.resolve():
        raise ValueError("采用目标必须与源 SQLite 文件不同")
    if target.exists():
        raise FileExistsError(f"采用目标已存在：{target}")

    source_snapshot_hash, snapshot, snapshot_directory = _verified_source_snapshot(
        source
    )
    try:
        classification = classify_sqlite(snapshot)
        if classification.kind is not SchemaKind.KNOWN_MIXED:
            raise ValueError(
                f"仅允许采用 known_mixed schema，实际为 {classification.kind.value}: "
                f"{classification.reason or '-'}"
            )

        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(snapshot, target)
        try:
            if file_sha256(target) != source_snapshot_hash:
                raise RuntimeError("复制后的 SQLite 快照哈希不一致")

            target_url = sqlite_database_url(target)
            if _metadata_differences(target_url):
                raise RuntimeError("复制后的 schema parity 校验失败，未执行 stamp")

            command.stamp(alembic_config(target_url), "head")
            result = classify_sqlite(target)
            if result.kind is not SchemaKind.ALEMBIC_MANAGED:
                raise RuntimeError("采用后数据库未进入 Alembic managed 状态")

            verification = Path(snapshot_directory.name) / f"final-{source.name}"
            _snapshot_sqlite(source, verification)
            if file_sha256(verification) != source_snapshot_hash:
                raise RuntimeError("采用过程中原始 SQLite 发生变化，请停止写入后重试")
            return result
        except Exception as exc:
            try:
                _remove_sqlite_files(target)
            except OSError as cleanup_exc:
                exc.add_note(f"清理失败的 SQLite 目标时发生错误：{cleanup_exc}")
            raise
    finally:
        snapshot_directory.cleanup()


def migrate_managed_sqlite_copy(
    source: Path,
    target: Path,
) -> SchemaClassification:
    """复制合法 Alembic 旧库并在副本上升级，原文件始终保持不变。"""
    if source.resolve() == target.resolve():
        raise ValueError("迁移目标必须与源 SQLite 文件不同")
    if target.exists():
        raise FileExistsError(f"迁移目标已存在：{target}")

    source_snapshot_hash, snapshot, snapshot_directory = _verified_source_snapshot(
        source
    )
    try:
        classification = classify_sqlite(snapshot)
        if classification.kind is not SchemaKind.ALEMBIC_MANAGED:
            raise ValueError(
                "仅允许升级 alembic_managed schema，"
                f"实际为 {classification.kind.value}: {classification.reason or '-'}"
            )

        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(snapshot, target)
        try:
            if file_sha256(target) != source_snapshot_hash:
                raise RuntimeError("复制后的 SQLite 快照哈希不一致")

            target_url = sqlite_database_url(target)
            command.upgrade(alembic_config(target_url), "head")
            differences = _metadata_differences(target_url)
            if differences:
                raise RuntimeError(
                    f"升级后的 schema parity 校验失败，共 {len(differences)} 项差异"
                )
            result = classify_sqlite(target)
            if result.kind is not SchemaKind.ALEMBIC_MANAGED:
                raise RuntimeError("升级后的数据库未进入 Alembic managed 状态")

            verification = Path(snapshot_directory.name) / f"final-{source.name}"
            _snapshot_sqlite(source, verification)
            if file_sha256(verification) != source_snapshot_hash:
                raise RuntimeError("升级过程中原始 SQLite 发生变化，请停止写入后重试")
            return result
        except Exception as exc:
            try:
                _remove_sqlite_files(target)
            except OSError as cleanup_exc:
                exc.add_note(f"清理失败的 SQLite 目标时发生错误：{cleanup_exc}")
            raise
    finally:
        snapshot_directory.cleanup()


__all__ = [
    "SchemaClassification",
    "SchemaKind",
    "adopt_known_mixed_sqlite",
    "alembic_config",
    "classify_sqlite",
    "file_sha256",
    "migrate_managed_sqlite_copy",
    "sqlite_database_url",
]
