from datetime import datetime, timedelta, timezone

from models.global_schedule import GlobalSchedule
from models.idempotency_record import IdempotencyRecord
from models.node import Node
from models.outbox_event import OutboxEvent
from models.storage_center import StorageCenter
from scripts.check_write_path_invariants import run_checks


def test_invariants_pass_for_single_idempotent_write_and_one_confirm(db_session):
    node = Node(
        node_code="K6N1",
        name="k6-node-K6N1",
        location="load-test",
        latitude=30.5,
        longitude=114.3,
        node_type="storage_center",
    )
    db_session.add(node)
    db_session.flush()
    db_session.add(StorageCenter(node_id=node.id, capacity=500))
    db_session.add(
        IdempotencyRecord(
            idempotency_key="idem-K6N1",
            status="SUCCEEDED",
            payload_hash="abc",
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1),
        )
    )
    schedule = GlobalSchedule(
        schedule_code="GS-K6-1",
        order_codes=["O001"],
        goods_schedules=[{"goods_code": "G001"}],
        total_distance=1,
        total_time=1,
        total_goods=1,
        score=1,
        algorithm_type="traditional",
        status="active",
        version=2,
    )
    db_session.add(schedule)
    db_session.add(
        OutboxEvent(
            dedup_key="replan-task:1:notification",
            event_type="replan.completed",
            payload={"task_id": 1},
            status="delivered",
        )
    )
    db_session.commit()

    report = run_checks(db_session, schedule_code="GS-K6-1")
    assert report["passed"] is True
    assert report["idempotency"]["node_count"] == 1
    assert report["confirm"]["status"] == "active"
    assert report["outbox"]["processing_count"] == 0


def test_invariants_fail_on_duplicate_nodes_and_processing(db_session):
    db_session.add_all(
        [
            Node(
                node_code="K6DUP",
                name="k6-node-a",
                location="load-test",
                latitude=1,
                longitude=1,
                node_type="storage_center",
            ),
            Node(
                node_code="K6DUP2",
                name="k6-node-a",
                location="load-test",
                latitude=1,
                longitude=1,
                node_type="storage_center",
            ),
            IdempotencyRecord(
                idempotency_key="idem-stuck",
                status="PROCESSING",
                payload_hash="abc",
                expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1),
            ),
            OutboxEvent(
                dedup_key="stuck-outbox",
                event_type="notification.test",
                payload={},
                status="processing",
            ),
            GlobalSchedule(
                schedule_code="GS-K6-DRAFT",
                order_codes=["O001"],
                goods_schedules=[],
                total_distance=1,
                total_time=1,
                total_goods=1,
                score=1,
                algorithm_type="traditional",
                status="draft",
            ),
        ]
    )
    db_session.commit()
    report = run_checks(db_session, schedule_code="GS-K6-DRAFT")
    assert report["passed"] is False
    assert report["idempotency"]["processing_count"] == 1
    assert report["outbox"]["processing_count"] == 1
    assert report["confirm"]["status"] == "draft"
