# ITV M&V Platform — System Architecture

```mermaid
graph TD
    A[User (Chat Interface)] -->|Natural Language Input| B[Orchestrator (LLM-powered Dispatcher)]
    B -->|Phase 1: Planning| C[Strategy Engine Agent]
    B -->|Phase 2 & 4: Baseline & Post-Impl.| D[Analytics Engine Agent]
    B -->|Phase 3 & 5: Implementation & Reporting| E[Documentation Engine Agent]
    C -->|Structured Recommendations| B
    D -->|QA/QC Results, Model Validation| B
    E -->|Generated Docs, Reports| B
    B -->|Responses| A

    subgraph Engines
        C
        D
        E
    end

    subgraph Data Sources
        F[Templates/Rules DB]
        G[Historical Data]
    end

    C -- Uses --> F
    D -- Uses --> G
    E -- Uses --> F
    E -- Uses --> G
```

## Backend MVP Components

- `backend/app/main.py` — FastAPI app entrypoint.
- `backend/app/api/routes.py` — `/health` and `/chat` endpoints.
- `llm_agents/orchestrator.py` — intent routing to specialized agents.
- `llm_agents/strategy_agent.py` — planning logic.
- `llm_agents/analytics_agent.py` — QA/QC and model-check guidance.
- `llm_agents/documentation_agent.py` — plan/report generation guidance.
