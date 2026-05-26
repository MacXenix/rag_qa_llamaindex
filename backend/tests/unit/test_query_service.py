import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.query_service import QueryService


@pytest.fixture
def db():
    session = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def service(db):
    return QueryService(db)


def make_mock_response(tokens: list[str], source_nodes=None):
    response = MagicMock()
    response.response_gen = iter(tokens)
    response.source_nodes = source_nodes or []
    return response


class TestExtractCitations:
    def test_empty_source_nodes_returns_empty(self, service):
        response = MagicMock()
        response.source_nodes = []
        assert service._extract_citations(response) == []

    def test_no_source_nodes_attr_returns_empty(self, service):
        assert service._extract_citations(MagicMock(spec=[])) == []

    def test_extracts_text_score_source_page(self, service):
        node = MagicMock()
        node.node.text = "Some context"
        node.node.metadata = {"file_name": "doc.pdf", "page_label": "3"}
        node.score = 0.92345

        response = MagicMock()
        response.source_nodes = [node]

        citations = service._extract_citations(response)

        assert len(citations) == 1
        assert citations[0]["text"] == "Some context"
        assert citations[0]["score"] == 0.9234
        assert citations[0]["source"] == "doc.pdf"
        assert citations[0]["page"] == "3"

    def test_truncates_text_to_300_chars(self, service):
        node = MagicMock()
        node.node.text = "x" * 500
        node.node.metadata = {}
        node.score = 0.5

        response = MagicMock()
        response.source_nodes = [node]

        assert len(service._extract_citations(response)[0]["text"]) == 300

    def test_missing_metadata_uses_defaults(self, service):
        node = MagicMock()
        node.node.text = "text"
        node.node.metadata = {}
        node.score = None

        response = MagicMock()
        response.source_nodes = [node]

        citation = service._extract_citations(response)[0]
        assert citation["source"] == "Unknown"
        assert citation["score"] == 0.0
        assert citation["page"] is None


class TestSaveChat:
    @pytest.mark.asyncio
    async def test_saves_to_db(self, service, db):
        await service._save_chat(1, "What?", "Answer.", [])
        db.add.assert_called_once()
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_serialises_citations_as_json(self, service, db):
        citations = [{"text": "x", "score": 0.9, "source": "f.pdf"}]
        await service._save_chat(1, "Q?", "A.", citations)

        saved = db.add.call_args[0][0]
        assert saved.citations == json.dumps(citations)
        assert saved.document_id == 1


class TestStreamQuery:
    @pytest.mark.asyncio
    async def test_yields_token_events(self, service):
        mock_resp = make_mock_response(["Hello", " world"])

        with patch("app.services.query_service.get_vector_store"), \
             patch("asyncio.to_thread", new=AsyncMock(side_effect=[MagicMock(), mock_resp])):
            events = [e async for e in service.stream_query(1, "What?")]

        token_events = [e for e in events if '"token"' in e]
        assert len(token_events) == 2
        assert json.loads(token_events[0].removeprefix("data: "))["token"] == "Hello"

    @pytest.mark.asyncio
    async def test_yields_citations_event(self, service):
        mock_resp = make_mock_response(["Answer"])

        with patch("app.services.query_service.get_vector_store"), \
             patch("asyncio.to_thread", new=AsyncMock(side_effect=[MagicMock(), mock_resp])):
            events = [e async for e in service.stream_query(1, "What?")]

        assert any('"citations"' in e for e in events)

    @pytest.mark.asyncio
    async def test_yields_done_event(self, service):
        mock_resp = make_mock_response([])

        with patch("app.services.query_service.get_vector_store"), \
             patch("asyncio.to_thread", new=AsyncMock(side_effect=[MagicMock(), mock_resp])):
            events = [e async for e in service.stream_query(1, "What?")]

        assert any("[DONE]" in e for e in events)

    @pytest.mark.asyncio
    async def test_saves_chat_after_streaming(self, service, db):
        mock_resp = make_mock_response(["The answer"])

        with patch("app.services.query_service.get_vector_store"), \
             patch("asyncio.to_thread", new=AsyncMock(side_effect=[MagicMock(), mock_resp])):
            async for _ in service.stream_query(1, "What?"):
                pass

        db.add.assert_called_once()
        db.commit.assert_awaited_once()