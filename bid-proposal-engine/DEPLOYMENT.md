# Deployment Guide

## Quick Deploy (Recommended)

### Frontend → Vercel
1. Go to [vercel.com](https://vercel.com)
2. Import GitHub repo
3. Framework: Vue
4. Root directory: `bid-proposal-engine`
5. Add environment variable: `VITE_API_BASE` = your backend URL
6. Deploy

### Backend → Render
1. Go to [render.com](https://render.com)
2. New Web Service from GitHub
3. Root directory: `bid-proposal-engine/backend`
4. Build: `pip install -r requirements.txt`
5. Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Add env vars: `GEMINI_API_KEY`, `OPENAI_API_KEY`, `GROQ_API_KEY`
7. Deploy

### Update Frontend
Set `VITE_API_BASE` in Vercel to your Render URL.

---

## Alternative: Hugging Face Spaces (Backend)

### Why HF Spaces?
- 16 GB RAM (vs 512 MB on Render free)
- Docker support
- Free, no credit card
- Built-in secrets management

### Steps
1. Create HF account at huggingface.co
2. Create new Space (SDK: Docker, Public)
3. Push code with Dockerfile
4. Add secrets: GEMINI_API_KEY, OPENAI_API_KEY, GROQ_API_KEY
5. Wait for build (5-10 min)
6. URL: `https://YOUR_USERNAME-bid-proposal-engine.hf.space`

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `OPENAI_API_KEY` | Optional | OpenAI API key (fallback) |
| `GROQ_API_KEY` | Optional | Groq API key (fallback) |
| `ALLOWED_ORIGINS` | Yes | Comma-separated frontend URLs |
| `DATABASE_URL` | No | PostgreSQL URL (defaults to SQLite) |

---

## Verification

After deployment:
1. Visit frontend URL
2. Upload a test RFP
3. Run full pipeline
4. Check `/health` endpoint
5. Check `/llm-stats` endpoint
