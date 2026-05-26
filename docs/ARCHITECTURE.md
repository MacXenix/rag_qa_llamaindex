# Architecture

**Project:** RAG-QA-SYSTEM-LLAMAINDEX
**Last updated:** 2026-05-26

---

## Overview

A rebuild of RAG-QA-SYSTEM using **LlamaIndex** instead of raw ChromaDB + manual embeddings. The goal is to learn LlamaIndex abstractions while building the same product — then extend it with advanced retrieval (HyDE, reranking) and agentic flows (ReAct agent).

---

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Language (BE) | Python 3.11+ | |
| Framework (BE) | FastAPI | Same as v1 |
| RAG Framework | LlamaIndex (llama-index-core) | Replaces manual embed/search |
| LLM Providers | OpenAI / Ollama / Gemini | Via LlamaIndex integrations |
| Vector Store | ChromaDB | Via `llama-index-vector-stores-chroma` |
| Relational DB | PostgreSQL 15 | Document metadata, chat history |
| ORM | SQLAlchemy (async) | Same as v1 |
| Streaming | Server-Sent Events (SSE) | Same as v1 |
| Language (FE) | TypeScript + React + Vite | Reuse from v1 |

---

## LlamaIndex Key Concepts

```
Documents → Nodes → VectorStoreIndex → QueryEngine → Response
```

| Concept | What it is |
|---------|-----------|
| `Document` | Raw text loaded from a file or URL |
| `Node` | A chunk of a document with metadata |
| `VectorStoreIndex` | Embeds nodes and stores in ChromaDB |
| `QueryEngine` | Retrieves relevant nodes and generates answer |
| `NodeWithScore` | Retrieved node + similarity score (used for citations) |
| `Settings` | Global config — sets LLM and embedding model once |
| `PromptTemplate` | Customizes the prompt sent to the LLM |
| `ReActAgent` | Agent that uses tools in a think→act→observe loop |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        Frontend                          │
│          React + TypeScript (port 5173)                  │
│   DocumentSidebar │ UploadModal │ NotebookView           │
│   AgentChat │ RetrievalModeToggle                        │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP / SSE
┌────────────────────────▼────────────────────────────────┐
│                    FastAPI Backend                        │
│                      (port 8000)                         │
│                                                          │
│  /api/documents  ──► IngestionService                    │
│                         └─ SimpleDirectoryReader         │
│                         └─ VectorStoreIndex              │
│                                                          │
│  /api/notebooks  ──► QueryService                        │
│                         └─ QueryEngine (streaming)       │
│                         └─ NodeWithScore → citations     │
│                                                          │
│  /api/agent      ──► AgentService                        │
│                         └─ ReActAgent                    │
│                         └─ Tools: RAG, WebSearch, Calc   │
└──────────────┬──────────────────┬───────────────────────┘
               │                  │
┌──────────────▼──┐    ┌──────────▼──────────┐
│   PostgreSQL    │    │      ChromaDB        │
│  (port 5432)    │    │     (port 8001)      │
│  documents      │    │  VectorStoreIndex    │
│  notebooks      │    │  (nodes + vectors)   │
│  chat_history   │    └─────────────────────┘
└─────────────────┘
```

---

## Directory Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── documents.py      # Upload, list, delete
│   │   ├── notebooks.py      # Chat, history
│   │   ├── agent.py          # ReAct agent chat
│   │   └── providers.py      # Active provider info
│   ├── services/
│   │   ├── ingestion_service.py   # LlamaIndex indexing
│   │   ├── query_service.py       # LlamaIndex query engine
│   │   ├── agent_service.py       # ReAct agent
│   │   └── provider_factory.py    # Sets LlamaIndex Settings
│   ├── models/               # SQLAlchemy ORM
│   ├── schemas/              # Pydantic schemas
│   └── core/
│       ├── config.py         # pydantic-settings
│       ├── database.py       # async SQLAlchemy
│       ├── chromadb.py       # ChromaDB client
│       └── startup.py        # Validation + init
├── tests/
│   ├── unit/
│   └── integration/
└── requirements.txt

frontend/                     # Reuse from RAG-QA-SYSTEM or rebuild
```

---

## LlamaIndex vs Manual (v1 comparison)

| Feature | RAG-QA-SYSTEM (v1) | RAG-QA-SYSTEM-LLAMAINDEX (v2) |
|---------|-------------------|-------------------------------|
| Chunking | Manual `RecursiveCharacterTextSplitter` | LlamaIndex `SentenceSplitter` |
| Embedding | Manual `provider.embed()` loop | `Settings.embed_model` auto |
| Vector store | Raw ChromaDB API | `ChromaVectorStore` + `StorageContext` |
| Retrieval | Manual `collection.query()` | `QueryEngine.query()` |
| Citations | Manual metadata extraction | `NodeWithScore.node.metadata` |
| Advanced retrieval | ❌ Not implemented | ✅ HyDE, reranking, multi-query |
| Agents | ❌ Not implemented | ✅ ReAct agent with tools |

---

## Provider Configuration

LlamaIndex uses a global `Settings` object instead of a custom provider adapter:

```python
from llama_index.core import Settings
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

Settings.llm = Ollama(model="llama3.2", request_timeout=60.0)
Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text")
```

Set once at startup — all LlamaIndex components use it automatically.

---

## Data Flow

### Ingestion
```
File upload
  → SimpleDirectoryReader.load_data()
  → VectorStoreIndex.from_documents(documents, storage_context)
      → SentenceSplitter (chunking)
      → Settings.embed_model.get_text_embedding() (per chunk)
      → ChromaVectorStore.add() (vector storage)
  → Save Document metadata to PostgreSQL
```

### Query
```
User question
  → VectorStoreIndex.as_query_engine(streaming=True)
  → Settings.embed_model.get_query_embedding(question)
  → ChromaVectorStore.query() (top-k similar nodes)
  → [Optional] Reranker.postprocess_nodes()
  → Settings.llm.stream_complete(prompt + context)
  → Stream tokens via SSE
  → NodeWithScore.node.metadata → citations
  → Save to chat_history
```

### Agent
```
User question
  → ReActAgent.stream_chat(question)
      → Think: which tool to use?
      → Act: call RAG tool / web search / calculator
      → Observe: tool result
      → Repeat until answer
  → Stream final response via SSE
```

---

## Environment Variables

```bash
LLM_PROVIDER=ollama           # openai | ollama | gemini
OPENAI_API_KEY=
GEMINI_API_KEY=
OLLAMA_BASE_URL=http://localhost:11434
DATABASE_URL=postgresql+asyncpg://ragqa:ragqa@localhost:5432/ragqa
CHROMA_HOST=localhost
CHROMA_PORT=8001
TAVILY_API_KEY=               # optional, for web search tool
```

---

## Key Differences from v1

1. **No custom LLMProvider** — LlamaIndex `Settings` replaces the abstract provider pattern
2. **No manual chunking** — LlamaIndex handles it via `SentenceSplitter`
3. **No manual embedding loop** — `VectorStoreIndex.from_documents()` handles it
4. **Citations via NodeWithScore** — cleaner than manual metadata extraction
5. **Advanced retrieval built-in** — HyDE, reranking, sub-questions are LlamaIndex features
6. **ReAct agent** — new capability not in v1
