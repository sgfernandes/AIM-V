from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User chat input")


class ChatResponse(BaseModel):
    engine: str
    intent: str
    response: str
