# Simple-Agent

A FastAPI backend for **Retrieval-Augmented Generation (RAG)** — document chunking, vector search via Supabase pgvector, and citation-based Q&A with OpenAI or Anthropic.

## Features

- FastAPI with OpenAPI docs at `/docs`
- Supabase + pgvector semantic search
- OpenAI embeddings (`text-embedding-3-small`, 1536 dimensions)
- OpenAI or Anthropic for answer generation
- Citation extraction from LLM responses
- Static chat UI at `/chat`
- Terminal client via `chatbot.py`

## Architecture

```
Simple-Agent/
├── app/
│   ├── main.py              # FastAPI app (/seed, /answer, /healthz)
│   ├── core/
│   │   ├── config.py        # Environment settings
│   │   └── database.py      # Supabase client + vector search
│   ├── models/              # Request/response schemas
│   ├── services/
│   │   ├── rag.py           # RAG pipeline orchestration
│   │   ├── chunker.py       # Text splitting
│   │   ├── embedding.py     # OpenAI embeddings
│   │   └── chat.py          # LLM answer generation
│   └── data/
│       └── default_documents.py
├── sql/init_supabase.sql    # Database setup (run once in Supabase)
├── main.py                  # uvicorn entry point
├── chatbot.py               # Terminal RAG client
├── test_setup.py            # End-to-end setup verification
├── verify_rag.py            # Vector search proof script
└── check_dimensions.py      # Embedding dimension checker
```

## RAG Pipeline

```
POST /seed    →  chunk  →  embed  →  Supabase upsert
POST /answer  →  embed query  →  vector_search  →  LLM + citations
```

| Step | File |
|------|------|
| HTTP routes | `app/main.py` |
| Orchestration | `app/services/rag.py` |
| Chunking | `app/services/chunker.py` |
| Embeddings | `app/services/embedding.py` |
| LLM answers | `app/services/chat.py` |
| Database | `app/core/database.py` |
| Config | `app/core/config.py` |

Each `/answer` request is **stateless** — there is no conversation memory. Persistent knowledge lives in Supabase as document chunks.

## Prerequisites

- Python 3.11+
- [Supabase](https://supabase.com) project (free tier is sufficient)
- [OpenAI API key](https://platform.openai.com) (required for embeddings; also used for chat by default)
- [Anthropic API key](https://console.anthropic.com) (optional, chat only)

## Quick Start

### 1. Install dependencies

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in your Supabase and OpenAI credentials (see [Required credentials](#required-credentials) below).

### 3. Initialize Supabase

1. Create a project at [supabase.com](https://supabase.com)
2. Open **SQL Editor** in the dashboard
3. Paste and run the full contents of `sql/init_supabase.sql`

This creates the `rag_chunks` table (`VECTOR(1536)`), indexes, the `match_chunks()` search function, and RLS policies.

### 4. Verify setup

```bash
python test_setup.py
```

### 5. Start the server

```bash
uvicorn main:app --reload --port 8000
```

- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Chat UI: http://localhost:8000/chat

### 6. Seed and ask

```bash
curl -X POST http://localhost:8000/seed

curl -X POST http://localhost:8000/answer \
  -H "Content-Type: application/json" \
  -d '{"query": "Can I return shoes after 30 days?", "top_k": 6}'
```

Or use the terminal client:

```bash
python chatbot.py
```

## Required credentials

To run RAG locally you need **all** of the following:

| What | Why | Where to get it |
|------|-----|-----------------|
| **Supabase project** | Stores document vectors | [supabase.com](https://supabase.com) → New project |
| **SUPABASE_URL** | API endpoint | Supabase → Settings → API → Project URL |
| **SUPABASE_ANON_KEY** | Public client key | Supabase → Settings → API → anon public |
| **SUPABASE_SERVICE_ROLE_KEY** | Backend write/search access | Supabase → Settings → API → service_role secret |
| **OPENAI_API_KEY** | Embeddings + chat (default) | [platform.openai.com](https://platform.openai.com) → API Keys |
| **SQL init script run** | Creates tables and search function | Run `sql/init_supabase.sql` in Supabase SQL Editor |

Optional:

| What | When needed |
|------|-------------|
| **ANTHROPIC_API_KEY** | Only if `AI_PROVIDER=anthropic` (embeddings still use OpenAI) |

## API Reference

### Health check

```bash
curl http://localhost:8000/healthz
```

### Seed knowledge base

```bash
curl -X POST http://localhost:8000/seed
```

### Ask a question

```bash
curl -X POST http://localhost:8000/answer \
  -H "Content-Type: application/json" \
  -d '{"query": "What is your return policy?", "top_k": 6}'
```

Example response:

```json
{
  "text": "You can return unworn items within 30 days [policy_returns_v1#1]...",
  "citations": ["policy_returns_v1#1"],
  "debug": {
    "top_doc_ids": ["policy_returns_v1#1"],
    "latency_ms": 1250
  }
}
```

## Configuration

Settings are loaded from `.env` via `app/core/config.py`.

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_EMBED_MODEL` | `text-embedding-3-small` | Embedding model (1536 dims) |
| `OPENAI_CHAT_MODEL` | `gpt-4o` | Chat model when `AI_PROVIDER=openai` |
| `AI_PROVIDER` | `openai` | `openai` or `anthropic` |
| `chunk_size` | 400 | Approximate tokens per chunk (in code) |
| `chunk_overlap` | 60 | Overlap between chunks (in code) |
| `default_top_k` | 6 | Chunks retrieved per query (in code) |
| `temperature` | 0.1 | LLM temperature (in code) |

## Utility Scripts

| Script | Purpose |
|--------|---------|
| `test_setup.py` | Full setup verification (imports, DB, seed, query) |
| `verify_rag.py` | Prove vector similarity search is working |
| `check_dimensions.py` | Inspect embedding dimensions in Supabase |
| `chatbot.py` | Rich terminal UI for `/answer` |

## Docker

```bash
docker build -t simple-agent .
docker run -p 8080:8080 --env-file .env simple-agent
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for Cloud Run instructions.

## Development

```bash
black app/
isort app/
flake8 app/
```

## Source, copyright and attribution

Original project: [Elyon0517/Simple-Agent](https://github.com/Elyon0517/Simple-Agent), maintained by
[Elyon0517](https://github.com/Elyon0517). Project code is available under the [MIT License](LICENSE), subject to file-specific and third-party notices. Redistributions must preserve the applicable copyright and permission notices.

For articles, demos and derivatives, please credit the original project and link here.
That link is a courtesy request, not an extra restriction on an existing open-source license.
See [copyright and third-party boundaries](COPYRIGHT.md) and [citation metadata](CITATION.cff).
