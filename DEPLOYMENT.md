# Deployment Guide

This guide covers deploying the **RAG FastAPI backend** (`app/main.py` via `main:app`). The ADK agent layer is intended for local/CLI use and is not included in the current Docker image or `requirements.txt`.

## What Gets Deployed

| Component | Deployed? | Notes |
|-----------|-----------|-------|
| RAG API (`/seed`, `/answer`, `/healthz`, `/chat`) | Yes | Default Docker / Cloud Run target |
| Static chat UI (`static/chat.html`) | Yes | Served at `/chat` |
| ADK agent API (`app/api/`) | No | Routes exist but are not mounted on `app/main.py` |
| Agent CLI (`app/chat_cli.py`) | No | Run locally with `google-adk` installed |

## Prerequisites

1. Supabase project with `sql/init_supabase.sql` applied
2. OpenAI API key (embeddings + chat, or embeddings only if using Anthropic for chat)
3. Container registry or Cloud Run access (for cloud deployment)

## Environment Variables

Set these for the RAG service:

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

OPENAI_API_KEY=sk-your_openai_key_here
OPENAI_EMBED_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o
AI_PROVIDER=openai

ENVIRONMENT=production
LOG_LEVEL=INFO
```

Optional Anthropic chat:

```env
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_anthropic_key_here
ANTHROPIC_CHAT_MODEL=claude-3-5-sonnet-20240620
```

Agent variables (`GEMINI_API_KEY`, `ADK_APP_NAME`, etc.) are not required for RAG deployment.

## Local Docker

```bash
docker build -t simple-agent .
docker run -p 8080:8080 --env-file .env simple-agent
```

The container listens on port 8080 (`PORT` env var is respected by the Dockerfile CMD).

Verify:

```bash
curl http://localhost:8080/healthz
curl -X POST http://localhost:8080/seed
curl -X POST http://localhost:8080/answer \
  -H "Content-Type: application/json" \
  -d '{"query": "Can I return shoes?"}'
```

## Google Cloud Run

### Option A: Cloud Console

1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Create or select a service
3. Deploy from source (uses the repo `Dockerfile`)
4. Under **Variables & Secrets**, add the RAG environment variables listed above
5. Set **Container port** to `8080`
6. Deploy

### Option B: gcloud CLI

```bash
gcloud run deploy simple-agent \
  --source . \
  --platform managed \
  --region us-east1 \
  --allow-unauthenticated \
  --port 8080 \
  --timeout 300 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --set-env-vars="SUPABASE_URL=your_url,SUPABASE_ANON_KEY=your_anon_key,SUPABASE_SERVICE_ROLE_KEY=your_service_key,OPENAI_API_KEY=your_openai_key,OPENAI_EMBED_MODEL=text-embedding-3-small,OPENAI_CHAT_MODEL=gpt-4o,AI_PROVIDER=openai,ENVIRONMENT=production,LOG_LEVEL=INFO"
```

Replace placeholder values before running. For production, prefer [Secret Manager](https://cloud.google.com/secret-manager) references instead of plain `--set-env-vars`.

### Recommended Cloud Run settings

| Setting | Value | Reason |
|---------|-------|--------|
| Memory | ≥ 1 GiB | Embedding + LLM API calls |
| Timeout | 300 s | First `/seed` can be slow |
| CPU | 1 | Sufficient for moderate traffic |
| Concurrency | 80 (default) | FastAPI handles concurrent requests |
| Port | 8080 | Matches Dockerfile `EXPOSE` and `PORT` default |

## Post-Deploy Checklist

```bash
SERVICE_URL=https://your-service-url

curl "$SERVICE_URL/healthz"
curl "$SERVICE_URL/chat"
curl -X POST "$SERVICE_URL/seed"
curl -X POST "$SERVICE_URL/answer" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is your return policy?"}'
```

Expected health response:

```json
{"status": "ok", "database_connected": true}
```

If `database_connected` is `false`, verify Supabase credentials and that `sql/init_supabase.sql` was run.

## Dockerfile Summary

Current image (`Dockerfile`):

- Base: `python:3.11-slim`
- Installs `requirements.txt` (RAG dependencies only)
- Runs as non-root user `app`
- CMD: `uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --timeout-keep-alive 0`

## Security

- Do not commit `.env` — it is listed in `.gitignore`
- Use Secret Manager or Cloud Run secrets for `SUPABASE_SERVICE_ROLE_KEY` and `OPENAI_API_KEY`
- RLS policies in `sql/init_supabase.sql` include an anonymous read policy for development; tighten before production
- CORS in `app/main.py` allows `*` — restrict origins for production frontends

## Deploying Agents (Future)

To run agents in production you would need to:

1. Add `google-adk` and `google-genai` to `requirements.txt`
2. Mount `app.api.router.api_router` on the FastAPI app (or deploy a second service)
3. Set agent env vars (`GEMINI_API_KEY`, `ADK_APP_NAME`, etc.)
4. Replace `InMemoryRunner` with a persistent ADK session backend if cross-restart memory is required

Until then, use `python -m app.chat_cli` locally for agent testing.
