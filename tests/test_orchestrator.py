import tempfile

from llm_agents.orchestrator import Orchestrator


def _make_orch():
    return Orchestrator(trace_dir=tempfile.mkdtemp())


def test_routes_to_analytics():
    orch = _make_orch()
    out = orch.run("Run regression and report R2", {"baseline_data": []})
    assert out["agent"] == "analytics"
    assert "trace_id" in out


def test_routes_to_documentation():
    orch = _make_orch()
    out = orch.run("Generate documentation template", {})
    assert out["agent"] == "documentation"
    assert "trace_id" in out


def test_routes_to_strategy_by_default():
    orch = _make_orch()
    out = orch.run("Plan my M&V approach", {})
    assert out["agent"] == "strategy"
    assert "trace_id" in out


def test_forced_intent_overrides():
    orch = _make_orch()
    out = orch.run("anything", {"intent": "documentation"})
    assert out["agent"] == "documentation"
    assert "trace_id" in out


def test_guided_mode_routes_to_guide():
    orch = _make_orch()
    out = orch.run("Help me get started", {"guided_mode": True})
    assert out["agent"] == "guide"
    assert out["result"]["current_stage"] == "strategy"
    assert "trace_id" in out
