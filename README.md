# DocuMind

> Upload your documents and chat with them using AI — powered by Corrective RAG, Groq LLM, and pgvector.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-purple)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red)

---

## What it does

DocuMind lets you upload any documents (PDF, DOCX, TXT, MD) and have an intelligent conversation with them. It uses **Corrective RAG** — a self-correcting retrieval pipeline that:

1. Retrieves relevant chunks from your documents
2. Grades them for relevance — if none are relevant, it **rewrites the question** and retries
3. Generates an answer grounded in your documents
4. Runs a **hallucination check** — if the answer isn't supported, it regenerates
5. Falls back to chitchat for greetings and small talk

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                     DocuMind                        │
│                                                     │
│  Streamlit UI (:8501)  ──►  FastAPI (:8000)         │
│                                 │                   │
│                        LangGraph CRAG Agent         │
│                                 │                   │
│                    ┌────────────┴────────────┐      │
│                    │                         │      │
│              pgvector (Postgres)          Groq LLM  │
│              Embeddings stored            Answers   │
└─────────────────────────────────────────────────────┘
```

### Tech stack

| Layer | Local Dev | Cloud (Insforge) |
|---|---|---|
| **LLM** | Groq (free) | Groq (free) |
| **Embeddings** | Ollama (`nomic-embed-text`) | Google (`gemini-embedding-001`) |
| **Vector DB** | Postgres + pgvector | Postgres + pgvector |
| **Agent** | LangGraph | LangGraph |
| **API** | FastAPI | FastAPI |
| **UI** | Streamlit | Streamlit |

---

## Project structure

```
documind/
├── agent/                  # LangGraph CRAG agent
│   ├── graph.py            # Graph wiring & conditional edges
│   ├── nodes.py            # Node functions (retrieve, grade, generate …)
│   ├── prompts.py          # All LLM prompts in one place
│   └── state.py            # Shared GraphState TypedDict
│
├── providers/              # Pluggable backends (swap via .env)
│   ├── embeddings.py       # ollama | google | openai
│   └── vectorstore.py      # pinecone | postgres
│
├── api.py                  # FastAPI — all REST endpoints
├── app.py                  # Streamlit — chat UI
├── ingest.py               # CLI ingestion (local folder or Google Drive)
│
├── Dockerfile.api          # Docker image for the API
├── Dockerfile.ui           # Docker image for the UI
├── docker-compose.yml      # Production compose (API + UI)
├── docker-compose.dev.yml  # Local dev compose (Postgres + pgAdmin)
│
├── pyproject.toml          # Dependencies (managed by uv)
├── Makefile                # One-word commands
└── .env.example            # All config options documented
```

---

## Quick start (local)

### Prerequisites

- [uv](https://docs.astral.sh/uv/) — Python package manager
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) — for Postgres
- [Ollama](https://ollama.com/) — for local embeddings

### 1. Clone and install

```bash
git clone https://github.com/your-username/documind.git
cd documind

# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install all dependencies
uv sync
```

### 2. Configure

```bash
cp .env.example .env
```

Open `.env` and fill in the required keys:

```bash
# Required
GROQ_API_KEY=gsk_...          # free at console.groq.com

# Choose your embedding provider
EMBED_PROVIDER=ollama          # local (default)
# EMBED_PROVIDER=google        # cloud (for Insforge deploy)
# GOOGLE_API_KEY=AIza...       # required if using google

# Choose your vector store
VECTOR_STORE=postgres          # recommended
POSTGRES_URL=postgresql://raguser:ragpass@localhost:5432/ragdb

# Or use Pinecone
# VECTOR_STORE=pinecone
# PINECONE_API_KEY=pcsk_...    # free at app.pinecone.io
```

### 3. Pull embedding model (if using Ollama)

```bash
ollama pull nomic-embed-text
```

### 4. Start Postgres

```bash
docker compose -f docker-compose.dev.yml up -d
```

### 5. Run the app

```bash
# Terminal 1 — API
make api

