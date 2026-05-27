from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.startup import run_startup


@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_startup()
    yield


app = FastAPI(
    title="RAG QA System",
    description="LlamaIndex-powered document Q&A",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.agent import router as agent_router  # noqa: E402
from app.api.documents import router as documents_router  # noqa: E402
from app.api.notebooks import router as notebooks_router  # noqa: E402

app.include_router(agent_router)
app.include_router(notebooks_router)
app.include_router(documents_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "provider": settings.llm_provider}