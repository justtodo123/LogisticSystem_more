"""条件更新抢占（CAS）辅助函数。"""

from collections.abc import Iterable

from sqlalchemy import update
from sqlalchemy.orm import Session
from sqlalchemy.sql import ColumnElement

from core.error_codes import CODE_STATE_CONFLICT
from core.errors import DomainError


def claim_status(
    db: Session,
    model,
    *,
    identity: ColumnElement[bool],
    from_statuses: str | Iterable[str],
    to_status: str,
    extra_values: dict | None = None,
    increment_version: bool = False,
) -> int:
    """按期望状态条件更新一行；更新 0 行则抛出已登记的状态冲突。

    以 UPDATE 受影响行数为准，明确区分抢占成功（1 行）和未抢到（0 行）。
    不依赖 RETURNING / scalar_one_or_none() 的隐式空结果。
    """
    statuses = (from_statuses,) if isinstance(from_statuses, str) else tuple(from_statuses)
    values: dict = {"status": to_status}
    if extra_values:
        values.update(extra_values)
    if increment_version:
        values[model.version] = model.version + 1

    conditions = [identity]
    if len(statuses) == 1:
        conditions.append(model.status == statuses[0])
    else:
        conditions.append(model.status.in_(statuses))

    stmt = (
        update(model)
        .where(*conditions)
        .values(values)
        .execution_options(synchronize_session=False)
    )
    result = db.execute(stmt)
    affected = result.rowcount
    if affected == 0:
        raise DomainError(CODE_STATE_CONFLICT)
    if affected != 1:
        raise DomainError(CODE_STATE_CONFLICT)
    return affected
