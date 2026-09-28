# Vercel Deployment Guide

## Quick Deploy (5 Minutes)

### Prerequisites

1. **PostgreSQL Database** (required - SQLite not compatible)
   - Sign up at [Supabase](https://supabase.com) or [Neon](https://neon.tech)
   - Create a new project
   - Copy the connection string

2. **Generate Secrets**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **Push to Git**
   ```bash
   git add .
   git commit -m "Deploy to Vercel"
   git push origin main
   ```

### Deploy

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click "Add New Project" → Import your Git repository
3. Vercel auto-detects configuration from `vercel.json`
4. Click "Deploy"

### Configure Environment Variables

In Vercel Dashboard → Settings → Environment Variables, add:

```bash
DATABASE_URL=postgresql://user:pass@host:5432/f1_predictor
SECRET_KEY=<generated-secret-from-step-2>
FRONTEND_ORIGIN=https://your-app.vercel.app
ENVIRONMENT=production
DEBUG=false
REDIS_REQUIRED=false
ENABLE_IN_MEMORY_FALLBACK=true
LIVE_UPDATE_INTERVAL=300
```

**Important:** Update `FRONTEND_ORIGIN` after deployment with your actual Vercel URL.

### Test

- Frontend: `https://your-app.vercel.app`
- API Docs: `https://your-app.vercel.app/docs`
- Health: `https://your-app.vercel.app/health`

---

## Configuration Files

### vercel.json
Monorepo configuration that routes:
- `/api/*`, `/docs`, `/health`, etc. → Backend (FastAPI)
- Everything else → Frontend (React/Vite)

### backend/vercel.py
Serverless entry point for FastAPI (no background processes).

### .env.example
Template for all required environment variables.

---

## Important Notes

⚠️ **Limitations:**
- Function timeout: 10s (Hobby free tier) / 60s (Pro $20/month)
- No Redis (using in-memory cache)
- No SQLite (must use PostgreSQL)
- Cold starts: 5-30s on first request after inactivity

✅ **What Works:**
- All prediction features
- PDF/Excel exports
- PostgreSQL database
- Authentication
- Rate limiting

💰 **Cost:** $0/month (Hobby) or $20/month (Pro) + Free PostgreSQL

---

## Troubleshooting

**Build fails:** Ensure `requirements.txt` exists in root directory

**Database error:** Verify `DATABASE_URL` is correct and database allows external connections

**CORS error:** Update `FRONTEND_ORIGIN` to match your exact Vercel URL

**Timeout:** Reduce `MONTE_CARLO_SIMULATIONS=500` or upgrade to Pro plan

For more details, see the full README.md deployment section.
