import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import get_db
from app.main import app
from app.models.document import Base

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_db() -> AsyncSession:
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_db: AsyncSession) -> AsyncClient:
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    with patch_ingestion():
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac

    app.dependency_overrides.clear()


def patch_ingestion():
    """Patch LlamaIndex calls so integration tests don't need Ollama/ChromaDB."""
    from contextlib import ExitStack
    from unittest.mock import AsyncMock, MagicMock, patch

    stack = ExitStack()
    stack.enter_context(
        patch(
            "app.services.ingestion_service.VectorStoreIndex.from_documents",
            return_value=MagicMock(),
        )
    )
    stack.enter_context(
        patch(
            "app.services.ingestion_service.get_storage_context",
            return_value=MagicMock(),
        )
    )
    stack.enter_context(
        patch(
            "app.services.ingestion_service.SimpleDirectoryReader",
            return_value=MagicMock(load_data=MagicMock(return_value=[MagicMock()])),
        )
    )
    stack.enter_context(
        patch(
            "asyncio.to_thread",
            new=AsyncMock(return_value=MagicMock()),
        )
    )
    return stack