import asyncio

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
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
        service.stream_query(document_id, request.question, request.mode),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{document_id}/compare")
async def compare_retrieval(
    document_id: int,
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Run the same question through basic and the configured advanced mode side by side."""
    advanced_mode = settings.retrieval_mode

    if advanced_mode == "basic":
        raise HTTPException(
            status_code=400,
            detail="Set RETRIEVAL_MODE to 'hyde', 'rerank', or 'hyde+rerank' to compare.",
        )

    service = QueryService(db)
    basic_result, advanced_result = await asyncio.gather(
        service.query_once(document_id, request.question, mode="basic"),
        service.query_once(document_id, request.question, mode=advanced_mode),
    )

    return {
        "question": request.question,
        "basic": basic_result,
        advanced_mode: advanced_result,
    }


@router.get("/{document_id}/history", response_model=list[ChatHistoryResponse])
async def get_history(
    document_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[ChatHistoryResponse]:
    return await QueryService(db).get_history(document_id)