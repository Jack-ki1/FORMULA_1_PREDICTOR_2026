# Deploying to GitHub Pages

A step-by-step guide to hosting the F1 Prediction System as a live website
at `https://YOUR_USERNAME.github.io/f1-prediction-system/`.

---

## Architecture Overview

```
GitHub Repository
│
├── data/ + engine/        ← Python prediction system
│
└── .github/workflows/
    └── deploy.yml          ← Runs every Thursday + on data changes
            │
            ▼
    Python runs prediction engine
            │
            ▼
    Generates web/ (static HTML + JSON)
            │
            ▼
    GitHub Pages serves web/
            │
            ▼
    https://YOUR_USERNAME.github.io/f1-prediction-system/
```

The workflow generates a **fully static site** — no server required.
Chart.js is loaded from CDN. Predictions are pre-computed JSON files.

---

## Step 1 — Create the GitHub Repository

```bash
# If you haven't already initialised git
cd f1-prediction-system
git init
git add .
git commit -m "Initial commit — F1 Prediction System"

# Create repo on GitHub (use GitHub CLI or website)
gh repo create f1-prediction-system --public
# or: create manually at https://github.com/new

# Push
git remote add origin https://github.com/YOUR_USERNAME/f1-prediction-system.git
git branch -M main
git push -u origin main
```

---

## Step 2 — Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** → **Pages** (left sidebar)
3. Under **Source**, select **GitHub Actions**
4. Save

That's it. The `deploy.yml` workflow will now deploy to Pages automatically.

---

## Step 3 — Trigger the First Deployment

Option A — automatic:
- Push any change to `main` that touches a file in `data/` or `engine/`

Option B — manual trigger:
1. Go to **Actions** tab in your repository
2. Click **"Deploy F1 Predictions to GitHub Pages"**
3. Click **"Run workflow"**
4. Fill in optional parameters and click **"Run workflow"**

The deployment takes about 2–3 minutes. Your site will be live at:
```
https://YOUR_USERNAME.github.io/f1-prediction-system/
```

---

## Step 4 — Verify the Deployment

After the workflow completes:
- ✅ Green checkmark in Actions tab
- Visit your GitHub Pages URL
- You should see the prediction dashboard with:
  - Next race card with predicted podium
  - Driver standings table
  - Win probability chart
  - Full calendar

---

## Workflow Triggers

The deploy workflow runs automatically when:

| Trigger | When |
|---------|------|
| **Scheduled** | Every Thursday at 09:00 UTC (before most race weekends) |
| **Push to main** | Whenever `data/`, `engine/`, or `config/` files change |
| **Manual dispatch** | Anytime from Actions tab with custom parameters |

---

## Manual Deployment with Custom Parameters

From the Actions tab → "Deploy F1 Predictions to GitHub Pages" → "Run workflow":

| Parameter | Description | Example |
|-----------|-------------|---------|
| `rain_probability` | Override rain chance | `0.65` for wet Monaco |
| `simulations` | Monte Carlo runs | `10000` for high precision |

This is useful for race-weekend previews with updated weather forecasts.

---

## Customising the Published Site

### Change the site title / branding

Edit the `<title>` and `<header>` in `scripts/generate_static_site.py`:
```python
# In write_index_html():
html = f"""...
<title>F1 2026 — My Prediction Model</title>
...
<h1>🏁 My F1 2026 Picks</h1>
...
"""
```

### Add a custom domain

1. Buy a domain (e.g. `f1picks.com`)
2. In repo Settings → Pages → Custom domain: enter your domain
3. Add these DNS records at your registrar:
   ```
   CNAME  www   YOUR_USERNAME.github.io
   A      @     185.199.108.153
   A      @     185.199.109.153
   A      @     185.199.110.153
   A      @     185.199.111.153
   ```
4. Check "Enforce HTTPS" in Pages settings
5. Create `web/CNAME` file containing your domain:
   ```
   www.f1picks.com
   ```

---

## File Structure After Deployment

```
web/                            ← Published as GitHub Pages root
├── index.html                  ← Main dashboard
├── predictions/
│   ├── canada.json
│   ├── monaco.json
│   └── ... (one per circuit)
└── assets/
    └── data.json               ← Full aggregate data for custom integrations
```

JSON files are publicly accessible:
```
https://YOUR_USERNAME.github.io/f1-prediction-system/assets/data.json
https://YOUR_USERNAME.github.io/f1-prediction-system/predictions/canada.json
```

This makes the system usable as a free public API.

---

## On-Demand Race Reports (PDF/HTML download)

The `predict.yml` workflow lets anyone with repo access generate a report:

1. Go to **Actions** → **"On-Demand Race Prediction"**
2. Click **"Run workflow"**
3. Enter circuit ID, rain probability, simulation count
4. After completion, download the HTML report from **Artifacts**

The artifact includes:
- `prediction_CIRCUIT.json` — raw prediction data
- `CIRCUIT_report.html` — styled standalone report

---

## Keeping the Deployed Site Fresh

The site auto-updates on Thursdays. For race weekends:

1. After qualifying (Saturday):
   ```bash
   # Update any grid position overrides if needed
   # Push changes to main → auto-deploys
   git add data/season_2026.py
   git commit -m "Update: Canada qualifying grid"
   git push
   ```

2. After the race (Sunday):
   ```bash
   python scripts/post_race_update.py --round 5 --circuit canada \
     --results "antonelli:1,russell:2,norris:3,..."
   git add data/season_2026.py
   git commit -m "Results: Canadian GP R5"
   git push
   # → Auto-deploys updated site within ~3 minutes
   ```

---

## Secrets & Environment Variables

For optional features (weather API, live data sync), add secrets in:
**Settings → Secrets and variables → Actions → New repository secret**

| Secret name | Description |
|-------------|-------------|
| `OPENWEATHER_API_KEY` | OpenWeatherMap API key for weather forecasts |
| `ERGAST_API_BASE` | Override default Ergast endpoint |

Reference in workflows:
```yaml
env:
  OPENWEATHER_API_KEY: ${{ secrets.OPENWEATHER_API_KEY }}
```

---

## Monitoring & Alerts

Set up email notifications for failed deployments:
1. **Settings → Notifications → Actions**
2. Enable "Send notifications for failed workflows"

You'll get an email if the Thursday deploy fails (e.g. due to a Python error
after a data update).
