from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    file_type: str
    source: str
    chroma_collection: str
    created_at: datetime


class URLIngestRequest(BaseModel):
    url: HttpUrl