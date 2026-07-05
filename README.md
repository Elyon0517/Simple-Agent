# Simple-Agent

A Python project with two complementary layers:

1. **RAG backend** — FastAPI + Supabase pgvector for document retrieval and citation-based Q&A
2. **Multi-agent runtime** — Google ADK orchestrator that routes requests to specialist agents (e.g. SPX market analysis)

The two systems share the repo but use different config modules and entry points. RAG and Agent are **not wired together yet**.

## Features

### RAG

- FastAPI with OpenAPI docs (`/docs`)
- Supabase + pgvector semantic search
- OpenAI or Anthropic for answer generation
- Chunking, embedding, citation extraction
- Static chat UI at `/chat`
- Terminal client via `chatbot.py`

### Agent (ADK)

- Orchestrator → specialist routing (`orchestrator` → `market_analysis_agent`)
- Structured JSON output via Pydantic schema
- Session memory via ADK `InMemoryRunner` (in-process, not persisted)
- CLI: `app/chat_cli.py`
- HTTP routes defined under `app/api/` (not mounted on the RAG FastAPI app yet)

## Architecture

```
Simple-Agent/
├── app/
│   ├── main.py                 # RAG FastAPI app (/seed, /answer, /healthz)
│   ├── core/                   # RAG config + Supabase client
│   ├── models/                 # RAG request/response schemas
│   ├── services/               # RAG pipeline (chunk, embed, search, chat)
│   ├── data/                   # Default seed documents
│   ├── ai/
│   │   ├── agents/             # orchestrator + market_analysis agents
│   │   ├── runtime/            # TextRuntimeService (ADK runner)
│   │   ├── sessions/           # ADK session wrapper
│   │   └── context/            # User message builder
│   ├── api/                    # Agent HTTP routes (chat stream, sessions)
│   ├── chat_cli.py             # Interactive agent CLI
│   └── run_local_test.py       # Agent smoke test
├── config/settings.py          # Agent / ADK settings
├── sql/init_supabase.sql       # Supabase schema for RAG
├── main.py                     # uvicorn entry (re-exports app.main:app)
├── chatbot.py                  # RAG terminal client
├── test_setup.py               # RAG end-to-end verification
├── verify_rag.py               # Vector search proof script
└── check_dimensions.py         # Embedding dimension checker
```

## Prerequisites

- Python 3.11+
- **RAG:** Supabase project, OpenAI API key (Anthropic optional for chat)
- **Agent:** Google Gemini API key, `google-adk` and `google-genai` packages

## Quick Start — RAG

### 1. Install dependencies

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

Create `.env` in the project root with RAG variables:

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

OPENAI_API_KEY=sk-your_openai_key_here
OPENAI_EMBED_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o
AI_PROVIDER=openai

ENVIRONMENT=development
LOG_LEVEL=INFO
```

Optional Anthropic chat provider:

```env
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_anthropic_key_here
ANTHROPIC_CHAT_MODEL=claude-3-5-sonnet-20240620
OPENAI_API_KEY=sk-your_openai_key_here
```

Embeddings always use OpenAI regardless of chat provider.

### 3. Initialize Supabase

1. Open Supabase Dashboard → SQL Editor
2. Paste and run the full contents of `sql/init_supabase.sql`

This creates the `rag_chunks` table with `VECTOR(1536)` (matching `text-embedding-3-small`), indexes, `match_chunks()` RPC, and RLS policies.

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

## Quick Start — Agent (ADK)

### 1. Install ADK dependencies

`requirements.txt` covers the RAG stack only. For agents, also install:

```bash
pip install google-adk google-genai
```

### 2. Configure environment

Copy agent variables into `.env` (see `.env.example`):

```env
ADK_APP_NAME=market_agent
APP_VERSION=0.1.0
EXPOSE_API_DOCS=true
AGENT_THINKING_ENABLED=true

GOOGLE_GENAI_USE_VERTEXAI=0
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_TEXT_MODEL_DEFAULT=gemini-2.5-flash

