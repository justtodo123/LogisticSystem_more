from pathlib import Path
import json

from scripts.outbox_worker import handle_write_path_probe
from scripts.probe_outbox_trace import (
    HTTP_REQUEST_ID,
    HTTP_TASK_ID,
    HTTP_TRACE_ID,
    PROBE_EVENT_TYPES,
    PROBE_KEYS,
    parse_worker_attempts,
    run_probe,
)
from models.outbox_event import OutboxEvent
from services.outbox_service import deliver_outbox_batch, enqueue_outbox
from core.request_context import RequestContext, bind_request_context, reset_request_context


def test_probe_covers_success_retry_and_dead_letter(db_session):
    report = run_probe(lambda: db_session)
    assert report['passed'] is True, report['failures']
    assert report['worker_mode'] == 'in-process'
    assert report['enqueue_source'] == 'in-process'
    assert report['final_status'] == {
        'write-path-success': 'delivered',
        'write-path-retry': 'delivered',
        'write-path-dead': 'dead-letter',
    }
    retry_ids = [item['request_id'] for item in report['attempts']['write-path-retry']]
    assert len(retry_ids) == 2
    assert retry_ids[0] != retry_ids[1]
    assert all(item['trace_id'] == HTTP_TRACE_ID for rows in report['attempts'].values() for item in rows)
    assert all(item['parent_request_id'] == HTTP_REQUEST_ID for rows in report['attempts'].values() for item in rows)
    assert all(item['request_id'] != HTTP_REQUEST_ID for rows in report['attempts'].values() for item in rows)


def test_parse_independent_worker_log(tmp_path: Path):
    log = tmp_path / 'write-outbox-worker.log'
    rows = []
    for key, req in (
        ('write-path-success', 'exec-1'),
        ('write-path-retry', 'exec-2'),
        ('write-path-retry', 'exec-3'),
        ('write-path-dead', 'exec-4'),
    ):
        rows.append(json.dumps({'msg': 'outbox_execute', 'trace_id': HTTP_TRACE_ID, 'request_id': req, 'parent_request_id': HTTP_REQUEST_ID, 'task_id': 'task-write-path-probe', 'dedup_key': key}))
        rows.append(json.dumps({'msg': 'worker_handle', 'trace_id': HTTP_TRACE_ID, 'request_id': req, 'parent_request_id': HTTP_REQUEST_ID}))
    log.write_text(chr(10).join(rows) + chr(10), encoding='utf-8')
    attempts = parse_worker_attempts(log)
    assert attempts['write-path-retry'][0]['request_id'] == 'exec-2'
    assert attempts['write-path-retry'][1]['request_id'] == 'exec-3'
    assert attempts['write-path-success'][0]['parent_request_id'] == HTTP_REQUEST_ID


def test_independent_worker_probe_handler_success_retry_dead(db_session):
    token = bind_request_context(RequestContext(request_id=HTTP_REQUEST_ID, trace_id=HTTP_TRACE_ID, task_id='task-write-path-probe'))
    try:
        enqueue_outbox(db_session, dedup_key='write-path-success', event_type='write_path_probe.success', payload={'case': 'success'})
        enqueue_outbox(db_session, dedup_key='write-path-retry', event_type='write_path_probe.retry', payload={'case': 'retry'})
        enqueue_outbox(db_session, dedup_key='write-path-dead', event_type='write_path_probe.dead', payload={'case': 'dead'})
        db_session.commit()
    finally:
        reset_request_context(token)
    def sender(event: OutboxEvent) -> bool:
        result = handle_write_path_probe(event)
        assert result is not None
        return result
    first = deliver_outbox_batch(lambda: db_session, sender, worker_id='unit-independent-worker', max_retries=3, retry_delay_seconds=0)
    second = deliver_outbox_batch(lambda: db_session, sender, worker_id='unit-independent-worker', max_retries=3, retry_delay_seconds=0)
    assert first['delivered'] == 1
    assert first['retry'] == 1
    assert first['dead-letter'] == 1
    assert second['delivered'] == 1
    db_session.expire_all()
    statuses = {row.dedup_key: row.status for row in db_session.query(OutboxEvent).filter(OutboxEvent.dedup_key.in_(['write-path-success', 'write-path-retry', 'write-path-dead']))}
    assert statuses == {'write-path-success': 'delivered', 'write-path-retry': 'delivered', 'write-path-dead': 'dead-letter'}


