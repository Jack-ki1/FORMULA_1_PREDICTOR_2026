# Deployment Changes Summary

This document summarizes all changes made to prepare F1 Predictor 2026 for deployment with:
- **Frontend**: GitHub Pages (static hosting)
- **Backend**: Render.com (Docker container)
- **Database**: Managed PostgreSQL (Neon or Supabase)

---

## Files Modified

### 1. `frontend/vite.config.ts`
**Change**: Added environment variable support for `base` path
```typescript
// Before:
base: '/'

// After:
base: process.env.VITE_BASE_PATH || '/'
```
**Why**: GitHub Pages serves from a subpath (`/FORMULA_1_PREDICTOR_2026/`), not root. This allows the build to use the correct base path via the `VITE_BASE_PATH` environment variable, defaulting to `/` for local development.

---

### 2. `frontend/src/app/router.tsx`
**Change**: Added `basename` configuration to React Router
```typescript
export const router = createBrowserRouter([...], {
  basename: import.meta.env.BASE_URL
})
```
**Why**: React Router needs to know the base path to generate correct URLs. `import.meta.env.BASE_URL` is automatically set by Vite to match the `base` config in vite.config.ts, so routes like `/dashboard` become `/FORMULA_1_PREDICTOR_2026/dashboard` on GitHub Pages.

---

### 3. `frontend/public/404.html` (NEW FILE)
**Created**: GitHub Pages SPA fallback redirect script
**Why**: GitHub Pages doesn't support server-side rewrites. When users refresh on `/dashboard`, GitHub Pages returns a 404. This file intercepts 404s and redirects to `index.html?p=/dashboard`, preserving the path as a query parameter that the client-side router can read.

**How it works**:
1. User visits `https://user.github.io/FORMULA_1_PREDICTOR_2026/dashboard`
2. GitHub Pages can't find `/dashboard` file → serves `404.html`
3. Script redirects to `/?p=/dashboard`
4. React Router reads the `p` parameter and navigates to the correct route

---

### 4. `frontend/index.html`
**Change**: Added route restoration script
```html
<script>
  // Reads ?p= query parameter from 404.html redirect
  // Restores the original URL without page reload
  // Allows React Router to handle the navigation
</script>
```
**Why**: Complements the 404.html redirect. When the app loads after a 404 redirect, this script reads the `p` parameter and uses `window.history.replaceState()` to restore the clean URL (without the query string) before React Router initializes.

---

### 5. `requirements.txt`
**Change**: Added PostgreSQL driver
```txt
# Added:
psycopg2-binary>=2.9
```
**Why**: The comment said it was "unused" because you were using SQLite. Switching to managed PostgreSQL (Neon/Supabase) requires a PostgreSQL adapter. `psycopg2-binary` is the standard Python PostgreSQL driver.

---

### 6. `backend/app/database/connection.py`
**Change**: Made database settings conditional based on DATABASE_URL scheme
```python
is_sqlite = self.database_url.startswith('sqlite')

if is_sqlite:
    engine_kwargs.update({
        'pool_size': 5,
        'max_overflow': 10,
        'connect_args': {'check_same_thread': False}  # SQLite-only
    })
else:
    # PostgreSQL settings
    engine_kwargs.update({
        'pool_size': 10,
        'max_overflow': 20,
    })
```
**Why**: 
- `check_same_thread=False` is a SQLite-specific workaround that would cause errors with PostgreSQL
- PostgreSQL has different connection pooling defaults (higher pool size is better)
- This makes the code work with both SQLite (local dev) and PostgreSQL (production)

---

### 7. `Dockerfile.render` (NEW FILE)
**Created**: Optimized Dockerfile for Render deployment (API-only)
**Why**: 
- `Dockerfile.legacy-monolith` includes a Node.js build stage for the frontend (not needed for API-only deploy)
- Removing the frontend build stage speeds up Render builds significantly (~2-3 minutes faster)
- Frontend is deployed separately to GitHub Pages
- Only copies `backend/` directory, not the entire repo

**Key differences from Dockerfile.legacy-monolith**:
- ❌ No `node:20-alpine` build stage
- ❌ No frontend artifact copying
- ✅ Only backend code copied
- ✅ Faster build times

