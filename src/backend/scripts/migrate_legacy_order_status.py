"""Idempotent backfill of historical four-state order values.

Usage:
    python scripts/migrate_legacy_order_status.py --dry-run
    python scripts/migrate_legacy_order_status.py
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from sqlalchemy import func

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from config.database import SessionLocal
from core.order_status import (
    HISTORICAL_ORDER_STATUS_MAP,
    plan_order_status_backfill,
)
from models.order import Order


def collect_distribution(db) -> Counter:
    rows = db.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
    return Counter({status: count for status, count in rows})


def migrate(dry_run: bool) -> dict:
    db = SessionLocal()
    try:
        before = collect_distribution(db)
        expanded: list[str] = []
        for status, count in before.items():
            expanded.extend([status] * count)
        plan = plan_order_status_backfill(expanded)
        plan["dry_run"] = dry_run

        if dry_run:
            return plan

        changed = 0
        for old_value, new_value in HISTORICAL_ORDER_STATUS_MAP.items():
            result = (
                db.query(Order)
                .filter(Order.status == old_value)
                .update({Order.status: new_value}, synchronize_session=False)
            )
            changed += result
        db.commit()
        plan["changed"] = changed
        plan["after"] = dict(sorted(collect_distribution(db).items()))
        plan["after_total"] = sum(plan["after"].values())
        plan["counts_match"] = plan["before_total"] == plan["after_total"]
        return plan
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill historical order status values")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned mapping without writing",
    )
    args = parser.parse_args()
    plan = migrate(dry_run=args.dry_run)
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    leftover = plan.get("leftover_unknown") or {}
    if leftover:
        raise SystemExit(f"leftover unknown order statuses: {leftover}")
    if not plan.get("counts_match", True):
        raise SystemExit("migration count mismatch")


if __name__ == "__main__":
    main()
