import asyncio
import json
from collections.abc import AsyncGenerator

from llama_index.core import PromptTemplate, VectorStoreIndex
from llama_index.core.postprocessor import LLMRerank
from llama_index.core.query_engine import TransformQueryEngine
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.chromadb import get_vector_store
from app.core.config import settings
from app.models.chat_history import ChatHistory

# HyDEQueryTransform was removed from some LlamaIndex releases.
# Try the real import first; fall back to a manual implementation.
try:
    from llama_index.core.indices.query.query_transform.hyde import HyDEQueryTransform
except ImportError:
    try:
        from llama_index.core.indices.query.query_transform.base import (
            BaseQueryTransform,
        )
        from llama_index.core.schema import QueryBundle as _QueryBundle

        class HyDEQueryTransform(BaseQueryTransform):  # type: ignore[no-redef]
            """
            Manual HyDE: ask the LLM to generate a hypothetical answer,
            then embed that answer instead of (or alongside) the raw question.
            """

            def __init__(self, include_original: bool = True) -> None:
                super().__init__()
                self.include_original = include_original

            def _run(
                self, query_bundle: _QueryBundle, metadata: dict
            ) -> _QueryBundle:
                from llama_index.core import Settings as _Settings

                prompt = (
                    "Write a short passage that would answer the following question:\n\n"
                    f"Question: {query_bundle.query_str}\n\nPassage:"
                )
                hypothetical_doc = str(_Settings.llm.complete(prompt))
                embedding_strs = [hypothetical_doc]
                if self.include_original:
                    embedding_strs.append(query_bundle.query_str)
                return _QueryBundle(
                    query_str=query_bundle.query_str,
                    custom_embedding_strs=embedding_strs,
                )

    except ImportError:

        class HyDEQueryTransform:  # type: ignore[no-redef]
            """Stub — only reached if LlamaIndex query-transform base is absent."""

            def __init__(self, include_original: bool = True) -> None:
                self.include_original = include_original


QA_PROMPT = PromptTemplate(
    "Context information is below.\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "Given only the context above and not prior knowledge, answer the query.\n"
    "If the context does not contain enough information, respond with exactly: "
    "'I couldn't find relevant information in the document to answer your question.'\n"
    "Query: {query_str}\n"
    "Answer: "
)


class QueryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Query engine factory
    # ------------------------------------------------------------------

    def _build_query_engine(self, index, mode: str, streaming: bool = True):
        """
        Build a LlamaIndex query engine based on retrieval mode.

        Modes:
          basic       — plain vector similarity search
          hyde        — HyDE: generate a hypothetical answer, embed it, search
          rerank      — retrieve more nodes then re-score with LLMRerank
          hyde+rerank — HyDE first, then rerank
        """
        node_postprocessors = []

        if "rerank" in mode:
            node_postprocessors.append(LLMRerank(choice_batch_size=5, top_n=3))

        query_engine = index.as_query_engine(
            streaming=streaming,
            similarity_top_k=6 if node_postprocessors else 4,
            text_qa_template=QA_PROMPT,
            node_postprocessors=node_postprocessors or None,
        )

        if "hyde" in mode:
            hyde_transform = HyDEQueryTransform(include_original=True)
            query_engine = TransformQueryEngine(
                query_engine, query_transform=hyde_transform
            )

        return query_engine

    # ------------------------------------------------------------------
    # Streaming query (SSE)
    # ------------------------------------------------------------------

    async def stream_query(
        self, document_id: int, question: str, mode: str | None = None
    ) -> AsyncGenerator[str, None]:
        vector_store = get_vector_store()
        index = await asyncio.to_thread(VectorStoreIndex.from_vector_store, vector_store)

        query_engine = self._build_query_engine(
            index, mode or settings.retrieval_mode, streaming=True
        )
        streaming_response = await asyncio.to_thread(query_engine.query, question)

        full_answer = ""
        for token in streaming_response.response_gen:
            full_answer += token
            yield f"data: {json.dumps({'token': token})}\n\n"
            await asyncio.sleep(0)

        citations = self._extract_citations(streaming_response)
        yield f"data: {json.dumps({'citations': citations})}\n\n"

        await self._save_chat(document_id, question, full_answer, citations)

        yield "data: [DONE]\n\n"

    # ------------------------------------------------------------------
    # Non-streaming query (for comparison endpoint)
    # ------------------------------------------------------------------

    async def query_once(
        self, document_id: int, question: str, mode: str = "basic"
    ) -> dict:
        vector_store = get_vector_store()
        index = await asyncio.to_thread(VectorStoreIndex.from_vector_store, vector_store)

        query_engine = self._build_query_engine(index, mode, streaming=False)
        response = await asyncio.to_thread(query_engine.query, question)

        return {
            "answer": str(response),
            "citations": self._extract_citations(response),
            "mode": mode,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _extract_citations(self, response) -> list[dict]:
        if not hasattr(response, "source_nodes") or not response.source_nodes:
            return []
        return [
            {
                "text": node.node.text[:300],
                "score": round(node.score or 0.0, 4),
                "source": node.node.metadata.get("file_name", "Unknown"),
                "page": node.node.metadata.get("page_label"),
            }
            for node in response.source_nodes
        ]

    async def _save_chat(
        self,
        document_id: int,
        question: str,
        answer: str,
        citations: list[dict],
    ) -> None:
        chat = ChatHistory(
            document_id=document_id,
            question=question,
            answer=answer,
            citations=json.dumps(citations),
        )
        self.db.add(chat)
        await self.db.commit()

    async def get_history(self, document_id: int) -> list[ChatHistory]:
        result = await self.db.execute(
            select(ChatHistory)
            .where(ChatHistory.document_id == document_id)
            .order_by(ChatHistory.created_at.asc())
        )
        return list(result.scalars().all())
