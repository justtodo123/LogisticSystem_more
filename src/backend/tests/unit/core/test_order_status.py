"""Order six-state contract: mapping, unknown values, frontend drift."""
from __future__ import annotations

import re
from pathlib import Path

from core.order_status import (
    HISTORICAL_ORDER_STATUS_MAP,
    ORDER_STATUSES,
    apply_order_status_backfill,
    is_known_order_status,
    map_historical_order_status,
    plan_order_status_backfill,
    unknown_order_status_message,
)
from services.state_machine import ORDER_TRANSITIONS


FRONTEND_SRC = Path(__file__).resolve().parents[4] / "frontend" / "src"


def test_order_statuses_match_state_machine():
    assert tuple(ORDER_TRANSITIONS) == ORDER_STATUSES
    assert set(ORDER_TRANSITIONS) == set(ORDER_STATUSES)


def test_historical_mapping_is_explicit_and_unambiguous():
    assert HISTORICAL_ORDER_STATUS_MAP == {
        "pending": "unassigned",
        "delivering": "in_transit",
        "completed": "signed",
    }
    assert map_historical_order_status("pending") == "unassigned"
    assert map_historical_order_status("delivering") == "in_transit"
    assert map_historical_order_status("completed") == "signed"
    assert HISTORICAL_ORDER_STATUS_MAP["completed"] != "closed"


def test_unknown_status_is_not_silently_mapped():
    assert map_historical_order_status("mystery") == "mystery"
    assert not is_known_order_status("pending")
    assert not is_known_order_status("delivering")
    assert not is_known_order_status("completed")
    assert not is_known_order_status("mystery")
    assert "mystery" in unknown_order_status_message("mystery")


def test_backfill_plan_preserves_counts_and_reports_unknown():
    plan = plan_order_status_backfill(
        ["pending", "pending", "delivering", "completed", "unassigned", "weird"]
    )
    assert plan["counts_match"] is True
    assert plan["before_total"] == 6
    assert plan["after_total"] == 6
    assert plan["after"]["unassigned"] == 3
    assert plan["after"]["in_transit"] == 1
    assert plan["after"]["signed"] == 1
    assert plan["leftover_unknown"] == {"weird": 1}
    assert [item["from"] for item in plan["planned"]] == [
        "completed",
        "delivering",
        "pending",
    ]


def test_apply_backfill_is_idempotent():
    rows = [
        {"status": "pending"},
        {"status": "signed"},
        {"status": "legacy-unknown"},
    ]
    first = apply_order_status_backfill(rows)
    assert rows[0]["status"] == "unassigned"
    assert rows[1]["status"] == "signed"
    assert rows[2]["status"] == "legacy-unknown"
    assert first["changed"] == 1
    second = apply_order_status_backfill(rows)
    assert second["changed"] == 0
    assert [row["status"] for row in rows] == [
        "unassigned",
        "signed",
        "legacy-unknown",
    ]


def _extract_string_tuple(source: str, name: str) -> list[str]:
    match = re.search(
        rf"export const {name} = \[([^\]]+)\] as const",
        source,
        re.S,
    )
    assert match, f"{name} not found"
    return re.findall(r"'([^']+)'", match.group(1))


def _extract_object_keys(source: str, name: str) -> list[str]:
    match = re.search(rf"export const {name}[^=]*= \{{(.*?)\n\}}", source, re.S)
    assert match, f"{name} not found"
    return re.findall(r"^\s+([A-Za-z_]+):", match.group(1), re.M)


def test_frontend_order_status_contract_matches_backend():
    order_ts = (FRONTEND_SRC / "types" / "order.ts").read_text(encoding="utf-8")
    status_ts = (FRONTEND_SRC / "constants" / "status.ts").read_text(encoding="utf-8")
    frontend_statuses = _extract_string_tuple(order_ts, "ORDER_STATUSES")
    assert frontend_statuses == list(ORDER_STATUSES)
    map_keys = _extract_object_keys(status_ts, "ORDER_STATUS_MAP")
    assert map_keys == list(ORDER_STATUSES)
    legacy = re.search(
        r"export const LEGACY_ORDER_STATUS_MAP[^=]*= \{([^}]+)\}",
        order_ts,
        re.S,
    )
    assert legacy, "LEGACY_ORDER_STATUS_MAP missing in frontend types"
    frontend_legacy = dict(re.findall(r"(\w+):\s*'(\w+)'", legacy.group(1)))
    assert frontend_legacy == HISTORICAL_ORDER_STATUS_MAP
