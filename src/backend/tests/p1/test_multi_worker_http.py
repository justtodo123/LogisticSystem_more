"""Explicit cross-process HTTP validation for the P1 topology."""
import os
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import select

from services.auth_service import get_password_hash
from models.idempotency_record import IdempotencyRecord
from models.log_event import LogEvent
from models.node import Node
from models.storage_center import StorageCenter
from models.user import User
from middleware.idempotency import build_durable_key
from utils.idempotency_store import STATUS_SUCCEEDED


def _worker_url(name: str) -> str:
    url = os.environ.get(name, "").strip().rstrip("/")
    if not url:
        pytest.skip(f"requires {name}")
    return url


def _assert_success(response: httpx.Response) -> dict:
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    return body


@pytest.mark.integration
def test_two_workers_share_revocation_and_idempotency(
    p1_postgres,
    p1_redis_url,
    p1_row_cleanup,
):
    """Address workers separately so shared-state checks cannot hit one process twice."""
    _engine, factory = p1_postgres
    worker_a = _worker_url("P1_WORKER_A_URL")
    worker_b = _worker_url("P1_WORKER_B_URL")
    suffix = uuid4().hex
    username = f"p1-http-{suffix}"
    password = f"P1-{suffix}"
    node_code = f"P1H{suffix[:16].upper()}"
    client_key = f"p1-http-idempotency-{suffix}"
    durable_key = build_durable_key(f"user:{username}", client_key)

    seed = factory()
    try:
        user = User(
            username=username,
            password_hash=get_password_hash(password),
            role="admin",
            display_name="P1 HTTP worker test",
            is_active=True,
        )
        seed.add(user)
        seed.commit()
        user_id = user.id
    finally:
        seed.close()

    p1_row_cleanup(
        StorageCenter,
        Node,
        IdempotencyRecord,
        LogEvent,
        User,
        filters={
            StorageCenter: StorageCenter.node_id.in_(
                select(Node.id).where(Node.node_code == node_code)
            ),
            Node: Node.node_code == node_code,
            IdempotencyRecord: IdempotencyRecord.idempotency_key == durable_key,
            LogEvent: LogEvent.user_id == user_id,
            User: User.username == username,
        },
    )

    with httpx.Client(timeout=30) as client:
        login = _assert_success(
            client.post(
                f"{worker_a}/api/auth/login",
                json={"username": username, "password": password},
            )
        )
        token = login["data"]["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        me = _assert_success(
            client.get(f"{worker_b}/api/auth/me", headers=auth_headers)
        )
        assert me["data"]["username"] == username

        payload = {
            "node_code": node_code,
            "name": "P1 cross-worker storage center",
            "location": "synthetic-ci",
            "latitude": 30.5,
            "longitude": 114.3,
            "capacity": 500.0,
            "inventory": 0,
        }
        write_headers = {
            **auth_headers,
            "X-Idempotency-Key": client_key,
        }
        first = client.post(
            f"{worker_a}/api/nodes/storage-centers",
            json=payload,
            headers=write_headers,
        )
        replay = client.post(
            f"{worker_b}/api/nodes/storage-centers",
            json=payload,
            headers=write_headers,
        )
        first_body = _assert_success(first)
        replay_body = _assert_success(replay)
        assert replay_body == first_body

        _assert_success(
            client.post(f"{worker_b}/api/auth/logout", headers=auth_headers)
        )
        rejected = client.get(f"{worker_a}/api/auth/me", headers=auth_headers)
        assert rejected.status_code == 401
        assert rejected.json()["code"] == 40100

    verify = factory()
    try:
        node = verify.query(Node).filter_by(node_code=node_code).one()
        assert (
            verify.query(StorageCenter)
            .filter_by(node_id=node.id)
            .count()
            == 1
        )
        record = (
            verify.query(IdempotencyRecord)
            .filter_by(idempotency_key=durable_key)
            .one()
        )
        assert record.status == STATUS_SUCCEEDED
    finally:
        verify.close()
