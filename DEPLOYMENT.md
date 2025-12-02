# HiRA Deployment Guide - Railway

This guide will help you deploy HiRA (Human Rights Assistant) to Railway.

## Prerequisites

1. Railway account (sign up at https://railway.app)
2. GitHub account (to connect your repository)
3. API Keys:
   - OpenAI API Key (for embeddings)
   - Anthropic API Key (for Claude)

## Deployment Steps

### 1. Push to GitHub

First, push your code to GitHub if you haven't already:

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/hrba-agent.git
git push -u origin main
```

### 2. Create Railway Project

1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select your `hrba-agent` repository
4. Railway will detect your project automatically

### 3. Deploy Backend

1. Railway will create a service for your backend
2. Set the **Root Directory** to `backend`
3. Railway will auto-detect the Dockerfile

### 4. Add Environment Variables

In Railway, go to your backend service → Variables tab and add:

#### Required Variables:

```
# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Environment
ENVIRONMENT=production
DEBUG=False

# Security (generate a random secret key)
SECRET_KEY=your-random-secret-key-here

# LLM Settings
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# Embedding Settings
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIMENSION=3072

# RAG Settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RETRIEVAL=8
SIMILARITY_THRESHOLD=0.6

# Vector Database
CHROMA_PERSIST_DIRECTORY=/app/data/vectorstore
CHROMA_COLLECTION_NAME=hira_documents

# CORS (will be updated after frontend deployment)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

#### Optional (if using OAuth/Zoom):
```
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
RECALL_API_KEY=your-recall-api-key
```

### 5. Add Persistent Volume

1. In Railway backend service → Settings → Volumes
2. Click "New Volume"
3. Mount Path: `/app/data`
4. Size: 1GB (should be enough for MVP)

This ensures your vector database persists across deployments.

### 6. Deploy Frontend

1. In Railway project, click "New Service"
2. Select "Deploy from GitHub repo" (same repository)
3. Set **Root Directory** to `frontend`
4. Set build command: `npm run build`
5. Set start command: `npm run preview`

### 7. Update CORS Settings

After both services are deployed:

1. Copy your Railway backend URL (e.g., `https://your-backend.up.railway.app`)
2. Copy your Railway frontend URL (e.g., `https://your-frontend.up.railway.app`)
3. Update backend environment variable:
   ```
   CORS_ORIGINS=https://your-frontend.up.railway.app
   ```

### 8. Update Frontend API URL

1. In Railway frontend service → Variables
2. Add:
   ```
   VITE_API_URL=https://your-backend.up.railway.app
   ```

### 9. Load Documents

After deployment, you need to load your core documents:

**Option 1: SSH into Railway**
```bash
railway shell
python reload_docs.py
```

**Option 2: Create a one-time job**
Add this as a temporary endpoint in your backend to trigger document loading via API.

## Verification

1. Visit your frontend URL
2. Try asking: "What is the EU AI Act?"
3. Should receive response with context from documents

## Troubleshooting

### Backend won't start
- Check Railway logs for errors
- Verify all environment variables are set
- Ensure volume is mounted correctly

### Frontend can't connect to backend
- Verify CORS_ORIGINS includes your frontend URL
- Check VITE_API_URL points to correct backend

### No RAG responses
- Ensure documents are loaded (run reload_docs.py)
- Check OPENAI_API_KEY is valid
- Verify volume is persistent

## Cost Estimate

**Railway Free Tier:**
- $5 credit per month
- Should be enough for MVP testing

**API Costs:**
- OpenAI embeddings: ~$0.13 per 1M tokens
- Anthropic Claude: ~$3 per 1M input tokens

For light usage (100 queries/day), expect ~$10-20/month in API costs.

## Production Checklist

- [ ] Set strong SECRET_KEY
- [ ] Set DEBUG=False
- [ ] Update CORS to only include production domain
- [ ] Enable SSL (Railway does this automatically)
- [ ] Set up monitoring/logging
- [ ] Configure rate limiting
- [ ] Add authentication (if needed)
- [ ] Backup vector database regularly
