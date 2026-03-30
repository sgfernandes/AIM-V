from llm_agents.guidance_agent import GuidanceAgent


class MockPlanner:
    def __init__(self, updates=None, guidance=None):
        self._updates = updates or {}
        self._guidance = guidance or {}

    def is_available(self):
        return True

    def extract_context_updates(self, message, context, stage):
        return dict(self._updates)

    def draft_guidance(self, message, context, result, previous_questions=None):
        return dict(self._guidance)

    def metadata(self):
        return {"provider": "openai", "model": "test-model", "enabled": True}


def test_guidance_starts_with_strategy_stage():
    agent = GuidanceAgent()
    out = agent.run("Plan a whole facility chiller retrofit", {})

    assert out["current_stage"] == "strategy"
    assert out["next_stage"] == "analytics"
    assert "strategy_output" in out
    assert out["strategy_output"]["recommended_option"] == "IPMVP Option C"


def test_guidance_requests_baseline_data_before_analytics():
    agent = GuidanceAgent()
    out = agent.run(
        "Continue",
        {
            "strategy_output": {
                "recommended_option": "IPMVP Option C",
                "measurement_boundary": "whole facility meter boundary",
                "independent_variables": ["outdoor_temperature"],
            }
        },
    )

    assert out["current_stage"] == "analytics"
    assert out["stage_status"] == "needs_input"
    assert "baseline data" in out["assistant_message"].lower()


def test_guidance_runs_analytics_when_data_available():
    agent = GuidanceAgent()
    out = agent.run(
        "Run the next stage",
        {
            "strategy_output": {
                "recommended_option": "IPMVP Option C",
                "measurement_boundary": "whole facility meter boundary",
                "independent_variables": ["outdoor_temperature"],
            },
            "baseline_data": [
                {"temperature": 20, "hours": 8, "energy": 164},
                {"temperature": 21, "hours": 9, "energy": 169},
                {"temperature": 22, "hours": 10, "energy": 174},
                {"temperature": 23, "hours": 11, "energy": 179},
            ],
            "dependent_var": "energy",
            "predictors": ["temperature", "hours"],
        },
    )

    assert out["current_stage"] == "analytics"
    assert out["next_stage"] == "documentation"
    assert out["stage_status"] == "ready"
    assert "analytics_output" in out
    assert out["analytics_output"]["r2"] > 0.9


def test_guidance_generates_documentation_after_analytics():
    agent = GuidanceAgent()
    out = agent.run(
        "Create the summary",
        {
            "strategy_output": {
                "recommended_option": "IPMVP Option C",
                "measurement_boundary": "whole facility meter boundary",
                "independent_variables": ["outdoor_temperature"],
            },
            "analytics_output": {
                "r2": 0.91,
                "cvrmse_percent": 8.5,
                "qa_qc": {"model_pass": True},
            },
            "project_name": "Plant Upgrade",
            "facility": "Site A",
        },
    )

    assert out["current_stage"] == "documentation"
    assert out["next_stage"] == "complete"
    assert "documentation_output" in out
    assert "Plant Upgrade" in out["documentation_output"]["document_markdown"]


def test_guidance_uses_llm_updates_and_message_when_available():
    agent = GuidanceAgent(
        planner=MockPlanner(
            updates={
                "measurement_boundary": "Boiler plant meter",
                "whole_facility": True,
                "retrofit_scope": "whole_facility",
            },
            guidance={
                "assistant_message": "I captured your project scope and boundary.",
                "action_items": ["Upload baseline trend data next."],
            },
        )
    )

    out = agent.run("The boundary is the boiler plant meter.", {})

    assert out["assistant_message"] == "I captured your project scope and boundary."
    assert out["action_items"] == ["Upload baseline trend data next."]
    assert out["context_updates"]["measurement_boundary"] == "Boiler plant meter"
    assert out["llm_guidance"]["enabled"] is True
