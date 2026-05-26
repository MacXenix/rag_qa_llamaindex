import pytest
from httpx import AsyncClient


class TestUploadDocument:
    @pytest.mark.asyncio
    async def test_upload_valid_txt_returns_201(self, client: AsyncClient):
        response = await client.post(
            "/api/documents/upload",
            files={"file": ("notes.txt", b"hello world", "text/plain")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "notes.txt"
        assert data["file_type"] == "txt"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_upload_invalid_extension_returns_400(self, client: AsyncClient):
        response = await client.post(
            "/api/documents/upload",
            files={"file": ("sheet.xlsx", b"data", "application/octet-stream")},
        )
        assert response.status_code == 400
        assert "Unsupported" in response.json()["detail"]


class TestIngestURL:
    @pytest.mark.asyncio
    async def test_ingest_valid_url_returns_201(self, client: AsyncClient):
        response = await client.post(
            "/api/documents/url",
            json={"url": "https://example.com"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["file_type"] == "url"

    @pytest.mark.asyncio
    async def test_ingest_invalid_url_returns_422(self, client: AsyncClient):
        response = await client.post(
            "/api/documents/url",
            json={"url": "not-a-url"},
        )
        assert response.status_code == 422


class TestListDocuments:
    @pytest.mark.asyncio
    async def test_empty_list(self, client: AsyncClient):
        response = await client.get("/api/documents")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_returns_uploaded_document(self, client: AsyncClient):
        await client.post(
            "/api/documents/upload",
            files={"file": ("a.txt", b"content", "text/plain")},
        )
        response = await client.get("/api/documents")
        assert response.status_code == 200
        assert len(response.json()) == 1


class TestDeleteDocument:
    @pytest.mark.asyncio
    async def test_delete_existing_returns_204(self, client: AsyncClient):
        upload = await client.post(
            "/api/documents/upload",
            files={"file": ("b.txt", b"content", "text/plain")},
        )
        doc_id = upload.json()["id"]

        response = await client.delete(f"/api/documents/{doc_id}")
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_404(self, client: AsyncClient):
        response = await client.delete("/api/documents/99999")
        assert response.status_code == 404