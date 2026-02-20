from fastapi import APIRouter

from backend.app.schemas import ChatRequest, ChatResponse
from llm_agents.orchestrator import Orchestrator

router = APIRouter()
orchestrator = Orchestrator()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    out = orchestrator.run(req.message, req.context)
    return ChatResponse(**out)
