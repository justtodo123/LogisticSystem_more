from scripts.probe_outbox_trace import HTTP_REQUEST_ID, HTTP_TRACE_ID, run_probe


def test_probe_covers_success_retry_and_dead_letter(db_session):
    report = run_probe(lambda: db_session)
    assert report["passed"] is True, report["failures"]
    assert report["final_status"] == {
        "write-path-success": "delivered",
        "write-path-retry": "delivered",
        "write-path-dead": "dead-letter",
    }
    retry_ids = [item["request_id"] for item in report["attempts"]["write-path-retry"]]
    assert len(retry_ids) == 2
    assert retry_ids[0] != retry_ids[1]
    assert all(item["trace_id"] == HTTP_TRACE_ID for rows in report["attempts"].values() for item in rows)
    assert all(item["parent_request_id"] == HTTP_REQUEST_ID for rows in report["attempts"].values() for item in rows)
    assert all(item["request_id"] != HTTP_REQUEST_ID for rows in report["attempts"].values() for item in rows)
