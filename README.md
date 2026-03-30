# AIM-V — Automation for Industrial M&V

Guided multi-agent workflow for industrial Measurement and Verification: strategy planning, baseline analytics, and documentation generation.

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

## Quick Start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Open `http://127.0.0.1:8501` for the guided UI.

To run the FastAPI backend instead:

```bash
uvicorn backend.app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for Swagger UI.

## Guided AI Mode

The Streamlit UI now supports a guided workflow assistant that can run in two modes:

- Deterministic fallback: works without external API access and guides users through strategy, analytics, and documentation with built-in rules.
- OpenAI-backed guidance: if `OPENAI_API_KEY` is set, the guide uses an OpenAI model to interpret freeform user replies and draft more natural stage-by-stage coaching while the domain logic still runs through the specialist agents.

Optional environment variables:

```bash
export OPENAI_API_KEY=your_key_here
export OPENAI_MODEL=gpt-4.1-mini
```

Then launch the UI:

```bash
streamlit run streamlit_app.py
```

If no OpenAI key is set, the app still works in deterministic mode.

## Deployment

The easiest hosted option is Streamlit Community Cloud.

1. Push this repo to GitHub.
2. In Streamlit Community Cloud, create a new app from the repo.
3. Set the entrypoint to `streamlit_app.py`.
4. Add secrets in the app settings:

```toml
OPENAI_API_KEY = "your_key_here"
OPENAI_MODEL = "gpt-4.1-mini"
```

If `OPENAI_MODEL` is omitted, AIM-V now defaults to `gpt-4.1-mini` and will try a small fallback model if the configured model is rejected.

You can also use `.streamlit/secrets.toml.example` as a template for local development, but never commit a real `.streamlit/secrets.toml`.

## Public Repo Checklist

- Rotate any key that has ever been pasted into chat or a terminal screenshot.
- Keep `.env` and `.streamlit/secrets.toml` local only.
- Review source PDFs and documents before publishing if they contain restricted project material.
- Run tests before pushing public changes.

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
