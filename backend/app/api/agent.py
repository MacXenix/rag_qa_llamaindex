from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.agent import AgentChatRequest
from app.services.agent_service import AgentService

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/chat")
async def agent_chat(request: AgentChatRequest) -> StreamingResponse:
    service = AgentService()
    return StreamingResponse(
        service.stream_agent(request.question),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )