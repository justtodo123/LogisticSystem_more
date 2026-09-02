"""In-process counters for R2-06 core business and HTTP signals."""

from __future__ import annotations

from collections import defaultdict
from threading import Lock
from typing import Any


class MetricsRegistry:
    """Process-local counters. Labels must stay low-cardinality."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._counters: dict[tuple[str, tuple[tuple[str, str], ...]], int] = defaultdict(int)

    def inc(self, name: str, amount: int = 1, **labels: str) -> None:
        key = (name, tuple(sorted((str(k), str(v)) for k, v in labels.items())))
        with self._lock:
            self._counters[key] += amount

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()

    def snapshot(self) -> dict[str, list[dict[str, Any]]]:
        with self._lock:
            grouped: dict[str, list[dict[str, Any]]] = {}
            for (name, labels), value in self._counters.items():
                grouped.setdefault(name, []).append(
                    {"labels": dict(labels), "value": value}
                )
            return grouped

    def total(self, name: str, **labels: str) -> int:
        wanted = tuple(sorted((str(k), str(v)) for k, v in labels.items()))
        with self._lock:
            if labels:
                return int(self._counters.get((name, wanted), 0))
            return sum(
                value for (counter_name, _), value in self._counters.items()
                if counter_name == name
            )

    def render_prometheus(self) -> str:
        lines: list[str] = []
        snapshot = self.snapshot()
        for name in sorted(snapshot):
            for series in snapshot[name]:
                labels = series["labels"]
                if labels:
                    rendered = ",".join(
                        f'{key}="{value}"' for key, value in sorted(labels.items())
                    )
                    lines.append(f"{name}{{{rendered}}} {series['value']}")
                else:
                    lines.append(f"{name} {series['value']}")
        return "\n".join(lines) + ("\n" if lines else "")


metrics = MetricsRegistry()


def observe_http_request(*, method: str, path: str, status: int) -> None:
    metrics.inc(
        "http_requests_total",
        method=method.upper()[:16],
        path=path[:128],
        status=str(status),
    )
    if status >= 400:
        metrics.inc(
            "http_errors_total",
            method=method.upper()[:16],
            path=path[:128],
            status=str(status),
        )


def observe_business_error(code: int) -> None:
    metrics.inc("business_errors_total", code=str(code))
    if code == 40901:
        metrics.inc("confirm_conflicts_total")
    elif code == 40902:
        metrics.inc("idempotency_in_progress_total")
    elif code == 40903:
        metrics.inc("idempotency_mismatch_total")


def observe_idempotency_replay() -> None:
    metrics.inc("idempotency_replay_total")


def observe_cache(*, hit: bool | None = None, degraded: bool = False) -> None:
    if hit is True:
        metrics.inc("cache_hit_total")
    elif hit is False:
        metrics.inc("cache_miss_total")
    if degraded:
        metrics.inc("cache_degraded_total")
