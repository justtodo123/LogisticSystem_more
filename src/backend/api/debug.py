from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from config.database import get_db
from config.settings import settings
from core.error_codes import CODE_NOT_FOUND
from core.errors import DomainError
from core.request_context import get_request_context
from services.outbox_service import enqueue_outbox
from utils.response import success_response

router = APIRouter(prefix="/api/debug", tags=["debug"], include_in_schema=False)

PROBE_EVENT_TYPES = {
    "write-path-success": "write_path_probe.success",
    "write-path-retry": "write_path_probe.retry",
    "write-path-dead": "write_path_probe.dead",
}


@router.post("/write-path-probe")
def enqueue_write_path_probe(db: Session = Depends(get_db)):
    if settings.ENV != "dev":
        raise DomainError(CODE_NOT_FOUND)

    context = get_request_context()
    enqueued = []
    for dedup_key, event_type in PROBE_EVENT_TYPES.items():
        payload = {"case": dedup_key.rsplit("-", 1)[-1]}
        if context is not None and context.task_id:
            payload["task_id"] = context.task_id
        event = enqueue_outbox(
            db,
            dedup_key=dedup_key,
            event_type=event_type,
            payload=payload,
        )
        enqueued.append(
            {
                "dedup_key": event.dedup_key,
                "event_type": event.event_type,
                "status": event.status,
            }
        )
    db.commit()
    return success_response(
        data={
            "enqueued": enqueued,
            "request_id": context.request_id if context is not None else None,
            "trace_id": context.trace_id if context is not None else None,
            "task_id": context.task_id if context is not None else None,
        }
    )
