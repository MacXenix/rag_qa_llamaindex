from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.document import DocumentResponse, URLIngestRequest
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    service = IngestionService(db)
    try:
        return await service.ingest_file(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/url", response_model=DocumentResponse, status_code=201)
async def ingest_url(
    request: URLIngestRequest,
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    service = IngestionService(db)
    try:
        return await service.ingest_url(str(request.url))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    db: AsyncSession = Depends(get_db),
) -> list[DocumentResponse]:
    return await IngestionService(db).list_documents()


@router.delete("/{doc_id}", status_code=204)
async def delete_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    service = IngestionService(db)
    try:
        await service.delete_document(doc_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))