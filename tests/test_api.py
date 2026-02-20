from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_chat_strategy():
    resp = client.post(
        "/chat",
        json={
            "message": "Help me plan M&V for a whole-facility retrofit",
            "context": {"whole_facility": True},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["agent"] == "strategy"
    assert "recommended_option" in body["result"]


def test_chat_analytics():
    baseline = [
        {"temperature": 20 + i, "hours": 8 + (i % 4), "energy": 100 + 2 * (20 + i) + 3 * (8 + i % 4)}
        for i in range(20)
    ]
    resp = client.post(
        "/chat",
        json={
            "message": "Run baseline regression",
            "context": {
                "baseline_data": baseline,
                "dependent_var": "energy",
                "predictors": ["temperature", "hours"],
            },
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["agent"] == "analytics"
    assert body["result"]["r2"] > 0.9


def test_chat_documentation():
    resp = client.post(
        "/chat",
        json={
            "message": "Generate final report",
            "context": {
                "project_name": "Test Project",
                "facility": "Lab 1",
            },
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["agent"] == "documentation"
    assert "document_markdown" in body["result"]
