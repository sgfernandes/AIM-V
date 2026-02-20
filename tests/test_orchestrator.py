from llm_agents.orchestrator import Orchestrator


def test_routes_to_analytics():
    orch = Orchestrator()
    out = orch.run("Run regression and report R2", {"baseline_data": []})
    assert out["agent"] == "analytics"


def test_routes_to_documentation():
    orch = Orchestrator()
    out = orch.run("Generate documentation template", {})
    assert out["agent"] == "documentation"


def test_routes_to_strategy_by_default():
    orch = Orchestrator()
    out = orch.run("Plan my M&V approach", {})
    assert out["agent"] == "strategy"


def test_forced_intent_overrides():
    orch = Orchestrator()
    out = orch.run("anything", {"intent": "documentation"})
    assert out["agent"] == "documentation"
