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

- [ ] Initialize backend with FastAPI + Poetry/pip
- [ ] Initialize frontend with Vite + React + TypeScript (can reuse from RAG-QA-SYSTEM)
- [ ] Configure `.env.example` with all required vars
- [ ] Set up PostgreSQL with Docker Compose
- [ ] Set up ChromaDB with Docker Compose
- [ ] Write `CLAUDE.md`
- [ ] Confirm both servers run locally

---

## Phase 1: LlamaIndex Core Setup

**Goal:** LlamaIndex wired up with provider and vector store.

- [ ] Install LlamaIndex (`llama-index-core`, `llama-index-vector-stores-chroma`)
- [ ] Install LlamaIndex LLM integrations (`llama-index-llms-ollama`, `llama-index-llms-openai`, `llama-index-llms-gemini`)
- [ ] Install LlamaIndex embedding integrations (`llama-index-embeddings-ollama`, `llama-index-embeddings-openai`, `llama-index-embeddings-gemini`)
- [ ] Configure `Settings` (global LlamaIndex settings — LLM + embed model)
- [ ] Provider factory — reads `LLM_PROVIDER` from env, sets `Settings.llm` and `Settings.embed_model`
- [ ] ChromaDB vector store setup via `ChromaVectorStore` + `StorageContext`
- [ ] Startup validation — fail fast if provider config missing
- [ ] Unit tests for provider factory

---

## Phase 2: Ingestion Pipeline

**Goal:** Upload a document and have it indexed via LlamaIndex.

- [ ] `SimpleDirectoryReader` wrapper for file ingestion
- [ ] URL ingestion via `TrafilaturaWebReader` or `BeautifulSoupWebReader`
- [ ] `VectorStoreIndex.from_documents()` — parse → chunk → embed → store
- [ ] PostgreSQL `documents` table model + migration
- [ ] Ingestion service — orchestrates load → index → save metadata
- [ ] File size validation (max 50MB)
- [ ] File type validation (PDF, DOCX, PPTX, TXT, MD, URL)
- [ ] `POST /api/documents/upload` endpoint
- [ ] `POST /api/documents/url` endpoint
- [ ] `GET /api/documents` endpoint
- [ ] `DELETE /api/documents/{id}` endpoint
- [ ] Unit tests for ingestion service
- [ ] Integration tests for upload → index flow

---

## Phase 3: Query Pipeline

**Goal:** Ask a question, get a streamed answer with citations.

- [ ] `VectorStoreIndex.as_query_engine()` — basic retrieval
- [ ] Streaming query engine (`streaming=True`)
- [ ] Custom prompt template via `PromptTemplate`
- [ ] Citation extraction from `NodeWithScore` results
- [ ] Save Q&A to `chat_history` table
- [ ] Honest fallback when no relevant nodes found
- [ ] `POST /api/notebooks/{id}/chat` endpoint (SSE streaming)
- [ ] Unit tests for query service (mocked index)

---

## Phase 4: Advanced Retrieval (LlamaIndex Power Features)

**Goal:** Better answers using LlamaIndex advanced features.

- [ ] **HyDE** — `HyDEQueryTransform` for hypothetical document embeddings
- [ ] **Reranking** — `SentenceTransformerRerank` or `LLMRerank` to re-score chunks
- [ ] **Multi-query** — `MultiStepQueryEngine` or query decomposition
- [ ] **Sub-question engine** — `SubQuestionQueryEngine` for multi-document queries
- [ ] Toggle between basic and advanced retrieval via env var
- [ ] A/B comparison endpoint to see retrieval difference

---

## Phase 5: Agentic Flow

**Goal:** ReAct agent that uses RAG as one tool among many.

- [ ] Define RAG tool — wraps query engine as a `FunctionTool`
- [ ] Define web search tool — Tavily or DuckDuckGo
- [ ] Define calculator tool
- [ ] `ReActAgent` wiring all tools together
- [ ] Streaming agent responses via SSE
- [ ] `POST /api/agent/chat` endpoint
- [ ] Unit tests for agent tool wrappers

---

## Phase 6: Frontend

**Goal:** UI connected to backend (can reuse Phase 4 frontend from RAG-QA-SYSTEM).

- [ ] Reuse or rebuild DocumentSidebar, UploadModal, NotebookView, ChatMessage
- [ ] Add retrieval mode toggle (basic / HyDE / reranking)
- [ ] Add agent chat tab separate from notebook chat
- [ ] Source citation display with node scores

---

## Phase 7: Coverage & Launch

**Goal:** 80%+ test coverage, clean build, ready to use.

- [ ] Run pytest coverage — fix gaps to reach 80%+
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
