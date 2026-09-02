"""SQL comment instrumentation tests."""

from sqlalchemy import create_engine, event, text
from core.request_context import RequestContext, bind_request_context, reset_request_context
from core.sql_comments import instrument_engine


def test_sql_statements_receive_request_id_comment():
    engine = create_engine("sqlite:///:memory:")
    instrument_engine(engine)
    instrument_engine(engine)
    statements = []

    def capture(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(engine, "after_cursor_execute", capture)
    token = bind_request_context(
        RequestContext(request_id="req-sql", trace_id="trc-sql", task_id="9")
    )
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    finally:
        reset_request_context(token)
        engine.dispose()

    assert statements
    assert "request_id=req-sql" in statements[0]
    assert "trace_id=trc-sql" in statements[0]
    assert "task_id=9" in statements[0]
