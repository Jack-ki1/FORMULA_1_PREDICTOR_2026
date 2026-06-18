# 🚀 F1 Predictor 2026 - Live Deployment Guide

**Deploy your F1 prediction dashboard to the cloud and share it with the world!**

---

## 📋 Pre-Deployment Checklist

Before deploying, ensure your project is ready:

### ✅ **Required Files Present**
```bash
# Core application files
dashboard/app.py                    # Flask server
dashboard/templates/dashboard.html  # Web interface
dashboard/static/                   # CSS, JS, assets
engine/                             # Prediction engine (all 9 files)
data/                               # Data layer (all 10 files)
database/models.py                  # Database models
config/                             # Configuration
reports/html_report.py              # Report generation
main.py                             # CLI entry point
requirements.txt                    # Dependencies
```

### ✅ **Create `.env` File**
Create a `.env` file in the root directory:
```env
# Server Configuration
FLASK_PORT=5000
FLASK_DEBUG=false

# Security
ALLOWED_ORIGINS=https://your-domain.com,http://localhost:5000

# Optional: API Keys (if using external APIs)
# F1_API_KEY=your_api_key_here
```

### ✅ **Test Locally First**
```bash
# Install dependencies
py -m pip install -r requirements.txt

# Initialize database
py main.py migrate-db

# Run quality check
py main.py quality-check

# Test dashboard locally
py main.py dashboard --port 5000

# Visit http://127.0.0.1:5000 and verify everything works
```

---

## 🌐 Deployment Options

### **Option 1: Hugging Face Spaces** ⭐ RECOMMENDED (Free & Easy)

**Best for:** Quick deployment, free hosting, easy sharing