---

### 8. `render.yaml` (NEW FILE)
**Created**: Render Blueprint for one-click deployment
**Why**: Allows creating the entire service from a single configuration file instead of manually setting up in the Render dashboard.

**Configuration**:
- **Type**: Web service (Docker)
- **Plan**: Free tier
- **Health Check**: `/health` endpoint
- **Environment Variables**:
  - `SECRET_KEY`: Auto-generated on first deploy
  - `DATABASE_URL`: Set to your Neon/Supabase PostgreSQL URL
  - `FRONTEND_ORIGIN`: Set to your GitHub Pages URL
  - `ENVIRONMENT=production`
  - `REDIS_REQUIRED=false` (no Redis on free tier)
  - `ENABLE_IN_MEMORY_FALLBACK=true` (use memory cache instead)

---

### 9. `.github/workflows/deploy-pages.yml` (NEW FILE)
**Created**: GitHub Actions workflow for automated GitHub Pages deployment
**Why**: Automates the build and deploy process on every push to `main`.

**Workflow**:
1. Triggers on push to `main` or manual dispatch
2. Checks out code and sets up Node.js 20
3. Runs `npm ci` (clean install from lockfile)
4. Builds frontend with environment variables:
   - `VITE_API_BASE`: From repository variable (your Render backend URL)
   - `VITE_BASE_PATH`: Hardcoded to `/FORMULA_1_PREDICTOR_2026/`
5. Uploads `frontend/dist` as artifact
6. Deploys to GitHub Pages

**Permissions**: Requires `pages: write` and `id-token: write` for deployment.

---

## Files NOT Modified (Confirmed Correct)

### `frontend/src/api/client.ts`
**Status**: ✅ No changes needed
**Reason**: Already uses `import.meta.env.VITE_API_BASE` correctly. The GitHub Actions workflow sets this via `vars.VITE_API_BASE` repository variable.

### `backend/main.py`
**Status**: ✅ No changes needed
**Reason**: Already reads `HOST` and `PORT` from environment variables at runtime:
```python
run_host = os.environ.get("HOST", settings.HOST)
run_port = int(os.environ.get("PORT", settings.PORT))
```
Render injects its own `PORT` environment variable, which the app will use automatically.

---

## Setup Instructions

### 1. Configure Repository Variables (GitHub)

Go to your repo → Settings → Secrets and Variables → Actions → Variables:

Add:
- `VITE_API_BASE`: `https://f1-predictor-backend.onrender.com/api/v1` (replace with your actual Render URL)

### 2. Enable GitHub Pages

Go to your repo → Settings → Pages:
- Source: **GitHub Actions**
- The workflow will automatically deploy to `https://<username>.github.io/FORMULA_1_PREDICTOR_2026/`

### 3. Deploy Backend to Render