OPENAI_API_KEY=
OPENAI_TEXT_MODEL_DEFAULT=gpt-4o-mini
OPENAI_TEXT_MODEL_CHEAP=gpt-4o-mini
OPENAI_TEXT_MODEL_HEAVY=gpt-4o
OPENAI_EMBED_MODEL_DEFAULT=text-embedding-3-small
OPENAI_IMAGE_MODEL_DEFAULT=gpt-image-1
OPENAI_TTS_MODEL_DEFAULT=gpt-4o-mini-tts
OPENAI_REALTIME_MODEL_DEFAULT=gpt-4o-realtime-preview
```

Agent settings are loaded from `config/settings.py`. RAG settings come from `app/core/config.py`. A single `.env` can hold both sets of variables.

### 3. Run the CLI

```bash
python -m app.chat_cli
```

Creates an ADK session, then streams orchestrator / specialist responses in the terminal.

### 4. Run the local test

```bash
python -m app.run_local_test
```

Sends a sample SPX analysis prompt and validates output against `MarketAnalysisResult`.

### Agent HTTP API (not mounted yet)

Routes are defined in `app/api/`:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/sessions` | Create ADK session |
| POST | `/chat/stream` | SSE stream from orchestrator |

To expose them, mount `app.api.router.api_router` on a FastAPI app (separate from or merged with `app/main.py`).

## RAG Pipeline

```
/seed  →  chunker  →  embedding  →  Supabase upsert
/answer  →  embed query  →  vector_search  →  LLM + citations
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

RAG has **no conversation memory** — each `/answer` call is stateless. Persistent storage is the document knowledge base in Supabase.

## Agent Pipeline

```
user message  →  TextRuntimeService  →  InMemoryRunner
  →  orchestrator_agent  →  market_analysis_agent  →  JSON response
```

| Step | File |
|------|------|
| Runtime | `app/ai/runtime/text_runtime_service.py` |
| Orchestrator | `app/ai/agents/orchestrator/` |
| Specialist | `app/ai/agents/market_analysis/` |
| Output schema | `app/ai/agents/market_analysis/schema.py` |
| Session memory | `app/ai/sessions/adk_session_service.py` |
| Config | `config/settings.py` |

Agent **memory** is ADK session history keyed by `user_id` + `session_id`. The current `InMemoryRunner` stores sessions in process memory (lost on restart).

## Configuration

### RAG (`app/core/config.py`)

| Variable | Default | Description |
|----------|---------|-------------|
| `chunk_size` | 400 | Approximate tokens per chunk |
| `chunk_overlap` | 60 | Overlap between chunks |
| `default_top_k` | 6 | Chunks retrieved per query |
| `temperature` | 0.1 | LLM temperature |
| `embedding_dimensions` | 1536 | Must match Supabase `VECTOR(1536)` |

Override via env: `OPENAI_EMBED_MODEL`, `OPENAI_CHAT_MODEL`, `AI_PROVIDER`, etc.

### Agent (`config/settings.py`)

| Variable | Description |
|----------|-------------|
| `ADK_APP_NAME` | ADK application identifier |
| `GEMINI_API_KEY` | Required for agent inference |
| `GEMINI_TEXT_MODEL_DEFAULT` | Model for orchestrator and specialists |
| `AGENT_THINKING_ENABLED` | Stream chain-of-thought as SSE events |

## Utility Scripts

| Script | Purpose |
|--------|---------|
| `test_setup.py` | Full RAG setup verification |
| `verify_rag.py` | Prove vector similarity search is working |
| `check_dimensions.py` | Inspect embedding dimensions in Supabase |
| `chatbot.py` | Rich terminal UI for RAG `/answer` |

## Docker

The Dockerfile deploys the **RAG FastAPI app** only:

```bash
docker build -t simple-agent .
docker run -p 8080:8080 --env-file .env simple-agent
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for Cloud Run instructions.

## Development

```bash
black app/ config/
isort app/ config/
flake8 app/ config/
```
