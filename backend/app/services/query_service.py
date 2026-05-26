import asyncio
import json
from collections.abc import AsyncGenerator

from llama_index.core import PromptTemplate, VectorStoreIndex
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.chromadb import get_vector_store
from app.models.chat_history import ChatHistory

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

    async def stream_query(
        self, document_id: int, question: str
    ) -> AsyncGenerator[str, None]:
        # Load existing index from ChromaDB (no re-embedding)
        vector_store = get_vector_store()
        index = await asyncio.to_thread(
            VectorStoreIndex.from_vector_store, vector_store
        )

        query_engine = index.as_query_engine(
            streaming=True,
            similarity_top_k=4,
            text_qa_template=QA_PROMPT,
        )

        # Blocking query — run in thread pool
        streaming_response = await asyncio.to_thread(query_engine.query, question)

        # Stream tokens to client
        full_answer = ""
        for token in streaming_response.response_gen:
            full_answer += token
            yield f"data: {json.dumps({'token': token})}\n\n"
            await asyncio.sleep(0)  # yield control between tokens

        # Send citations
        citations = self._extract_citations(streaming_response)
        yield f"data: {json.dumps({'citations': citations})}\n\n"

        # Persist Q&A
        await self._save_chat(document_id, question, full_answer, citations)

        yield "data: [DONE]\n\n"

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