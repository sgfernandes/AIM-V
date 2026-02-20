# AIM-V — Automation for Industrial M&V

Multi-agent platform for automating DOE ITV M&V workflows: strategy planning, baseline analytics, and documentation generation.

## Architecture

See [`docs/itv_mv_system_architecture.md`](docs/itv_mv_system_architecture.md) for the full system diagram.

| Component | Path | Purpose |
|-----------|------|---------|
| FastAPI backend | `backend/` | `/health` and `/chat` API endpoints |
| Strategy Engine | `llm_agents/strategy_agent.py` | IPMVP option recommendation + boundary guidance |
| Analytics Engine | `llm_agents/analytics_agent.py` | OLS regression, R², CV(RMSE), QA/QC, savings |
| Documentation Engine | `llm_agents/documentation_agent.py` | M&V plan and report markdown generation |
| Orchestrator | `llm_agents/orchestrator.py` | Intent routing across engines |
| Tests | `tests/` | Unit + API integration tests |
| Sample payloads | `docs/sample_chat_payloads.json` | Ready-to-use `/chat` request examples |
| ITV reports | `data/raw/itv_reports/` | Source validation reports |

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload
```

Open http://127.0.0.1:8000/docs for Swagger UI.

## Run tests

```bash
pytest -q
```

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health check |
| `POST` | `/chat` | Route prompt to Strategy, Analytics, or Documentation engine |

### POST /chat example

```json
{
  "message": "Run baseline regression and QA/QC",
  "context": {
    "dependent_var": "energy",
    "predictors": ["temperature", "hours"],
    "baseline_data": [
      {"temperature": 21, "hours": 8, "energy": 166},
      {"temperature": 22, "hours": 9, "energy": 171}
    ]
  }
}
```

