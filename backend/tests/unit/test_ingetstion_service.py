from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import UploadFile

from app.services.ingestion_service import (
    SUPPORTED_EXTENSIONS,
    MAX_FILE_SIZE,
    IngestionService,
)


def make_upload_file(filename: str, content: bytes = b"hello") -> UploadFile:
    return UploadFile(filename=filename, file=BytesIO(content))


@pytest.fixture
def db():
    session = AsyncMock()
    session.add = MagicMock()  # add() is synchronous in SQLAlchemy
    session.get = AsyncMock()
    return session


@pytest.fixture
def service(db):
    return IngestionService(db)


class TestIngestFile:
    @pytest.mark.asyncio
    async def test_unsupported_extension_raises(self, service):
        file = make_upload_file("report.xlsx")
        with pytest.raises(ValueError, match="Unsupported file type"):
            await service.ingest_file(file)

    @pytest.mark.asyncio
    async def test_file_too_large_raises(self, service):
        big_content = b"x" * (MAX_FILE_SIZE + 1)
        file = make_upload_file("big.pdf", content=big_content)
        with pytest.raises(ValueError, match="50 MB"):
            await service.ingest_file(file)

    @pytest.mark.asyncio
    async def test_valid_pdf_indexes_and_saves(self, service, db):
        file = make_upload_file("doc.pdf", content=b"%PDF fake")
        mock_doc = MagicMock()

        with patch.object(service, "_load_file", return_value=[MagicMock()]), \
             patch("app.services.ingestion_service.get_storage_context"), \
             patch("app.services.ingestion_service.VectorStoreIndex.from_documents"), \
             patch("asyncio.to_thread", new=AsyncMock(return_value=None)):
            db.refresh = AsyncMock(return_value=None)
            result = await service.ingest_file(file)

        db.add.assert_called_once()
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_valid_txt_is_accepted(self, service, db):
        file = make_upload_file("notes.txt", content=b"plain text")
        with patch.object(service, "_load_file", return_value=[MagicMock()]), \
             patch("app.services.ingestion_service.get_storage_context"), \
             patch("asyncio.to_thread", new=AsyncMock(return_value=None)):
            db.refresh = AsyncMock()
            await service.ingest_file(file)
        db.add.assert_called_once()


class TestIngestURL:
    @pytest.mark.asyncio
    async def test_non_http_url_raises(self, service):
        with pytest.raises(ValueError, match="http"):
            await service.ingest_url("ftp://example.com")

    @pytest.mark.asyncio
    async def test_valid_url_indexes_and_saves(self, service, db):
        with patch("app.services.ingestion_service.BeautifulSoupWebReader") as mock_reader, \
             patch("app.services.ingestion_service.get_storage_context"), \
             patch("asyncio.to_thread", new=AsyncMock(return_value=[MagicMock()])):
            db.refresh = AsyncMock()
            await service.ingest_url("https://example.com")

        db.add.assert_called_once()
        db.commit.assert_awaited_once()


class TestListDocuments:
    @pytest.mark.asyncio
    async def test_returns_list(self, service, db):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [MagicMock(), MagicMock()]
        db.execute = AsyncMock(return_value=mock_result)

        result = await service.list_documents()
        assert len(result) == 2


class TestDeleteDocument:
    @pytest.mark.asyncio
    async def test_not_found_raises(self, service, db):
        db.get = AsyncMock(return_value=None)
        with pytest.raises(ValueError, match="not found"):
            await service.delete_document(99)

    @pytest.mark.asyncio
    async def test_found_deletes(self, service, db):
        mock_doc = MagicMock()
        db.get = AsyncMock(return_value=mock_doc)

        await service.delete_document(1)

        db.delete.assert_awaited_once_with(mock_doc)
        db.commit.assert_awaited_once()