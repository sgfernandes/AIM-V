from typing import Any, Dict, List

from fastapi import APIRouter

from backend.app.schemas import (
    ChatRequest,
    ChatResponse,
    FeedbackResponse,
    PairwisePreferenceRequest,
    ScalarFeedbackRequest,
)
from llm_agents.feedback import (
    RUBRIC_CRITERIA,
    FeedbackStore,
    PairwisePreference,
    ScalarFeedback,
)
from llm_agents.orchestrator import Orchestrator
from llm_agents.trace_logger import TraceLogger

router = APIRouter()
orchestrator = Orchestrator()
feedback_store = FeedbackStore()
trace_logger = TraceLogger()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    out = orchestrator.run(req.message, req.context)
    return ChatResponse(**out)


# ---------- Feedback endpoints ----------

@router.get("/feedback/rubric")
def get_rubric() -> Dict[str, List[str]]:
    return {"criteria": RUBRIC_CRITERIA}


@router.post("/feedback/scalar", response_model=FeedbackResponse)
def submit_scalar_feedback(req: ScalarFeedbackRequest) -> FeedbackResponse:
    fb = ScalarFeedback(
        trace_id=req.trace_id,
        evaluator_id=req.evaluator_id,
        scores=req.scores,
        comment=req.comment,
    )
    feedback_store.record_scalar(fb)
    return FeedbackResponse(feedback_id=fb.feedback_id)


@router.post("/feedback/preference", response_model=FeedbackResponse)
def submit_pairwise_preference(req: PairwisePreferenceRequest) -> FeedbackResponse:
    pref = PairwisePreference(
        trace_id=req.trace_id,
        evaluator_id=req.evaluator_id,
        output_a=req.output_a,
        output_b=req.output_b,
        preferred=req.preferred,
        rationale=req.rationale,
    )
    feedback_store.record_preference(pref)
    return FeedbackResponse(feedback_id=pref.preference_id)


# ---------- Trace query ----------

@router.get("/traces")
def list_traces() -> List[Dict[str, Any]]:
    return trace_logger.load_all()


@router.get("/traces/{trace_id}")
def get_trace(trace_id: str) -> Dict[str, Any]:
    record = trace_logger.load_by_id(trace_id)
    if record is None:
        return {"error": f"Trace {trace_id} not found"}
    return record
