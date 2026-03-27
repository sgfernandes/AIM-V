import tempfile

from llm_agents.feedback import (
    FeedbackStore,
    PairwisePreference,
    ScalarFeedback,
)


def test_scalar_feedback_roundtrip():
    store = FeedbackStore(log_dir=tempfile.mkdtemp())
    fb = ScalarFeedback(
        trace_id="t1",
        evaluator_id="eval1",
        scores={"technical_correctness": 4, "clarity": 5},
        comment="good output",
    )
    store.record_scalar(fb)
    loaded = store.load_scalar()
    assert len(loaded) == 1
    assert loaded[0]["trace_id"] == "t1"
    assert loaded[0]["scores"]["clarity"] == 5


def test_pairwise_preference_roundtrip():
    store = FeedbackStore(log_dir=tempfile.mkdtemp())
    pref = PairwisePreference(
        trace_id="t2",
        evaluator_id="eval1",
        output_a={"text": "A"},
        output_b={"text": "B"},
        preferred="b",
        rationale="B more complete",
    )
    store.record_preference(pref)
    loaded = store.load_pairwise()
    assert len(loaded) == 1
    assert loaded[0]["preferred"] == "b"


def test_empty_stores():
    store = FeedbackStore(log_dir=tempfile.mkdtemp())
    assert store.load_scalar() == []
    assert store.load_pairwise() == []


def test_multiple_records():
    store = FeedbackStore(log_dir=tempfile.mkdtemp())
    for i in range(5):
        fb = ScalarFeedback(
            trace_id=f"t{i}",
            evaluator_id="eval1",
            scores={"usefulness": i},
        )
        store.record_scalar(fb)
    loaded = store.load_scalar()
    assert len(loaded) == 5
