# AIM-V (Industrial Technology Validation Automation)

AIM-V (Automation for Industrial M&V) is the full project scaffold for automating the DOE ITV program workflows: technology screening, automated M&V plan generation, RAG-grounded LLM agents, and RLHF-based improvement.

Contents
- `backend/` — FastAPI microservices
- `llm_agents/` — agents for screening, M&V planning, analysis, and report writing
- `data/` — storage for ingested reports and training data
- `docs/` — architecture, M&V summary and training notes
- `training/` — SFT + RLHF scaffolds and evaluation harness

Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Prepare example training corpus
python training/scripts/prepare_corpus.py
# Run quick eval harness
python training/scripts/eval_run.py
```

Contributing
- Open issues and PRs on GitHub. Create topic branches and include tests where appropriate.

License
- Add a license if you want to make this project public. For now this repo is private.

