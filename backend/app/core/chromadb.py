import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext

from app.core.config import settings


def get_chroma_client() -> chromadb.HttpClient:
    return chromadb.HttpClient(
        host=settings.chroma_host,
        port=settings.chroma_port,
    )


def get_vector_store(collection_name: str = "documents") -> ChromaVectorStore:
    client = get_chroma_client()
    collection = client.get_or_create_collection(collection_name)
    return ChromaVectorStore(chroma_collection=collection)


def get_storage_context(collection_name: str = "documents") -> StorageContext:
    vector_store = get_vector_store(collection_name)
    return StorageContext.from_defaults(vector_store=vector_store)