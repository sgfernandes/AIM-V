from typing import Any, Dict

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User chat input")
    context: Dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    agent: str
    intent: str
    result: Dict[str, Any]
