# Handover

> Snapshot of project state for a new session, a new developer, or a new AI context window.
> Update this whenever the project state changes significantly.

**Last updated:** 2026-05-26
**Updated by:** Claude (project planning session)

---

## Current State

**Phase:** Not started — planning complete, ready for implementation
**Milestone:** Phase 0 setup
**Deadline:** None

### What works right now

- [ ] Nothing yet — project just planned

### What's in progress

None — starting fresh.

### What's blocked

None.

---

## Project Goal

Rebuild RAG-QA-SYSTEM using **LlamaIndex** instead of manual embedding/retrieval. Same product (upload docs, ask questions, get answers with citations) but using LlamaIndex abstractions. Then extend with:
- Advanced retrieval: HyDE, reranking, multi-query
- Agentic flows: ReAct agent with RAG + web search tools

**Learning goal:** Understand LlamaIndex well enough to use it in production.

---

## Prior Art

This is v2 of `RAG-QA-SYSTEM` (in `D:\Projects\Personal\Side Projects\AI\RAG\RAG-QA-SYSTEM`).

Key things learned from v1:
- ChromaDB version must match between Docker and pip
- pydantic-settings v2: use `SettingsConfigDict`, use `settings_customise_sources` to ignore system env vars
- FastAPI dependency injection in tests: use `app.dependency_overrides[get_db]` not `patch`
- `AsyncMock` makes child attributes also async — mock `scalar_one_or_none` as `MagicMock` explicitly
- SSE streaming: use `StreamingResponse` with `media_type="text/event-stream"`
- LLM_PROVIDER system env var can override .env — fixed via `settings_customise_sources`

---

## Architecture Summary

```
File upload → SimpleDirectoryReader → VectorStoreIndex (ChromaDB)
Question → QueryEngine (streaming) → NodeWithScore → Citations
Agent question → ReActAgent → Tools (RAG, WebSearch, Calculator)
```

Full details: `docs/ARCHITECTURE.md`

---

## Environment Notes

| Environment | Status | Notes |
|-------------|--------|-------|
| Local | Not set up | Docker for ChromaDB + PG |

### Required env vars (`backend/.env`)

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

### Ollama models needed

```bash
ollama pull nomic-embed-text   # embeddings
ollama pull llama3.2           # chat
```

Ollama models stored at: `D:\DevTools\Ollama\models`
Set via: `OLLAMA_MODELS=D:\DevTools\Ollama\models` (Machine env var)

---

## What to do next

1. Phase 0 — Initialize project (FastAPI + Vite + Docker)
2. Phase 1 — LlamaIndex core setup (Settings, provider factory, ChromaVectorStore)
3. Phase 2 — Ingestion with `SimpleDirectoryReader` + `VectorStoreIndex`
4. Phase 3 — Query with streaming `QueryEngine`
5. Phase 4 — Advanced retrieval (HyDE, reranking)
6. Phase 5 — ReAct agent

---

## Key LlamaIndex Packages

```
llama-index-core
llama-index-vector-stores-chroma
llama-index-llms-ollama
llama-index-llms-openai
llama-index-llms-gemini
llama-index-embeddings-ollama
llama-index-embeddings-openai
llama-index-embeddings-gemini
llama-index-readers-web          # URL ingestion
llama-index-postprocessor-flag-embedding-reranker  # reranking
```

## Context for AI

- Read `docs/ARCHITECTURE.md` first — it explains all LlamaIndex concepts used
- Read `docs/TASK_LIST.md` for the full phase breakdown
- The previous project is at `D:\Projects\Personal\Side Projects\AI\RAG\RAG-QA-SYSTEM` — reference it for patterns but don't copy blindly, LlamaIndex changes the approach significantly
- Provider config: use `llama_index.core.Settings` — set `Settings.llm` and `Settings.embed_model` once at startup
- No custom LLMProvider abstract class needed — LlamaIndex handles it
- ChromaDB version: check current Docker image version and match pip package
- pydantic-settings: same pattern as v1 — `settings_customise_sources` to ignore system env vars

---

## Contacts

| Role | Name | Contact |
|------|------|---------|
| Developer | — | — |
