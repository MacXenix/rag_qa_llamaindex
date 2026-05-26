# CLAUDE.md

> Project-level instructions for Claude Code. Claude reads this at the start of every session.

---

## Project Overview

**Name:** RAG-QA-SYSTEM-LLAMAINDEX
**Type:** Personal Knowledge Base Web App (v2)
**Status:** In Progress

A rebuild of RAG-QA-SYSTEM using **LlamaIndex** instead of manual embeddings and retrieval. Same product — upload documents (PDF, DOCX, PPTX, TXT, MD, URLs), ask questions, get streamed AI answers with source citations. Extended with advanced retrieval (HyDE, reranking) and a ReAct agent.

**Previous project:** `D:\Projects\Personal\Side Projects\AI\RAG\RAG-QA-SYSTEM` — reference for patterns but LlamaIndex changes the approach significantly.

---

## Working Style

- Guide step by step — provide code file by file
- Do NOT edit files directly unless explicitly asked
- User pastes the code themselves

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language (BE) | Python 3.11+ |
| Framework (BE) | FastAPI |
| RAG Framework | LlamaIndex (llama-index-core) |
| LLM Providers | OpenAI / Ollama / Gemini (via LlamaIndex integrations) |
| Vector Store | ChromaDB (`llama-index-vector-stores-chroma`) |
| Relational DB | PostgreSQL 15 |
| ORM | SQLAlchemy (async) |
| Streaming | Server-Sent Events (SSE) |
| Language (FE) | TypeScript + React + Vite |

---

## Key Docs

| Document | Purpose |
|----------|---------|
| `docs/ARCHITECTURE.md` | LlamaIndex concepts, system design, data flow |
| `docs/TASK_LIST.md` | All phases and tasks — check this every session |
| `docs/HANDOVER.md` | Current state, lessons from v1, what to do next |

**Read all three at the start of every session before doing anything.**

---

## LlamaIndex Core Pattern

```python
from llama_index.core import Settings, VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

# Set once at startup — all components use it automatically
Settings.llm = Ollama(model="llama3.2")
Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text")

# Ingest
documents = SimpleDirectoryReader(input_files=["doc.pdf"]).load_data()
index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)

# Query
query_engine = index.as_query_engine(streaming=True)
response = query_engine.query("What is this about?")
```

---

## Environment Variables

```bash
LLM_PROVIDER=ollama
OPENAI_API_KEY=
GEMINI_API_KEY=
OLLAMA_BASE_URL=http://localhost:11434
DATABASE_URL=postgresql+asyncpg://ragqa:ragqa@localhost:5432/ragqa
CHROMA_HOST=localhost
CHROMA_PORT=8001
TAVILY_API_KEY=               # optional, for agent web search
```

---

## Development Commands

```bash
# Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
pnpm dev

# Docker (PostgreSQL + ChromaDB)
docker compose up -d

# Tests
cd backend && pytest --cov=app tests/
```

---

## Context Compaction — Auto-update Handover

**When approaching context limits (context window ~80% full), BEFORE compaction occurs:**

1. Update `docs/HANDOVER.md` with:
   - Current phase and task being worked on
   - What was just completed (bullet list)
   - What is in progress (exact file, function, or step)
   - What to do next (specific next action)
   - Any errors encountered and how they were fixed
   - Any decisions made and why
2. Update `docs/TASK_LIST.md` — mark completed tasks `[x]` and in-progress tasks `[~]`
3. Commit both files:
   ```bash
   git add docs/HANDOVER.md docs/TASK_LIST.md
   git commit -m "docs: update handover before context compaction"
   ```

This ensures the next session can resume exactly where this one left off without losing context.

---

## Conventions

- Minimum 80% test coverage
- Mock LlamaIndex components in tests — never call real APIs
- AAA pattern: Arrange → Act → Assert
- Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`
- Functions under 50 lines, files under 800 lines
- pydantic-settings: use `settings_customise_sources` to ignore system env vars

---

## Lessons from v1

- ChromaDB Docker image version must match pip package version
- `AsyncMock` child attributes are also async — mock `scalar_one_or_none` as `MagicMock` explicitly
- Use `app.dependency_overrides[get_db]` not `patch` for FastAPI dependency mocking
- Set `OLLAMA_MODELS=D:\DevTools\Ollama\models` — models stored on D drive
- Ollama must be running (`ollama serve`) before starting the backend
