from fastapi import APIRouter

from backend.app.schemas import ChatRequest, ChatResponse, HealthResponse
from llm_agents.orchestrator import Orchestrator

router = APIRouter()
orchestrator = Orchestrator()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    result = orchestrator.route(payload.message)
    return ChatResponse(
        engine=result.engine,
        intent=result.intent,
        response=result.response,
    )