# Terminal 2 — UI
make chat
```

Open **http://localhost:8501**

---

## API reference

The FastAPI backend exposes these endpoints (Swagger UI at **http://localhost:8000/docs**):

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `POST` | `/chat` | Send a message, get an answer |
| `POST` | `/ingest/upload` | Upload files to server |
| `POST` | `/ingest/store/{upload_id}` | Trigger embedding + storage |
| `GET` | `/ingest/status/{job_id}` | Poll ingestion job progress |
| `GET` | `/ingest/jobs` | List all ingestion jobs |
| `GET` | `/documents` | List all stored documents |
| `DELETE` | `/documents/{source}` | Delete a document from the KB |

### Example

```bash
# Upload a file
curl -X POST http://localhost:8000/ingest/upload \
  -F "files=@report.pdf"
# → { "upload_id": "a3f1bc22", "files": ["report.pdf"] }

# Trigger storage
curl -X POST http://localhost:8000/ingest/store/a3f1bc22
# → { "job_id": "b7e29d11" }

# Poll progress
curl http://localhost:8000/ingest/status/b7e29d11
# → { "status": "done", "chunks_total": 342 }

# Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What does the report say about revenue?"}'
# → { "answer": "...", "steps": [...] }
```

---

## Switching providers

Everything is controlled by `.env` — no code changes needed.

### Embedding providers

```bash
# Local (default, needs Ollama running)
EMBED_PROVIDER=ollama
OLLAMA_EMBED_MODEL=nomic-embed-text

# Google (free, works on cloud)
EMBED_PROVIDER=google
GOOGLE_API_KEY=AIza...

# OpenAI
EMBED_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

### Vector stores

```bash
# Postgres + pgvector (recommended)
VECTOR_STORE=postgres
POSTGRES_URL=postgresql://user:pass@host:5432/db

# Pinecone
VECTOR_STORE=pinecone
PINECONE_API_KEY=pcsk_...
PINECONE_INDEX=documind-index
```

> **Important:** Always re-upload your documents after switching providers — embeddings from different models are incompatible.

---

## Deploy to Insforge

Insforge provides built-in Postgres + pgvector and Custom Compute for containers. No Ollama needed — use Google embeddings (free).

```bash
# 1. Install Insforge CLI
npm install -g @insforge/cli
insforge login

# 2. Link your project
insforge link <project-id>

# 3. Set environment variables
insforge secrets set GROQ_API_KEY=gsk_...
insforge secrets set GOOGLE_API_KEY=AIza...
insforge secrets set EMBED_PROVIDER=google
insforge secrets set VECTOR_STORE=postgres
insforge secrets set POSTGRES_URL=postgresql://...   # from Insforge dashboard
insforge secrets set EMBED_DIM=768

# 4. Deploy
insforge compute deploy --name documind-api --dockerfile Dockerfile.api --port 8000
insforge secrets set API_URL=https://documind-api.insforge.app
insforge compute deploy --name documind-ui  --dockerfile Dockerfile.ui  --port 8501
```

---

## Available commands

```bash
make install          # Install dependencies
make api              # Start FastAPI backend  (localhost:8000)
make chat             # Start Streamlit UI     (localhost:8501)
make ingest SOURCE=./your-docs   # Ingest a local folder
make ingest-drive ID=<folder-id> # Ingest from Google Drive
```

---

## Environment variables

See [`.env.example`](.env.example) for the full list with descriptions.

| Variable | Required | Default | Description |
|---|---|---|---|
| `GROQ_API_KEY` | ✅ | — | Groq API key |
| `GROQ_MODEL` | | `llama-3.1-8b-instant` | Groq model |
| `EMBED_PROVIDER` | | `ollama` | `ollama` \| `google` \| `openai` |
| `VECTOR_STORE` | | `pinecone` | `pinecone` \| `postgres` |
| `POSTGRES_URL` | if postgres | — | Postgres connection string |
| `PINECONE_API_KEY` | if pinecone | — | Pinecone API key |
| `GOOGLE_API_KEY` | if google | — | Google AI API key |
| `EMBED_DIM` | | `768` | Embedding dimension |
| `CHUNK_SIZE` | | `400` | Words per chunk |
| `API_URL` | | `http://localhost:8000` | FastAPI base URL for UI |

---

## License

MIT
