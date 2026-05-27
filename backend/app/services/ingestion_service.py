import asyncio
import os
import tempfile
from pathlib import Path

from fastapi import UploadFile
from llama_index.core import VectorStoreIndex
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.readers.web import BeautifulSoupWebReader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.chromadb import get_chroma_client, get_storage_context
from app.models.document import Document

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt", ".md"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


class IngestionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # File ingestion
    # ------------------------------------------------------------------

    async def ingest_file(self, file: UploadFile) -> Document:
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: {suffix!r}. "
                f"Allowed: {sorted(SUPPORTED_EXTENSIONS)}"
            )

        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise ValueError(
                f"File exceeds 50 MB limit ({len(content) / 1_048_576:.1f} MB)"
            )

        documents = self._load_file(content, suffix)
        source = file.filename or "unknown"
        for doc in documents:
            doc.metadata["rag_source"] = source

        storage_context = get_storage_context()
        await asyncio.to_thread(
            VectorStoreIndex.from_documents,
            documents,
            storage_context=storage_context,
        )

        doc = Document(
            filename=file.filename or "unknown",
            file_type=suffix.lstrip("."),
            source=file.filename or "unknown",
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    def _load_file(self, content: bytes, suffix: str) -> list:
        """Save content to a temp file and load with the best available reader."""
        tmp_path: str | None = None
        try:
            # delete=False required on Windows — file can't be opened twice
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            if suffix == ".pdf":
                return self._load_pdf(tmp_path)

            return SimpleDirectoryReader(input_files=[tmp_path]).load_data()
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @staticmethod
    def _text_is_readable(text: str) -> bool:
        """Return True if text looks like real extracted content (not raw PDF binary)."""
        sample = text[:500]
        if not sample:
            return False
        printable = sum(1 for c in sample if c.isprintable() or c in '\n\t\r ')
        return (printable / len(sample)) > 0.8

    def _load_pdf(self, path: str) -> list:
        """Use PyMuPDF for PDFs — handles more types than the default parser."""
        try:
            from llama_index.readers.file import PyMuPDFReader

            docs = PyMuPDFReader().load(file_path=path)

            # FIX: PyMuPDFReader stores bytes instead of str in Document.text.
            # Pydantic auto-decodes valid UTF-8, but we guard against edge cases.
            for doc in docs:
                if isinstance(doc.text, bytes):
                    doc.text = doc.text.decode("utf-8", errors="replace")

            # Drop blank pages and pages with garbled/binary content
            docs = [d for d in docs if d.text.strip() and self._text_is_readable(d.text)]

            if docs:
                return docs
        except Exception:
            pass

        # Fallback to pypdf via SimpleDirectoryReader
        try:
            fallback_docs = SimpleDirectoryReader(input_files=[path]).load_data()
            # Validate fallback output — reject if it looks like raw PDF binary
            fallback_docs = [
                d for d in fallback_docs
                if d.text.strip() and self._text_is_readable(d.text)
            ]
            if fallback_docs:
                return fallback_docs
        except Exception:
            pass

        raise ValueError(
            "Could not extract readable text from this PDF. "
            "It may be scanned/image-based and require OCR."
        )

    # ------------------------------------------------------------------
    # URL ingestion
    # ------------------------------------------------------------------

    async def ingest_url(self, url: str) -> Document:
        if not url.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")

        documents = await asyncio.to_thread(
            BeautifulSoupWebReader().load_data, urls=[url]
        )
        for doc in documents:
            doc.metadata["rag_source"] = url

        storage_context = get_storage_context()
        await asyncio.to_thread(
            VectorStoreIndex.from_documents,
            documents,
            storage_context=storage_context,
        )

        doc = Document(filename=url, file_type="url", source=url)
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    # ------------------------------------------------------------------
    # List / delete
    # ------------------------------------------------------------------

    async def list_documents(self) -> list[Document]:
        result = await self.db.execute(
            select(Document).order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    def _delete_from_chroma(self, source: str) -> None:
        """Delete all ChromaDB nodes matching this document by rag_source or file_name."""
        try:
            client = get_chroma_client()
            collection = client.get_or_create_collection("documents")
            ids_to_delete: list[str] = []

            # Match by rag_source (set during ingestion)
            try:
                results = collection.get(where={"rag_source": source})
                ids_to_delete.extend(results.get("ids", []))
            except Exception:
                pass

            # Also match by file_name (set by SimpleDirectoryReader/PyMuPDFReader)
            # This catches chunks that were ingested without rag_source metadata
            try:
                results = collection.get(where={"file_name": source})
                ids_to_delete.extend(results.get("ids", []))
            except Exception:
                pass

            if ids_to_delete:
                # Deduplicate
                collection.delete(ids=list(set(ids_to_delete)))
        except Exception:
            pass  # Best-effort cleanup — log in production

    async def delete_document(self, doc_id: int) -> None:
        doc = await self.db.get(Document, doc_id)
        if doc is None:
            raise ValueError(f"Document {doc_id} not found")
        await asyncio.to_thread(self._delete_from_chroma, doc.source)
        await self.db.delete(doc)
        await self.db.commit()