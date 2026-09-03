"""Server-side write-path invariants after k6 idempotency/confirm scenarios."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from config.database import SessionLocal
from models.global_schedule import GlobalSchedule
from models.idempotency_record import IdempotencyRecord
from models.node import Node
from models.outbox_event import OutboxEvent
from models.package import Package
from models.storage_center import StorageCenter


PROCESSING_STATUSES = frozenset({"PROCESSING", "processing"})


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def check_idempotency(
    db: Session,
    *,
    node_name_prefix: str = "k6-node-",
) -> dict[str, Any]:
    nodes = list(db.scalars(select(Node).where(Node.name.like(f"{node_name_prefix}%"))).all())
    node_codes = [node.node_code for node in nodes]
    duplicate_nodes = sorted({code for code in node_codes if node_codes.count(code) > 1})
    # Stored keys are SHA-256 fingerprints, not the caller-provided idem- prefix.
    records = list(db.scalars(select(IdempotencyRecord)).all())
    processing = [row.idempotency_key for row in records if row.status in PROCESSING_STATUSES]
    succeeded = [row for row in records if row.status == "SUCCEEDED"]
    payload_groups: dict[tuple[str, str | None], int] = {}
    for row in succeeded:
        key = (row.idempotency_key, row.payload_hash)
        payload_groups[key] = payload_groups.get(key, 0) + 1
    duplicate_records = [key for key, count in payload_groups.items() if count > 1]
    storage_ids = {node.id for node in nodes}
    storage_count = 0
    if storage_ids:
        storage_count = db.scalar(
            select(func.count()).select_from(StorageCenter).where(StorageCenter.node_id.in_(storage_ids))
        ) or 0
    failures: list[str] = []
    if duplicate_nodes:
        failures.append(f"duplicate node_code values: {duplicate_nodes}")
    if processing:
        failures.append(f"leftover PROCESSING idempotency records: {len(processing)}")
    if duplicate_records:
        failures.append("duplicate succeeded idempotency records for the same key/payload")
    if nodes and storage_count != len(nodes):
        failures.append(
            f"storage_center rows {storage_count} != k6 nodes {len(nodes)}"
        )
    return {
        "node_count": len(nodes),
        "unique_node_codes": len(set(node_codes)),
        "storage_center_count": int(storage_count),
        "idempotency_record_count": len(records),
        "processing_count": len(processing),
        "duplicate_node_codes": duplicate_nodes,
        "passed": not failures,
        "failures": failures,
    }


def check_confirm(
    db: Session,
    *,
    schedule_code: str | None = None,
    started_at: datetime | None = None,
) -> dict[str, Any]:
    query = select(GlobalSchedule)
    if schedule_code:
        query = query.where(GlobalSchedule.schedule_code == schedule_code)
    elif started_at is not None:
        query = query.where(GlobalSchedule.created_at >= started_at)
        query = query.order_by(GlobalSchedule.created_at.desc())
    else:
        query = query.order_by(GlobalSchedule.created_at.desc())
    schedules = list(db.scalars(query).all())
    failures: list[str] = []
    target = None
    if schedule_code:
        target = schedules[0] if schedules else None
        if target is None:
            failures.append(f"schedule {schedule_code} not found")
    else:
        created = [row for row in schedules if started_at is None or (row.created_at and row.created_at >= started_at)]
        drafts_or_active = [row for row in created if row.status in {"draft", "active"}]
        if not drafts_or_active:
            failures.append("no confirm-conflict target schedule found")
        else:
            target = drafts_or_active[0]
    package_count = 0
    if target is not None:
        package_count = db.scalar(
            select(func.count()).select_from(Package).where(Package.schedule_id == target.id)
        ) or 0
        if target.status != "active":
            failures.append(
                f"schedule {target.schedule_code} status is {target.status}, expected active"
            )
        goods = target.goods_schedules if isinstance(target.goods_schedules, list) else []
        if goods and package_count > len(goods):
            failures.append(
                f"package count {package_count} exceeds goods_schedules {len(goods)}"
            )
    return {
        "schedule_code": None if target is None else target.schedule_code,
        "status": None if target is None else target.status,
        "version": None if target is None else target.version,
        "package_count": int(package_count),
        "passed": not failures,
        "failures": failures,
    }


def check_outbox(db: Session) -> dict[str, Any]:
    processing = db.scalar(
        select(func.count()).select_from(OutboxEvent).where(OutboxEvent.status == "processing")
    ) or 0
    total = db.scalar(select(func.count()).select_from(OutboxEvent)) or 0
    failures: list[str] = []
    if processing:
        failures.append(f"leftover PROCESSING outbox events: {processing}")
    return {
        "outbox_total": int(total),
        "processing_count": int(processing),
        "passed": not failures,
        "failures": failures,
    }


def run_checks(
    db: Session,
    *,
    schedule_code: str | None = None,
    started_at: datetime | None = None,
) -> dict[str, Any]:
    idem = check_idempotency(db)
    confirm = check_confirm(db, schedule_code=schedule_code, started_at=started_at)
    outbox = check_outbox(db)
    failures = list(idem["failures"]) + list(confirm["failures"]) + list(outbox["failures"])
    return {
        "idempotency": idem,
        "confirm": confirm,
        "outbox": outbox,
        "passed": not failures,
        "failures": failures,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check write-path database invariants")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--schedule-code")
    parser.add_argument("--started-at", help="ISO timestamp; schedules created after this are in scope")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    started_at = None
    if args.started_at:
        started_at = datetime.fromisoformat(args.started_at.replace("Z", "+00:00")).replace(tzinfo=None)
    db = SessionLocal()
    try:
        report = run_checks(db, schedule_code=args.schedule_code, started_at=started_at)
    finally:
        db.close()
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    sys.stdout.write(encoded)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
