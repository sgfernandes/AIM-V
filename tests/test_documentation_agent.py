from llm_agents.documentation_agent import DocumentationAgent


def test_generates_markdown():
    agent = DocumentationAgent()
    out = agent.run(
        "write plan",
        {
            "project_name": "Pilot Retrofit",
            "facility": "Site A",
            "strategy_output": {
                "recommended_option": "IPMVP Option C",
                "measurement_boundary": "whole facility meter boundary",
                "independent_variables": ["outdoor_temperature", "operating_hours"],
            },
            "analytics_output": {
                "r2": 0.91,
                "cvrmse_percent": 12.3,
                "qa_qc": {"pass": True},
            },
        },
    )
    assert out["document_type"] == "mv_plan_summary_markdown"
    assert "# M&V Plan Summary" in out["document_markdown"]
    assert "Pilot Retrofit" in out["document_markdown"]
    assert "IPMVP Option C" in out["document_markdown"]


def test_defaults_when_no_context():
    agent = DocumentationAgent()
    out = agent.run("generate report", {})
    assert "Untitled M&V Project" in out["document_markdown"]
    assert "TBD" in out["document_markdown"]
