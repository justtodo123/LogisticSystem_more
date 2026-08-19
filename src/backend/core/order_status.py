"""Authoritative order-status contract.

Runtime transition edges stay in ``services.state_machine.ORDER_TRANSITIONS``.
This module names the six values, labels, mutability and the historical
four-state backfill map so API, seed, export and tests reuse one source.
"""
from __future__ import annotations

from collections import Counter
from typing import Dict, Iterable, List, MutableMapping, Sequence, Tuple

ORDER_STATUS_CONTRACT_VERSION = "2026-08-19-six-state"

ORDER_UNASSIGNED = "unassigned"
ORDER_ASSIGNED = "assigned"
ORDER_IN_TRANSIT = "in_transit"
ORDER_SIGNED = "signed"
ORDER_EXCEPTION = "exception"
ORDER_CLOSED = "closed"

ORDER_STATUSES: Tuple[str, ...] = (
    ORDER_UNASSIGNED,
    ORDER_ASSIGNED,
    ORDER_IN_TRANSIT,
    ORDER_SIGNED,
    ORDER_EXCEPTION,
    ORDER_CLOSED,
)

ORDER_STATUS_LABELS: Dict[str, str] = {
    ORDER_UNASSIGNED: "待分配",
    ORDER_ASSIGNED: "已分配",
    ORDER_IN_TRANSIT: "运输中",
    ORDER_SIGNED: "已签收",
    ORDER_EXCEPTION: "异常",
    ORDER_CLOSED: "已关闭",
}

# signed = all goods delivered; may still move to exception if a later issue is found.
# closed = cancelled / abandoned without completion; no further transitions.
ORDER_TERMINAL_STATUSES: Tuple[str, ...] = (ORDER_CLOSED,)
ORDER_DELIVERY_COMPLETE_STATUSES: Tuple[str, ...] = (ORDER_SIGNED,)

# Edit / delete before the order has entered transit or a terminal outcome.
ORDER_MUTABLE_STATUSES: Tuple[str, ...] = (ORDER_UNASSIGNED, ORDER_ASSIGNED)
# close_order API currently allows only these two; exception->closed stays a state-machine path.
ORDER_CLOSABLE_STATUSES: Tuple[str, ...] = (ORDER_UNASSIGNED, ORDER_ASSIGNED)
ORDER_SCHEDULABLE_STATUSES: Tuple[str, ...] = (ORDER_UNASSIGNED, ORDER_EXCEPTION)

# Old four-state values. ``completed`` means finished delivery (signed), not cancelled (closed).
HISTORICAL_ORDER_STATUS_MAP: Dict[str, str] = {
    "pending": ORDER_UNASSIGNED,
    "delivering": ORDER_IN_TRANSIT,
    "completed": ORDER_SIGNED,
}

HISTORICAL_MAPPING_NOTES: Dict[str, str] = {
    "completed": (
        "completed historically meant 已完成/签收; "
        "closed is cancellation-only and is not inferred from completed"
    ),
}


def is_known_order_status(value: str | None) -> bool:
    return value in ORDER_STATUSES


def map_historical_order_status(value: str) -> str:
    """Map a known historical value; leave unknown values unchanged."""
    return HISTORICAL_ORDER_STATUS_MAP.get(value, value)


def plan_order_status_backfill(
    current_statuses: Iterable[str],
) -> Dict[str, object]:
    """Build an idempotent backfill plan from observed status values.

    Unknown values are reported, never invented into a legal state.
    """
    counts = Counter(current_statuses)
    planned: List[Dict[str, object]] = []
    leftover_unknown: Dict[str, int] = {}
    after: Counter[str] = Counter()

    for status, count in sorted(counts.items(), key=lambda item: item[0]):
        mapped = map_historical_order_status(status)
        if status in HISTORICAL_ORDER_STATUS_MAP:
            planned.append(
                {
                    "from": status,
                    "to": mapped,
                    "count": count,
                    "note": HISTORICAL_MAPPING_NOTES.get(status, ""),
                }
            )
            after[mapped] += count
        elif is_known_order_status(status):
            after[status] += count
        else:
            leftover_unknown[status] = count
            after[status] += count

    return {
        "version": ORDER_STATUS_CONTRACT_VERSION,
        "before": dict(sorted(counts.items())),
        "after": dict(sorted(after.items())),
        "planned": planned,
        "leftover_unknown": leftover_unknown,
        "before_total": sum(counts.values()),
        "after_total": sum(after.values()),
        "counts_match": sum(counts.values()) == sum(after.values()),
    }


def apply_order_status_backfill(
    rows: Sequence[MutableMapping[str, str]],
    status_key: str = "status",
) -> Dict[str, object]:
    """Apply the historical map in memory. Unknown values stay as-is."""
    before = [row[status_key] for row in rows]
    plan = plan_order_status_backfill(before)
    changed = 0
    for row in rows:
        original = row[status_key]
        mapped = map_historical_order_status(original)
        if mapped != original:
            row[status_key] = mapped
            changed += 1
    plan["changed"] = changed
    return plan


def unknown_order_status_message(value: str) -> str:
    allowed = ", ".join(ORDER_STATUSES)
    return f"未知订单状态 '{value}'，允许值: {allowed}"