def test_probe_handler_ignores_business_events():
    event = OutboxEvent(dedup_key='biz', event_type='replan.completed', payload={})
    assert handle_write_path_probe(event) is None


def test_wait_worker_requires_http_enqueue(db_session, tmp_path: Path):
    log = tmp_path / 'write-outbox-worker.log'
    log.write_text('', encoding='utf-8')
    report = run_probe(lambda: db_session, wait_worker=True, worker_log=log, timeout=0.2)
    assert report['passed'] is False
    assert report['enqueue_source'] == 'http'
    assert any('base-url' in item for item in report['failures'])
    assert db_session.query(OutboxEvent).filter(OutboxEvent.dedup_key.in_(PROBE_KEYS)).count() == 0


class _FakeHttpResponse:
    status = 200
    headers = {
        'X-Request-ID': HTTP_REQUEST_ID,
        'X-Trace-ID': HTTP_TRACE_ID,
        'X-Task-ID': HTTP_TASK_ID,
    }

    def read(self):
        return json.dumps({'code': 0, 'message': 'success', 'data': {'enqueued': list(PROBE_KEYS)}}).encode('utf-8')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_wait_worker_enqueues_via_http(db_session, tmp_path: Path, monkeypatch):
    log = tmp_path / 'write-outbox-worker.log'
    rows = []
    for key, req in (
        ('write-path-success', 'exec-1'),
        ('write-path-retry', 'exec-2'),
        ('write-path-retry', 'exec-3'),
        ('write-path-dead', 'exec-4'),
    ):
        rows.append(json.dumps({'msg': 'outbox_execute', 'trace_id': HTTP_TRACE_ID, 'request_id': req, 'parent_request_id': HTTP_REQUEST_ID, 'task_id': HTTP_TASK_ID, 'dedup_key': key}))
        rows.append(json.dumps({'msg': 'worker_handle', 'trace_id': HTTP_TRACE_ID, 'request_id': req, 'parent_request_id': HTTP_REQUEST_ID}))
        rows.append(json.dumps({'msg': 'outbox_outcome', 'trace_id': HTTP_TRACE_ID, 'request_id': req}))
        if key == 'write-path-dead':
            rows.append(json.dumps({'msg': 'notification_dead_letter', 'trace_id': HTTP_TRACE_ID, 'request_id': req}))
    log.write_text(chr(10).join(rows) + chr(10), encoding='utf-8')

    def fake_urlopen(request, timeout=10):
        assert '/api/debug/write-path-probe' in request.full_url
        token = bind_request_context(RequestContext(request_id=HTTP_REQUEST_ID, trace_id=HTTP_TRACE_ID, task_id=HTTP_TASK_ID))
        try:
            for dedup_key, event_type in PROBE_EVENT_TYPES.items():
                enqueue_outbox(
                    db_session,
                    dedup_key=dedup_key,
                    event_type=event_type,
                    payload={'case': dedup_key.rsplit('-', 1)[-1]},
                )
            db_session.commit()
        finally:
            reset_request_context(token)

        def sender(event: OutboxEvent) -> bool:
            result = handle_write_path_probe(event)
            assert result is not None
            return result

        deliver_outbox_batch(lambda: db_session, sender, worker_id='unit-http-worker', max_retries=3, retry_delay_seconds=0)
        deliver_outbox_batch(lambda: db_session, sender, worker_id='unit-http-worker', max_retries=3, retry_delay_seconds=0)
        return _FakeHttpResponse()

    monkeypatch.setattr('scripts.probe_outbox_trace.urlopen', fake_urlopen)
    report = run_probe(
        lambda: db_session,
        base_url='http://127.0.0.1:18001',
        wait_worker=True,
        worker_log=log,
        timeout=2,
    )
    assert report['passed'] is True, report['failures']
    assert report['worker_mode'] == 'independent'
    assert report['enqueue_source'] == 'http'
    assert report['http']['path'] == '/api/debug/write-path-probe'
    assert report['http']['request_id'] == HTTP_REQUEST_ID
    retry_ids = [item['request_id'] for item in report['attempts']['write-path-retry']]
    assert retry_ids == ['exec-2', 'exec-3']
