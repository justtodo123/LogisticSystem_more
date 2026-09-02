"""Optional large code-range CAS; skipped unless P1_CODE_SCALE is set.

Production global_schedule codes are width=3 (max 999). This job therefore
measures unique, contiguous claims on a dedicated CodeRange row rather than
changing production width.
"""
import math
import os
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from uuid import uuid4

import pytest
from sqlalchemy import select, update

from models.code_range import CodeRange


@pytest.mark.integration
def test_postgres_code_range_scale(p1_postgres, p1_row_cleanup):
    scale = int(os.environ.get("P1_CODE_SCALE", "0") or "0")
    if scale < 1:
        pytest.skip("set P1_CODE_SCALE to run the optional allocation scale test")
    workers = int(os.environ.get("P1_CODE_SCALE_WORKERS", "8") or "8")

    _engine, factory = p1_postgres
    prefix = f"P1S{uuid4().hex[:10]}"
    seed = factory()
    try:
        seed.add(
            CodeRange(
                resource="p1_scale",
                prefix=prefix,
                next_value=1,
                width=6,
            )
        )
        seed.commit()
    finally:
        seed.close()
    p1_row_cleanup(
        CodeRange,
        filters={
            CodeRange: (CodeRange.resource == "p1_scale") & (CodeRange.prefix == prefix)
        },
    )

    claimed: list[int] = []
    latencies: list[float] = []
    lock = Lock()

    def claim_one() -> None:
        started_one = time.perf_counter()
        session = factory()
        try:
            for attempt in range(128):
                current = session.execute(
                    select(CodeRange.next_value).where(
                        CodeRange.resource == "p1_scale",
                        CodeRange.prefix == prefix,
                    )
                ).scalar_one()
                result = session.execute(
                    update(CodeRange)
                    .where(
                        CodeRange.resource == "p1_scale",
                        CodeRange.prefix == prefix,
                        CodeRange.next_value == current,
                    )
                    .values(next_value=current + 1)
                )
                if result.rowcount == 1:
                    session.commit()
                    with lock:
                        claimed.append(current)
                        latencies.append(time.perf_counter() - started_one)
                    return
                session.rollback()
                time.sleep(min(0.001 * (2**min(attempt, 5)), 0.02))
            raise AssertionError("failed to claim a code after 128 retries")
        finally:
            session.close()

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(lambda _: claim_one(), range(scale)))
    elapsed = time.perf_counter() - started

    assert len(claimed) == scale
    assert len(set(claimed)) == scale
    assert sorted(claimed) == list(range(1, scale + 1))

    resumed = factory()
    try:
        current = resumed.execute(
            select(CodeRange.next_value).where(
                CodeRange.resource == "p1_scale",
                CodeRange.prefix == prefix,
            )
        ).scalar_one()
        result = resumed.execute(
            update(CodeRange)
            .where(
                CodeRange.resource == "p1_scale",
                CodeRange.prefix == prefix,
                CodeRange.next_value == current,
            )
            .values(next_value=current + 1)
        )
        assert result.rowcount == 1
        resumed.commit()
        assert current == scale + 1
    finally:
        resumed.close()

    sorted_latencies = sorted(latencies)

    def percentile(value: float) -> float:
        index = max(0, math.ceil(value * len(sorted_latencies)) - 1)
        return sorted_latencies[index]

    print(
        "code_scale="
        f"{scale} workers={workers} unique={len(set(claimed))} "
        f"contiguous=1..{scale} resume_next={scale + 1} elapsed_s={elapsed:.3f} "
        f"throughput_per_s={scale / elapsed:.1f} "
        f"p95_ms={percentile(0.95) * 1000:.3f} "
        f"p99_ms={percentile(0.99) * 1000:.3f}",
        flush=True,
    )
