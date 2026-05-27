# Task List

> Implementation tasks broken into phases. Update status as work progresses.
> Each task should be completable in one session (roughly 2–4 hours of work).

**Project:** RAG-QA-SYSTEM-LLAMAINDEX
**Last updated:** 2026-05-26

---

## Status Key

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[~]` | In progress |
| `[x]` | Done |
| `[!]` | Blocked |
| `[-]` | Skipped / cancelled |

---

## Phase 0: Setup

**Goal:** Working project skeleton, both servers running, git initialized.

- [x] Initialize backend with FastAPI + Poetry/pip
- [x] Initialize frontend with Vite + React + TypeScript (can reuse from RAG-QA-SYSTEM)
- [x] Configure `.env.example` with all required vars
- [x] Set up PostgreSQL with Docker Compose
- [x] Set up ChromaDB with Docker Compose
- [x] Write `CLAUDE.md`
- [x] Confirm both servers run locally

---

## Phase 1: LlamaIndex Core Setup

**Goal:** LlamaIndex wired up with provider and vector store.

- [x] Install LlamaIndex (`llama-index-core`, `llama-index-vector-stores-chroma`)
- [x] Install LlamaIndex LLM integrations (`llama-index-llms-ollama`, `llama-index-llms-openai`, `llama-index-llms-gemini`)
- [x] Install LlamaIndex embedding integrations (`llama-index-embeddings-ollama`, `llama-index-embeddings-openai`, `llama-index-embeddings-gemini`)
- [x] Configure `Settings` (global LlamaIndex settings — LLM + embed model)
- [x] Provider factory — reads `LLM_PROVIDER` from env, sets `Settings.llm` and `Settings.embed_model`
- [x] ChromaDB vector store setup via `ChromaVectorStore` + `StorageContext`
- [x] Startup validation — fail fast if provider config missing
- [x] Unit tests for provider factory

---

## Phase 2: Ingestion Pipeline

**Goal:** Upload a document and have it indexed via LlamaIndex.

- [x] `SimpleDirectoryReader` wrapper for file ingestion
- [x] URL ingestion via `TrafilaturaWebReader` or `BeautifulSoupWebReader`
- [x] `VectorStoreIndex.from_documents()` — parse → chunk → embed → store
- [x] PostgreSQL `documents` table model + migration
- [x] Ingestion service — orchestrates load → index → save metadata
- [x] File size validation (max 50MB)
- [x] File type validation (PDF, DOCX, PPTX, TXT, MD, URL)
- [x] `POST /api/documents/upload` endpoint
- [x] `POST /api/documents/url` endpoint
- [x] `GET /api/documents` endpoint
- [x] `DELETE /api/documents/{id}` endpoint
- [x] Unit tests for ingestion service
- [x] Integration tests for upload → index flow

---

## Phase 3: Query Pipeline

**Goal:** Ask a question, get a streamed answer with citations.

- [x] `VectorStoreIndex.as_query_engine()` — basic retrieval
- [x] Streaming query engine (`streaming=True`)
- [x] Custom prompt template via `PromptTemplate`
- [x] Citation extraction from `NodeWithScore` results
- [x] Save Q&A to `chat_history` table
- [x] Honest fallback when no relevant nodes found
- [x] `POST /api/notebooks/{id}/chat` endpoint (SSE streaming)
- [x] Unit tests for query service (mocked index)

---

## Phase 4: Advanced Retrieval (LlamaIndex Power Features)

**Goal:** Better answers using LlamaIndex advanced features.

- [x] **HyDE** — `HyDEQueryTransform` for hypothetical document embeddings
- [x] **Reranking** — `SentenceTransformerRerank` or `LLMRerank` to re-score chunks
- [ ] **Multi-query** — `MultiStepQueryEngine` or query decomposition
- [ ] **Sub-question engine** — `SubQuestionQueryEngine` for multi-document queries
- [x] Toggle between basic and advanced retrieval via env var
- [x] A/B comparison endpoint to see retrieval difference

---

## Phase 5: Agentic Flow

**Goal:** ReAct agent that uses RAG as one tool among many.

- [x] Define RAG tool — wraps query engine as a `FunctionTool`
- [x] Define web search tool — Tavily or DuckDuckGo
- [x] Define calculator tool
- [x] `ReActAgent` wiring all tools together
- [x] Streaming agent responses via SSE
- [x] `POST /api/agent/chat` endpoint
- [x] Unit tests for agent tool wrappers

---

## Phase 6: Frontend

**Goal:** UI connected to backend (can reuse Phase 4 frontend from RAG-QA-SYSTEM).

- [x] Reuse or rebuild DocumentSidebar, UploadModal, NotebookView, ChatMessage
- [x] Add retrieval mode toggle (basic / HyDE / reranking)
- [x] Add agent chat tab separate from notebook chat
- [x] Source citation display with node scores

---

## Phase 7: Coverage & Launch

**Goal:** 80%+ test coverage, clean build, ready to use.

- [~] Run pytest coverage — fix gaps to reach 80%+ (Currently at 78%)
- [ ] Final README update
- [ ] Tag `v1.0.0`

---

## Backlog (Unscheduled)

- [ ] LlamaIndex evaluation with RAGAS
- [ ] Observability with LlamaTrace / Langfuse
- [ ] Fine-tuned embedding model
- [ ] Knowledge graph index (`KnowledgeGraphIndex`)
- [ ] Multi-document summarization

---

## Completed

<!-- Move finished phases here as work progresses -->
