from pydantic import BaseModel


class AgentChatRequest(BaseModel):
    question: str
