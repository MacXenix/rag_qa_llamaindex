from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChatRequest(BaseModel):
    question: str


class ChatHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    question: str
    answer: str
    citations: str  # JSON-encoded list
    created_at: datetime
