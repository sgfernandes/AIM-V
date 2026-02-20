from llm_agents.analytics_agent import AnalyticsAgent


def _baseline_rows(n=30):
    rows = []
    for i in range(n):
        temp = 20 + (i % 10)
        hours = 8 + (i % 4)
        energy = 100 + 2.0 * temp + 3.0 * hours
        rows.append({"temperature": temp, "hours": hours, "energy": energy})
    return rows


def test_ols_returns_metrics():
    agent = AnalyticsAgent()
    out = agent.run(
        "run analytics",
        {
            "baseline_data": _baseline_rows(),
            "dependent_var": "energy",
            "predictors": ["temperature", "hours"],
        },
    )
    assert out["model_type"] == "OLS"
    assert out["r2"] > 0.99
    assert out["cvrmse_percent"] < 1.0
    assert out["qa_qc"]["pass"] is True


def test_ols_error_on_empty_data():
    agent = AnalyticsAgent()
    out = agent.run("run analytics", {})
    assert "error" in out


def test_ols_error_on_missing_dep():
    agent = AnalyticsAgent()
    out = agent.run(
        "check",
        {
            "baseline_data": [{"x": 1}],
            "dependent_var": "energy",
        },
    )
    assert "error" in out


def test_savings_calculation():
    agent = AnalyticsAgent()
    baseline = _baseline_rows()
    post = [
        {
            "temperature": r["temperature"],
            "hours": r["hours"],
            "energy": r["energy"] - 5.0,
        }
        for r in baseline
    ]
    out = agent.run(
        "calculate savings",
        {
            "baseline_data": baseline,
            "post_data": post,
            "dependent_var": "energy",
            "predictors": ["temperature", "hours"],
        },
    )
    assert "post_period" in out
    assert out["post_period"]["estimated_savings"] > 0
    assert out["post_period"]["estimated_savings_percent"] > 0


def test_qa_fail_on_bad_data():
    agent = AnalyticsAgent()
    bad = [{"x": i, "energy": (i % 2) * 999} for i in range(30)]
    out = agent.run(
        "check",
        {
            "baseline_data": bad,
            "dependent_var": "energy",
            "predictors": ["x"],
        },
    )
    assert "r2" in out  # runs without crashing
