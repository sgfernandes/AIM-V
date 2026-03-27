import tempfile

from llm_agents.trace_logger import TraceLogger, TraceRecord


def test_begin_and_end():
    logger = TraceLogger(log_dir=tempfile.mkdtemp())
    rec = logger.begin("test message", {"key": "val"})
    assert isinstance(rec, TraceRecord)
    assert rec.user_message == "test message"
    assert rec.context == {"key": "val"}

    rec.chosen_route = "strategy"
    rec.agent_name = "strategy"
    rec.agent_output = {"recommended_option": "IPMVP Option C"}
    logger.end(rec)

    assert rec.duration_ms >= 0
    assert rec.end_time >= rec.start_time


def test_persist_and_load():
    tmp = tempfile.mkdtemp()
    logger = TraceLogger(log_dir=tmp)

    rec = logger.begin("msg 1", {})
    rec.agent_name = "analytics"
    logger.end(rec)

    rec2 = logger.begin("msg 2", {})
    rec2.agent_name = "documentation"
    logger.end(rec2)

    all_records = logger.load_all()
    assert len(all_records) == 2
    assert all_records[0]["agent_name"] == "analytics"
    assert all_records[1]["agent_name"] == "documentation"


def test_load_by_id():
    tmp = tempfile.mkdtemp()
    logger = TraceLogger(log_dir=tmp)

    rec = logger.begin("lookup test", {})
    rec.agent_name = "strategy"
    logger.end(rec)

    found = logger.load_by_id(rec.trace_id)
    assert found is not None
    assert found["user_message"] == "lookup test"

    assert logger.load_by_id("nonexistent") is None


def test_empty_load():
    logger = TraceLogger(log_dir=tempfile.mkdtemp())
    assert logger.load_all() == []
