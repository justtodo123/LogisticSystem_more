"""Dump a dedicated synthetic slice and restore it into another Postgres database."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from config.database_url import engine_create_kwargs, resolve_database_url
from core.code_allocation import RESOURCE_GLOBAL_SCHEDULE, allocate_code
from models.code_range import CodeRange
from models.global_schedule import GlobalSchedule
from models.idempotency_record import IdempotencyRecord
from models.outbox_event import OutboxEvent
from services.outbox_service import enqueue_outbox
from utils.idempotency_store import STATUS_SUCCEEDED


BACKEND_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ARTIFACTS = BACKEND_ROOT / "p1-artifacts"


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, text=True, **kwargs)


def docker_id(image_prefix: str) -> str:
    result = run(["docker", "ps", "--format", "{{.ID}} {{.Image}}"], capture_output=True)
    for line in result.stdout.splitlines():
        container_id, image = line.split(" ", 1)
        if image.startswith(image_prefix):
            return container_id
    raise SystemExit(f"no running container for {image_prefix}")


def make_factory(url: str):
    resolved = resolve_database_url(url)
    engine = create_engine(resolved, **engine_create_kwargs(resolved))
    return engine, sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _schedule(code: str) -> GlobalSchedule:
    return GlobalSchedule(
        schedule_code=code,
        order_codes=["P1-BACKUP"],
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", default=str(DEFAULT_ARTIFACTS))
    parser.add_argument("--restore-db", default="logistics_restore")
    args = parser.parse_args()
    artifacts = Path(args.artifacts)
    artifacts.mkdir(parents=True, exist_ok=True)
    source_url = os.environ.get("DATABASE_URL", "")
    if not source_url:
        raise SystemExit("DATABASE_URL is required")

    postgres_id = docker_id("postgres:16-alpine")
    suffix = uuid4().hex[:12]
    now = datetime(2099, 6, 1)
    engine, factory = make_factory(source_url)
    session = factory()
    try:
        code = allocate_code(session, RESOURCE_GLOBAL_SCHEDULE, now=now)
        session.add(_schedule(code))
        session.add(
            IdempotencyRecord(
                idempotency_key=f"p1-backup-{suffix}",
                payload_hash="synthetic",
                status=STATUS_SUCCEEDED,
                expires_at=datetime.utcnow() + timedelta(days=1),
            )
        )
        enqueue_outbox(
            session,
            dedup_key=f"p1-backup-outbox-{suffix}",
            event_type="p1.backup",
            payload={"code": code},
        )
        session.commit()
        source_code = code
    finally:
        session.close()

    dump_path = artifacts / "pg-backup.sql"
    with dump_path.open("w", encoding="utf-8") as handle:
        run(
            [
                "docker",
                "exec",
                postgres_id,
                "pg_dump",
                "-U",
                "logistics",
                "-d",
                "logistics",
            ],
            stdout=handle,
        )

    run(
        [
            "docker",
            "exec",
            "-e",
            "PGPASSWORD=logistics",
            postgres_id,
            "psql",
            "-U",
            "logistics",
            "-d",
            "postgres",
            "-c",
            f"DROP DATABASE IF EXISTS {args.restore_db};",
        ]
    )
    run(
        [
            "docker",
            "exec",
            "-e",
            "PGPASSWORD=logistics",
            postgres_id,
            "psql",
            "-U",
            "logistics",
            "-d",
            "postgres",
            "-c",
            f"CREATE DATABASE {args.restore_db} OWNER logistics;",
        ]
    )
    run(
        [
            "docker",
            "exec",
            "-i",
            postgres_id,
            "psql",
            "-U",
            "logistics",
            "-d",
            args.restore_db,
        ],
        input=dump_path.read_text(encoding="utf-8"),
    )

    restore_url = source_url.rsplit("/", 1)[0] + f"/{args.restore_db}"
    restore_engine, restore_factory = make_factory(restore_url)
    restore = restore_factory()
    try:
        version = restore.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        restored_code = restore.scalar(
            select(GlobalSchedule.schedule_code).where(GlobalSchedule.schedule_code == source_code)
        )
        restored_idem = restore.scalar(
            select(IdempotencyRecord.idempotency_key).where(
                IdempotencyRecord.idempotency_key == f"p1-backup-{suffix}"
            )
        )
        restored_outbox = restore.scalar(
            select(OutboxEvent.dedup_key).where(
                OutboxEvent.dedup_key == f"p1-backup-outbox-{suffix}"
            )
        )
        if not restored_code or not restored_idem or not restored_outbox:
            raise SystemExit("restored database is missing synthetic rows")
        next_code = allocate_code(restore, RESOURCE_GLOBAL_SCHEDULE, now=now)
        restore.add(_schedule(next_code))
        restore.commit()
        if next_code == source_code:
            raise SystemExit("restored allocation reused dumped code")
    finally:
        restore.close()
        restore_engine.dispose()
        engine.dispose()

    summary = artifacts / "backup-restore-summary.txt"
    lines = [
        f"source_code={source_code}",
        f"restore_db={args.restore_db}",
        f"alembic_version={version}",
        f"restored_code={restored_code}",
        f"next_code_after_restore={next_code}",
        f"dump_bytes={dump_path.stat().st_size}",
        "data=synthetic",
        "scope=dedicated-temp-database",
    ]
    summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