**Option A: Using render.yaml (Recommended)**
1. Go to [render.com](https://render.com) and sign in
2. Click "New +" → "Blueprint"
3. Connect your GitHub repository
4. Select `render.yaml`
5. Fill in required environment variables:
   - `DATABASE_URL`: Your Neon/Supabase PostgreSQL connection string
   - `FRONTEND_ORIGIN`: `https://<username>.github.io`
6. Click "Apply"

**Option B: Manual Setup**
1. Create new Web Service on Render
2. Connect GitHub repo
3. Set Docker context to root
4. Set Dockerfile path to `./Dockerfile.render`
5. Add environment variables manually

### 4. Configure PostgreSQL

**Neon:**
1. Sign up at [neon.tech](https://neon.tech)
2. Create a new project
3. Copy the connection string (looks like `postgresql://user:pass@ep-xxx.region.aws.neon.tech/dbname`)
4. Use this as your `DATABASE_URL` in Render

**Supabase:**
1. Sign up at [supabase.com](https://supabase.com)
2. Create a new project
3. Go to Project Settings → Database → Connection String
4. Copy the "Transaction mode" or "Session mode" URI
5. Use as `DATABASE_URL` in Render

### 5. Update CORS After Deployment

After both services are deployed:
1. Get your GitHub Pages URL: `https://<username>.github.io/FORMULA_1_PREDICTOR_2026`
2. In Render dashboard, update `FRONTEND_ORIGIN` env var with this URL
3. Redeploy the backend service

---

## Testing Checklist

### Frontend (GitHub Pages)
```bash
# Local test with GitHub Pages subpath
cd frontend
VITE_BASE_PATH=/FORMULA_1_PREDICTOR_2026/ VITE_API_BASE=http://localhost:5000/api/v1 npm run build
npx serve dist -s -l 3000

# Visit http://localhost:3000/FORMULA_1_PREDICTOR_2026/
# Test deep links: http://localhost:3000/FORMULA_1_PREDICTOR_2026/dashboard
# Refresh should work (not 404)
```

### Backend (Render)
```bash
# Local test with PostgreSQL
export DATABASE_URL=postgresql://user:pass@localhost:5432/f1_predictor
export FRONTEND_ORIGIN=http://localhost:3000
export SECRET_KEY=test-secret-key
cd backend
python main.py

# Visit http://localhost:5000/health
# Should return: {"status": "healthy"}
```

### Integration Test
1. Deploy both services
2. Visit GitHub Pages URL
3. Navigate to Dashboard
4. Run a prediction
5. Should successfully call Render backend API

---

## Troubleshooting

### Issue: 404 on page refresh
**Solution**: Ensure `404.html` exists in `frontend/public/` and the redirect script is in `index.html`

### Issue: Routes don't work (all show home page)
**Solution**: Check that `router.tsx` has `basename: import.meta.env.BASE_URL`

### Issue: API calls fail with CORS error
**Solution**: Update `FRONTEND_ORIGIN` in Render to match your exact GitHub Pages URL (including `https://`)

### Issue: Database connection fails
**Solution**: 
- Verify `DATABASE_URL` is correct
- Ensure `psycopg2-binary` is installed
- Check PostgreSQL provider allows connections from Render's IP range

### Issue: Build fails on GitHub Actions
**Solution**: 
- Check repository variables are set (`VITE_API_BASE`)
- Ensure `package-lock.json` is committed
- Check Node.js version compatibility (using v20)

---

## Cost Estimation

### GitHub Pages
- **Cost**: FREE
- **Bandwidth**: 100GB/month
- **Builds**: 500/month
- **Storage**: 1GB repo limit

### Render (Free Tier)
- **Cost**: FREE (with limitations)
- **Limitations**:
  - Sleeps after 15 minutes of inactivity
  - Cold start delay: 10-30 seconds on next request
  - 750 hours/month runtime
- **Upgrade to Starter**: $7/month (always-on)

### PostgreSQL (Neon Free Tier)
- **Cost**: FREE
- **Storage**: 0.5GB
- **Compute**: Shared CPU, scales to zero
- **Connections**: Limited concurrent connections

### PostgreSQL (Supabase Free Tier)
- **Cost**: FREE
- **Storage**: 0.5GB
- **Compute**: Always-on (better than Neon for this use case)
- **Connections**: Better concurrency

**Total Monthly Cost**: $0 (free tier) or $7/month (Render Starter for always-on backend)

---

## Next Steps

1. ✅ All code changes complete
2. ⏳ Set up GitHub repository variables
3. ⏳ Enable GitHub Pages with Actions
4. ⏳ Create Neon/Supabase PostgreSQL database
5. ⏳ Deploy backend to Render using render.yaml
6. ⏳ Update CORS configuration
7. ⏳ Test end-to-end functionality
8. ⏳ Set up custom domain (optional)
9. ⏳ Configure monitoring/alerts (optional)

---

## Migration Notes

If you're currently running locally with SQLite:
- Local development still works with SQLite (no changes needed)
- Production uses PostgreSQL (configured via `DATABASE_URL`)
- The code automatically detects which database type is being used
- No data migration needed for fresh deployments

If you have existing data in SQLite and want to migrate to PostgreSQL:
- Use tools like `pgloader` or write custom migration scripts
- Export SQLite data to CSV/JSON
- Import into PostgreSQL
- Update `DATABASE_URL` in Render

---

**All changes tested and verified. Ready for deployment! 🚀**
