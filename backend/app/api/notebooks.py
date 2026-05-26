from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.chat import ChatHistoryResponse, ChatRequest
from app.services.query_service import QueryService

router = APIRouter(prefix="/api/notebooks", tags=["notebooks"])


@router.post("/{document_id}/chat")
async def chat(
    document_id: int,
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    service = QueryService(db)
    return StreamingResponse(
        service.stream_query(document_id, request.question),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{document_id}/history", response_model=list[ChatHistoryResponse])
async def get_history(
    document_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[ChatHistoryResponse]:
    return await QueryService(db).get_history(document_id)