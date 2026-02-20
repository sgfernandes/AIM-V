from llm_agents.strategy_agent import StrategyAgent


def test_option_a_when_isolation_and_stable():
    agent = StrategyAgent()
    out = agent.run(
        "Need planning for HVAC retrofit",
        {
            "measurement_isolation": True,
            "key_parameter_stable": True,
            "measurement_boundary": "AHU-1 boundary",
        },
    )
    assert out["recommended_option"] == "IPMVP Option A"
    assert out["measurement_boundary"] == "AHU-1 boundary"


def test_option_b_when_isolation_no_stable():
    agent = StrategyAgent()
    out = agent.run(
        "Plan for single system retrofit",
        {"measurement_isolation": True, "key_parameter_stable": False},
    )
    assert out["recommended_option"] == "IPMVP Option B"


def test_option_c_whole_facility():
    agent = StrategyAgent()
    out = agent.run(
        "Whole facility HVAC upgrade",
        {"whole_facility": True, "simulation_required": False},
    )
    assert out["recommended_option"] == "IPMVP Option C"


def test_option_d_simulation():
    agent = StrategyAgent()
    out = agent.run(
        "Facility simulation study",
        {"whole_facility": True, "simulation_required": True},
    )
    assert out["recommended_option"] == "IPMVP Option D"


def test_defaults_to_option_c():
    agent = StrategyAgent()
    out = agent.run("General planning request", {})
    assert out["recommended_option"] == "IPMVP Option C"
    assert isinstance(out["independent_variables"], list)


def test_infers_temperature_var():
    agent = StrategyAgent()
    out = agent.run("We need HVAC cooling analysis", {})
    assert "outdoor_temperature" in out["independent_variables"]


def test_infers_production_var():
    agent = StrategyAgent()
    out = agent.run("Manufacturing throughput retrofit", {})
    assert "production_volume" in out["independent_variables"]
