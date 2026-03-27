from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User chat input")
    context: Dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    agent: str
    intent: str
    result: Dict[str, Any]
    trace_id: str = ""


# ---------- Feedback schemas ----------

class ScalarFeedbackRequest(BaseModel):
    trace_id: str = Field(..., min_length=1)
    evaluator_id: str = Field(..., min_length=1)
    scores: Dict[str, int] = Field(
        ...,
        description="Rubric criterion -> score (1-5)",
    )
    comment: str = ""


class PairwisePreferenceRequest(BaseModel):
    trace_id: str = Field(..., min_length=1)
    evaluator_id: str = Field(..., min_length=1)
    output_a: Dict[str, Any]
    output_b: Dict[str, Any]
    preferred: str = Field(..., pattern="^(a|b)$")
    rationale: str = ""


class FeedbackResponse(BaseModel):
    status: str = "ok"
    feedback_id: str = ""
