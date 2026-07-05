# Deployment Guide

Deploys the RAG FastAPI backend (`app/main.py` via `main:app`).

## Prerequisites

1. Supabase project with `sql/init_supabase.sql` applied
2. OpenAI API key (embeddings + chat, or embeddings only if using Anthropic for chat)
3. Container registry or Cloud Run access (for cloud deployment)

## Environment Variables

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

## Local Docker

```bash
docker build -t simple-agent .
docker run -p 8080:8080 --env-file .env simple-agent
```

Verify:

```bash
curl http://localhost:8080/healthz
curl -X POST http://localhost:8080/seed
curl -X POST http://localhost:8080/answer \
  -H "Content-Type: application/json" \
  -d '{"query": "Can I return shoes?"}'
```

## Google Cloud Run

### Cloud Console

1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Create or select a service
3. Deploy from source (uses the repo `Dockerfile`)
4. Under **Variables & Secrets**, add the environment variables listed above
5. Set **Container port** to `8080`
6. Deploy

### gcloud CLI

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

For production, prefer [Secret Manager](https://cloud.google.com/secret-manager) over plain `--set-env-vars`.

### Recommended settings

| Setting | Value | Reason |
|---------|-------|--------|
| Memory | ≥ 1 GiB | Embedding + LLM API calls |
| Timeout | 300 s | First `/seed` can be slow |
| CPU | 1 | Sufficient for moderate traffic |
| Port | 8080 | Matches Dockerfile |

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

## Security

- Do not commit `.env` — it is listed in `.gitignore`
- Use Secret Manager or Cloud Run secrets for `SUPABASE_SERVICE_ROLE_KEY` and `OPENAI_API_KEY`
- RLS policies in `sql/init_supabase.sql` include an anonymous read policy for development; tighten before production
- CORS in `app/main.py` allows `*` — restrict origins for production frontends