#### **Step 1: Create Hugging Face Account**
1. Go to [huggingface.co](https://huggingface.co/)
2. Sign up (free)
3. Click **"New Space"** → Choose **"Docker"** or **"Gradio"** (we'll use Docker)

#### **Step 2: Prepare Repository**

Create these files in your project root:

**`Dockerfile`:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p output cache .fastf1_cache

# Expose port
EXPOSE 7860

# Set environment variables
ENV FLASK_PORT=7860
ENV FLASK_DEBUG=false
ENV PYTHONUNBUFFERED=1

# Initialize database and start app
CMD ["sh", "-c", "python main.py migrate-db && python dashboard/app.py"]
```

**`.dockerignore`:**
```
.git
.gitignore
*.pyc
__pycache__
.env
f1_predictor.db
fastf1_cache.sqlite
output/
cache/
.fastf1_cache/
*.json
PROJECT_AUDIT.md
README_DEPLOYMENT.md
cleanup_and_test.bat
examples/
```

**Update `dashboard/app.py` for Hugging Face:**

Add this at the end of [app.py](file://c:\Users\PC\Music\FORMULA_1_PREDICTOR_2026\dashboard\app.py) (replace the existing `if __name__ == '__main__':` block):

```python
if __name__ == '__main__':
    import os
    logging.basicConfig(level=logging.INFO)
    
    # Hugging Face Spaces uses port 7860
    port = int(os.environ.get('FLASK_PORT', os.environ.get('PORT', 7860)))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    
    # For production, don't use debug mode
    if debug:
        print("⚠️  WARNING: Debug mode enabled in production!")
    
    print("=" * 60)
    print("🏎️  F1 Predictor Dashboard v3.0")
    print("=" * 60)
    print(f"📊 Dashboard: http://0.0.0.0:{port}")
    print(f"🔧 API: http://0.0.0.0:{port}/api/*")
    print(f"💾 Database: {'Initialized' if os.path.exists('f1_predictor.db') else 'Not initialized'}")
    print("=" * 60)
    
    # Bind to 0.0.0.0 for external access
    app.run(host='0.0.0.0', debug=debug, port=port)
```

#### **Step 3: Push to Hugging Face**

**Method A: Git Push (Recommended)**
```bash
# Initialize git repo (if not already)
git init
git add .
git commit -m "Initial commit"

# Add Hugging Face remote (replace YOUR_USERNAME and SPACE_NAME)
git remote add origin https://huggingface.co/spaces/YOUR_USERNAME/f1-predictor-2026

# Push to Hugging Face
git push -u origin main
```

**Method B: Web Upload**
1. Go to your Space on Hugging Face
2. Click **"Files"** → **"Add file"** → **"Upload files"**
3. Upload all project files (except `.git`, cache, database)
4. Wait for build (~5-10 minutes)

#### **Step 4: Configure Space Settings**

1. Go to **"Settings"** tab in your Space
2. Set:
   - **Hardware:** CPU Basic (free) or CPU Upgrade ($0.60/hr for faster predictions)
   - **Storage:** Enable persistent storage (for database)
   - **Secrets:** Add any API keys if needed
3. Click **"Rebuild"**

#### **Step 5: Access Your Live Dashboard**

Your dashboard will be available at:
```
https://YOUR_USERNAME-f1-predictor-2026.hf.space
```

**Pros:**
- ✅ Completely free (CPU Basic tier)
- ✅ Easy setup (just push to Git)
- ✅ Automatic HTTPS
- ✅ Built-in monitoring
- ✅ Shareable URL

**Cons:**
- ⚠️ Free tier sleeps after 48 hours of inactivity
- ⚠️ Limited to 2 vCPU, 16GB RAM
- ⚠️ Cold start takes ~2 minutes after sleep

---

### **Option 2: Railway** 💰 (Free Tier Available)

**Best for:** More control, always-on option, custom domains

#### **Step 1: Create Railway Account**
1. Go to [railway.app](https://railway.app/)
2. Sign up with GitHub
3. Click **"New Project"** → **"Deploy from GitHub repo"**

#### **Step 2: Configure Project**

Railway auto-detects Python projects, but you need a `Procfile`:

**Create `Procfile`:**
```procfile
web: python main.py migrate-db && python dashboard/app.py
```

**Create `railway.toml`:**
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python main.py migrate-db && python dashboard/app.py"
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
```

#### **Step 3: Set Environment Variables**

In Railway dashboard:
1. Go to **"Variables"** tab
2. Add:
   ```
   FLASK_PORT=$PORT
   FLASK_DEBUG=false
   ALLOWED_ORIGINS=https://your-project.railway.app
   ```

#### **Step 4: Deploy**

1. Connect your GitHub repository
2. Railway automatically builds and deploys
3. Get your URL: `https://your-project.railway.app`

**Pricing:**
- Free tier: $5/month credit (enough for small projects)
- Hobby plan: $5/month for always-on
- Pro plan: $20/month for more resources

**Pros:**
- ✅ Always-on (with paid plan)
- ✅ Custom domains
- ✅ Better performance than HF Spaces
- ✅ Easy environment variable management

**Cons:**
- ⚠️ Free tier has limited hours
- ⚠️ Requires credit card for paid plans

---

### **Option 3: Render** 💰 (Free Tier Available)

**Best for:** Simple deployment, automatic SSL, good documentation

#### **Step 1: Create Render Account**
1. Go to [render.com](https://render.com/)
2. Sign up with GitHub
3. Click **"New +"** → **"Web Service"**

#### **Step 2: Configure Service**

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
python main.py migrate-db && python dashboard/app.py
```

**Environment Variables:**
```
FLASK_PORT=10000
FLASK_DEBUG=false
```

#### **Step 3: Deploy**

1. Connect GitHub repo
2. Choose **"Free"** tier
3. Click **"Create Web Service"**
4. Wait ~5 minutes for deployment

**URL:** `https://your-app-name.onrender.com`

**Pricing:**
- Free tier: Sleeps after 15 minutes of inactivity
- Starter: $7/month (always-on)
- Standard: $25/month (more resources)

**Pros:**
- ✅ Free tier available
- ✅ Automatic HTTPS
- ✅ Good uptime
- ✅ Easy setup

**Cons:**
- ⚠️ Free tier sleeps quickly
- ⚠️ Slower cold starts than Railway

---

### **Option 4: PythonAnywhere** 💰 (Beginner-Friendly)

**Best for:** Beginners, simple Flask apps, educational use

#### **Step 1: Create Account**
1. Go to [pythonanywhere.com](https://www.pythonanywhere.com/)
2. Sign up for free account
3. Go to **"Web"** tab → **"Add a new web app"**

#### **Step 2: Configure Web App**

1. Choose **"Manual configuration"**
2. Select **Python 3.10**
3. Set paths:
   - **Source code:** `/home/yourusername/F1_PREDICTOR_2026`
   - **Working directory:** `/home/yourusername/F1_PREDICTOR_2026`
   - **WSGI configuration file:** Edit to point to Flask app

#### **Step 3: Upload Code**

**Via Git:**
```bash
# In PythonAnywhere bash console
git clone https://github.com/yourusername/F1_PREDICTOR_2026.git
cd F1_PREDICTOR_2026
pip install -r requirements.txt
python main.py migrate-db
```

**Via Web Interface:**
1. Use **"Files"** tab to upload zip
2. Extract in console

#### **Step 4: Configure WSGI**

Edit `/var/www/yourusername_pythonanywhere_com_wsgi.py`:

```python
import sys
path = '/home/yourusername/F1_PREDICTOR_2026'
if path not in sys.path:
    sys.path.insert(0, path)

from dashboard.app import app as application
```

#### **Step 5: Reload Web App**

Click **"Reload"** button in Web tab.

**URL:** `https://yourusername.pythonanywhere.com`

**Pricing:**
- Free tier: Limited bandwidth, shows ads
- Beginner: $5/month
- Intermediate: $10/month

**Pros:**
- ✅ Very beginner-friendly
- ✅ Good documentation
- ✅ Free tier available

**Cons:**
- ⚠️ Free tier has limitations
- ⚠️ Slower than other options
- ⚠️ Manual setup required

---

### **Option 5: Fly.io** 💰 (Global Deployment)

**Best for:** Global audience, low latency, scaling

#### **Step 1: Install Fly CLI**
```bash
# Windows (via Chocolatey)
choco install flyctl

# Or download from https://fly.io/docs/hands-on/install-flyctl/
```

#### **Step 2: Login and Launch**
```bash
fly auth login
fly launch
```

Follow the prompts:
- App name: `f1-predictor-2026`
- Region: Choose closest to your users
- Yes to PostgreSQL? **No** (we use SQLite)

#### **Step 3: Configure**

**Create `fly.toml`:**
```toml
app = "f1-predictor-2026"
primary_region = "ams"  # Amsterdam (change to your region)

[build]

[env]
  FLASK_PORT = "8080"
  FLASK_DEBUG = "false"

[[mounts]]
  source = "f1_data"
  destination = "/app/data"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0
  processes = ["app"]
```

#### **Step 4: Deploy**
```bash
fly deploy
fly open  # Opens browser
```

**Pricing:**
- Free allowance: $5/month credit
- Pay-as-you-go after that
- ~$2-5/month for small app

**Pros:**
- ✅ Global edge network
- ✅ Auto-scaling
- ✅ Fast performance
- ✅ Generous free tier

**Cons:**
- ⚠️ More complex setup
- ⚠️ CLI-based workflow

---

### **Option 6: Heroku** 💰 (Classic Choice)

**Note:** Heroku ended free tier in 2022, but still popular for paid deployments.

#### **Step 1: Install Heroku CLI**
```bash
# Download from https://devcenter.heroku.com/articles/heroku-cli
```

#### **Step 2: Create App**
```bash
heroku login
heroku create f1-predictor-2026
```

#### **Step 3: Configure**
```bash
heroku config:set FLASK_PORT=$PORT
heroku config:set FLASK_DEBUG=false
```

#### **Step 4: Deploy**
```bash
git push heroku main
heroku open
```

**Pricing:**
- Eco dynos: $5/month
- Basic dynos: $7/month

---

## 🔧 Platform-Specific Optimizations

### **For All Platforms: Reduce Startup Time**

**Problem:** Database migration on every startup is slow.

**Solution:** Modify [`dashboard/app.py`](file://c:\Users\PC\Music\FORMULA_1_PREDICTOR_2026\dashboard\app.py):

```python
# At the top of app.py, before routes
import os
from database.models import init_db

# Initialize database once at startup
try:
    if not os.path.exists('f1_predictor.db'):
        print("📦 Initializing database...")
        from database.models import migrate_from_static
        migrate_from_static()
        print("✅ Database initialized")
    else:
        print("✅ Database already exists")
except Exception as e:
    print(f"⚠️  Database initialization warning: {e}")
```

Remove `python main.py migrate-db &&` from startup commands.

---

### **For All Platforms: Disable Debug Mode**

**ALWAYS** set `FLASK_DEBUG=false` in production!

Debug mode:
- ❌ Slows down requests
- ❌ Security risk (shows stack traces)
- ❌ Uses more memory

---

### **For All Platforms: Add Health Check**

Your `/health` endpoint is perfect! Most platforms use it to monitor your app.

Test it:
```bash
curl https://your-app.com/health
# Should return: {"status": "healthy", "service": "F1 Predictor Dashboard v3.0"}
```

---

### **For Hugging Face: Optimize Build Time**

**Add to `Dockerfile`:**
```dockerfile
# Cache pip downloads
RUN pip cache purge

# Pre-download FastF1 data (optional, speeds up first prediction)
RUN python -c "import fastf1; fastf1.Cache.enable_cache('cache')" || true
```

---

### **For Railway/Render: Persistent Storage**

SQLite database needs persistent storage!

**Railway:**
```toml
# railway.toml
[volumes]
data = "/app/data"
```

**Render:**
- Use **"Disk"** feature ($0.25/GB/month)
- Mount at `/app/data`

**Hugging Face:**
- Enable **"Persistent Storage"** in Space settings
- Store database in `/data` directory

---

## 📊 Performance Comparison

| Platform | Free Tier | Cold Start | Monthly Cost | Best For |
|----------|-----------|------------|--------------|----------|
| **Hugging Face** | ✅ Yes | 2-3 min | $0 | Sharing demos |
| **Railway** | ⚠️ Limited | 30 sec | $5 | Production apps |
| **Render** | ⚠️ Limited | 1-2 min | $7 | Simple deployments |
| **PythonAnywhere** | ✅ Yes | 1 min | $5 | Beginners |
| **Fly.io** | ✅ $5 credit | 10 sec | $2-5 | Global users |
| **Heroku** | ❌ No | 30 sec | $7 | Legacy projects |

---

## 🛡️ Security Checklist for Production

### **1. Environment Variables**
Never commit secrets! Use platform's secret management:

```python
# In app.py
API_KEY = os.environ.get("F1_API_KEY")  # ✅ Good
API_KEY = "my_secret_key"               # ❌ Bad
```

### **2. CORS Configuration**
Update allowed origins:

```python
# In app.py
CORS(app, resources={
    r"/api/*": {
        "origins": os.getenv("ALLOWED_ORIGINS", "").split(","),
        "methods": ["GET", "POST"],
    }
})
```

Set `ALLOWED_ORIGINS=https://your-domain.com`

### **3. Rate Limiting**
Already implemented! Keep these limits:
```python
@limiter.limit("30 per minute")  # Per user
```

### **4. Database Backups**
Schedule regular backups:

**For Hugging Face:**
```python
# Add to app.py
import shutil
from datetime import datetime

@app.route('/api/admin/backup-db')
def backup_database():
    """Admin endpoint to backup database."""
    if os.path.exists('f1_predictor.db'):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f'backups/f1_predictor_{timestamp}.db'
        os.makedirs('backups', exist_ok=True)
        shutil.copy2('f1_predictor.db', backup_path)
        return jsonify({"status": "success", "backup": backup_path})
    return jsonify({"status": "error", "message": "Database not found"}), 404
```

---

## 🚀 Recommended Deployment Path

### **For Personal Use / Demo:**
```
Hugging Face Spaces (Free)
├── Easy setup
├── Free forever
└── Perfect for sharing with friends
```

### **For Serious Project:**
```
Railway ($5/month)
├── Always-on
├── Custom domain
├── Better performance
└── Professional appearance
```

### **For Maximum Reach:**
```
Fly.io ($2-5/month)
├── Global CDN
├── Auto-scaling
├── Lowest latency
└── Best value
```

---

## 📝 Step-by-Step: Hugging Face Deployment (Detailed)

Since HF Spaces is the easiest, here's a complete walkthrough:

### **Minute 0-5: Prepare Files**

1. Create these files in project root:
   - `Dockerfile` (see above)
   - `.dockerignore` (see above)
   - `.env` (with your settings)

2. Update `dashboard/app.py`:
   ```python
   # Change host binding at the end
   app.run(host='0.0.0.0', debug=False, port=7860)
   ```

3. Test locally:
   ```bash
   docker build -t f1-predictor .
   docker run -p 7860:7860 f1-predictor
   # Visit http://localhost:7860
   ```

### **Minute 5-10: Create Space**

1. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
2. Fill in:
   - **Space name:** `f1-predictor-2026`
   - **License:** MIT
   - **SDK:** Docker
   - **Visibility:** Public (or Private)
3. Click **"Create Space"**

### **Minute 10-15: Upload Code**

**Option A: Git (Recommended)**
```bash
cd c:\Users\PC\Music\FORMULA_1_PREDICTOR_2026

# Initialize git if needed
git init
git add .
git commit -m "Ready for deployment"

# Add remote (copy from HF Space page)
git remote add origin https://huggingface.co/spaces/YOUR_USERNAME/f1-predictor-2026

# Push
git push -u origin main
```

**Option B: Web Upload**
1. In your Space, click **"Files"**
2. Drag and drop all files (except `.git`, cache, database)
3. Wait for upload

### **Minute 15-25: Wait for Build**

1. Click **"App"** tab
2. Watch build logs
3. If errors occur:
   - Click **"Settings"** → **"Factory Rebuild"**
   - Check logs for specific errors

Common issues:
- **Missing dependencies:** Check `requirements.txt`
- **Port mismatch:** Ensure Dockerfile uses port 7860
- **Database error:** Check migration runs successfully

### **Minute 25-30: Test Live App**

1. Your URL: `https://YOUR_USERNAME-f1-predictor-2026.hf.space`
2. Test features:
   - ✅ Load dashboard
   - ✅ Run prediction
   - ✅ H2H comparison
   - ✅ Download report

### **Optional: Upgrade Hardware**

If predictions are slow:
1. Go to **"Settings"**
2. Change **"Hardware"** to:
   - **CPU Upgrade:** $0.60/hr (2x faster)
   - **GPU:** Not needed (we use NumPy, not GPU)

---

## 🐛 Troubleshooting Common Issues

### **"ModuleNotFoundError: No module named 'X'"**

**Cause:** Missing dependency

**Fix:**
```bash
# Add to requirements.txt
echo "missing-package" >> requirements.txt

# Rebuild
git add requirements.txt
git commit -m "Add missing dependency"
git push
```

### **"Database locked" Error**

**Cause:** Multiple processes accessing SQLite

**Fix:** Add to `dashboard/app.py`:
```python
from sqlalchemy import create_engine
engine = create_engine('sqlite:///f1_predictor.db', connect_args={'timeout': 30})
```

### **"Cold Start Too Slow"**

**Cause:** Database migration on startup

**Fix:** Pre-build database locally, commit it:
```bash
# Locally
py main.py migrate-db
git add f1_predictor.db
git commit -m "Add pre-built database"
git push
```

**Note:** Only do this for small databases (<100MB)

### **"Port Already in Use"**

**Cause:** Hardcoded port conflict

**Fix:** Use environment variable:
```python
port = int(os.environ.get('PORT', os.environ.get('FLASK_PORT', 7860)))
```

### **"Build Timeout"**

**Cause:** Too many dependencies or large files

**Fix:**
1. Add to `.dockerignore`:
   ```
   output/
   *.json
   *.html
   ```
2. Split requirements into `requirements-core.txt` and `requirements-dev.txt`

---

## 📈 Monitoring Your Deployment

### **Hugging Face:**
- Go to **"Monitoring"** tab
- View CPU/Memory usage
- Check request logs

### **Railway:**
- Dashboard shows real-time metrics
- Logs available in **"Deployments"** tab

### **Render:**
- **"Metrics"** tab shows performance
- **"Logs"** tab for debugging

---

## 💰 Cost Optimization Tips

### **1. Use Free Tiers Wisely**
- Hugging Face: Completely free
- Railway: $5 credit lasts months for low traffic
- Fly.io: $5 credit covers small app

### **2. Optimize Resource Usage**
```python
# Reduce simulation count for free tier
if os.getenv('FREE_TIER'):
    default_sims = 1000  # Instead of 10000
else:
    default_sims = 10000
```

### **3. Cache Aggressively**
```python
# Add caching to expensive operations
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_prediction(circuit_id, rain_prob):
    return predict(...)
```

### **4. Schedule Downtime**
For personal projects, shut down during night:
```bash
# Railway cron job
0 2 * * * curl -X POST https://api.railway.app/v1/projects/ID/stop
0 8 * * * curl -X POST https://api.railway.app/v1/projects/ID/start
```

---

## 🎯 Final Recommendation

**For your F1 Predictor 2026 project:**

### **Start with Hugging Face Spaces**
```
✅ Completely free
✅ Takes 30 minutes to deploy
✅ Perfect for testing
✅ Easy to share URL
✅ Can upgrade later
```

### **If You Need More Power:**
```
Migrate to Railway ($5/month)
├── Always-on
├── Faster predictions
├── Custom domain (f1predictor.yourname.com)
└── Professional appearance
```

### **Migration Path:**
```
HF Spaces (Free) 
  ↓ (getting serious?)
Railway ($5/month)
  ↓ (going global?)
Fly.io ($2-5/month)
```

All three use the same codebase—just change the deployment config!

---

## 📞 Need Help?

**Platform Documentation:**
- [Hugging Face Spaces Docs](https://huggingface.co/docs/hub/spaces)
- [Railway Docs](https://docs.railway.app/)
- [Render Docs](https://render.com/docs)
- [Fly.io Docs](https://fly.io/docs/)

**Common Questions:**
- Q: "Can I use a custom domain?"  
  A: Yes! Railway, Render, and Fly.io support custom domains. HF Spaces does not.

- Q: "Will my database persist?"  
  A: Only if you enable persistent storage (all platforms offer this).

- Q: "How many users can it handle?"  
  A: Free tiers: ~10-50 concurrent users. Paid tiers: 100+ users.

- Q: "Can I keep it private?"  
  A: Yes! All platforms offer private deployments.

---

**Ready to deploy? Start with Hugging Face Spaces—it's free and takes 30 minutes! 🚀**
