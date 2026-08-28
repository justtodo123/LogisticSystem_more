"""业务编号号段条件更新。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.error_codes import (
    CODE_CODE_ALLOCATION_CONFLICT,
    CODE_CODE_RANGE_EXHAUSTED,
)
from core.errors import DomainError
from models.code_range import CodeRange


RESOURCE_GLOBAL_SCHEDULE = "global_schedule"
RESOURCE_PACKAGE = "package"
RESOURCE_ROUTE = "route"
RESOURCE_DISPATCH_BATCH = "dispatch_batch"
RESOURCE_NODE_DISPATCH = "node_dispatch"

MAX_CLAIM_RETRIES = 32
MAX_UNIQUE_RETRIES = 8


@dataclass(frozen=True, slots=True)
class CodeResource:
    name: str
    prefix_stem: str
    width: int
    model: type
    column: str


_SPECS: dict[str, CodeResource] | None = None


def _resource_specs() -> dict[str, CodeResource]:
    global _SPECS
    if _SPECS is None:
        from models.dispatch_batch import DispatchBatch
        from models.global_schedule import GlobalSchedule
        from models.node_dispatch import NodeDispatch
        from models.package import Package
        from models.route import Route

        specs = (
            CodeResource(
                RESOURCE_GLOBAL_SCHEDULE, "GS", 3, GlobalSchedule, "schedule_code"
            ),
            CodeResource(RESOURCE_PACKAGE, "PKG", 4, Package, "package_code"),
            CodeResource(RESOURCE_ROUTE, "ROUTE", 3, Route, "route_code"),
            CodeResource(
                RESOURCE_DISPATCH_BATCH, "BATCH", 3, DispatchBatch, "batch_code"
            ),
            CodeResource(
                RESOURCE_NODE_DISPATCH, "DISP", 3, NodeDispatch, "dispatch_code"
            ),
        )
        _SPECS = {spec.name: spec for spec in specs}
    return _SPECS


def get_resource(resource: str) -> CodeResource:
    try:
        return _resource_specs()[resource]
    except KeyError as exc:
        raise ValueError(f"未知编号资源: {resource}") from exc


def prefix_for(spec: CodeResource, now: datetime | None = None) -> str:
    day = (now or datetime.now()).strftime("%Y%m%d")
    return f"{spec.prefix_stem}{day}"


def max_seq_for(width: int) -> int:
    return 10 ** width - 1


def format_code(prefix: str, seq: int, width: int) -> str:
    return f"{prefix}{seq:0{width}d}"


def parse_seq(code: str, prefix: str) -> int | None:
    if not code.startswith(prefix):
        return None
    suffix = code[len(prefix):]
    if not suffix.isdigit():
        return None
    return int(suffix)


def seed_next_value(db: Session, spec: CodeResource, prefix: str) -> int:
    """仅在号段行不存在时扫描已有编码，确定起始 next_value。"""
    column = getattr(spec.model, spec.column)
    max_record = (
        db.query(column)
        .filter(column.like(f"{prefix}%"))
        .order_by(column.desc())
        .first()
    )
    if not max_record or not max_record[0]:
        return 1
    seq = parse_seq(max_record[0], prefix)
    if seq is None:
        return 1
    return seq + 1


def _code_taken(db: Session, spec: CodeResource, code: str) -> bool:
    column = getattr(spec.model, spec.column)
    if db.query(spec.model).filter(column == code).first() is not None:
        return True
    for obj in db.new:
        if isinstance(obj, spec.model) and getattr(obj, spec.column, None) == code:
            return True
    return False


def _read_next_value(db: Session, resource: str, prefix: str) -> int | None:
    value = db.execute(
        select(CodeRange.next_value).where(
            CodeRange.resource == resource,
            CodeRange.prefix == prefix,
        )
    ).scalar_one_or_none()
    return int(value) if value is not None else None


def _insert_range(db: Session, spec: CodeResource, prefix: str, next_value: int) -> None:
    try:
        with db.begin_nested():
            db.execute(
                insert(CodeRange).values(
                    resource=spec.name,
                    prefix=prefix,
                    next_value=next_value,
                    width=spec.width,
                )
            )
    except IntegrityError:
        return


def _claim_next_value(db: Session, spec: CodeResource, prefix: str) -> int:
    max_seq = max_seq_for(spec.width)
    for _ in range(MAX_CLAIM_RETRIES):
        current = _read_next_value(db, spec.name, prefix)
        if current is None:
            seed = seed_next_value(db, spec, prefix)
            if seed > max_seq:
                raise DomainError(CODE_CODE_RANGE_EXHAUSTED)
            _insert_range(db, spec, prefix, seed)
            continue
        if current > max_seq:
            raise DomainError(CODE_CODE_RANGE_EXHAUSTED)
        result = db.execute(
            update(CodeRange)
            .where(
                CodeRange.resource == spec.name,
                CodeRange.prefix == prefix,
                CodeRange.next_value == current,
            )
            .values(next_value=current + 1)
            .execution_options(synchronize_session=False)
        )
        if result.rowcount == 1:
            return current
    raise DomainError(CODE_CODE_ALLOCATION_CONFLICT)


def allocate_code(db: Session, resource: str, *, now: datetime | None = None) -> str:
    """从号段表条件更新抢下一个业务编号。"""
    spec = get_resource(resource)
    prefix = prefix_for(spec, now)
    for _ in range(MAX_UNIQUE_RETRIES):
        seq = _claim_next_value(db, spec, prefix)
        code = format_code(prefix, seq, spec.width)
        if not _code_taken(db, spec, code):
            return code
    raise DomainError(CODE_CODE_ALLOCATION_CONFLICT)