# GitCheck — Viva Preparation Guide

---

## 1. ONE-LINE PITCH (say this if asked "what did you build?")

> **GitCheck is a trust and reliability scoring system that analyzes any public GitHub repository using live GitHub data and a machine learning model to help developers decide whether a project is safe to adopt as a dependency.**

---

## 2. THE PROBLEM IT SOLVES

Open-source developers blindly trust projects just because they have lots of stars. Stars are a vanity metric — a repo can have 10k stars but have had zero commits in 2 years, unresolved issues, no license, and no maintainers. GitCheck looks at the *real* signals that matter: **how active is it? how responsive are maintainers? how many people actually work on it?**

---

## 3. FULL SYSTEM ARCHITECTURE

```
User (Browser)
     │  enters GitHub repo URL
     ▼
Frontend (HTML/CSS/JS — served as static files by FastAPI)
     │  POST /analyze?repo_url=...
     ▼
FastAPI Backend (main.py)
     │
     ├──► github_api.py     → calls GitHub REST API, gets raw data
     │
     ├──► features.py       → normalizes raw data into 0-1 scores
     │
     ├──► ml_model.py       → RandomForest → Reliable / Unreliable + confidence
     │
     ├──► trust_score.py    → weighted formula → trust score (0-100) + risk level
     │
     └──► Response JSON returned to browser → rendered as dashboard
```

---

## 4. EVERY FILE EXPLAINED

### `app/main.py` — The entry point / API
- Uses **FastAPI** framework
- Mounts the `/web/static` folder so HTML/CSS/JS is served directly
- **Endpoints:**
  - `GET /` → returns the frontend HTML page
  - `GET /api/health` → health check (returns `{"status": "GitCheck API is running"}`)
  - `GET /rate-limit` → shows how many GitHub API calls are left before hitting the rate limit
  - `POST /analyze?repo_url=<url>` → the main endpoint; does everything and returns the full analysis
  - `GET /report/{owner}/{repo}` → serves the same HTML (for shareable URLs)
- `generate_recommendation()` — combines ML result and rule-based risk to give a human-readable verdict (✅ / 🟡 / ⚠️)

---

### `app/github_api.py` — GitHub Data Fetcher
- Reads `GITHUB_TOKEN` from `.env` file
- Sets auth headers: `Authorization: Bearer <token>`
- **Functions:**
  - `parse_repo_url()` — splits `https://github.com/owner/repo` → `(owner, repo)`
  - `get_repo_metadata()` — main function; calls all the below and assembles one big dict
  - `get_commit_activity()` — counts commits in **last 90 days** (paginated, up to 1000 commits)
  - `get_commit_activity_timeline()` — weekly commit totals for last 52 weeks (for the chart)
  - `get_issue_close_rate()` — `closed_issues / total_issues` (filters out PRs)
  - `get_contributor_count()` — total unique contributors (paginated)
  - `get_workflow_files()` — lists `.github/workflows/` to detect CodeQL / code scanning
  - `file_exists()` — checks if `SECURITY.md` or `dependabot.yml` exists
  - `check_rate_limit()` — queries `/rate_limit` endpoint
  - `handle_rate_limit()` — sleeps if fewer than 10 API calls remaining

- **Error handling:** 404 → repo not found, 403 → private repo, 409 → empty repo, timeout → 10 second cap

---

### `app/features.py` — Normalization
- Takes raw numbers and converts them to **0.0–1.0 scores**
- `normalize(value, max_value)` → `min(value/max_value, 1.0)` (capped at 1.0)

| Feature | Raw Source | Max Value Used |
|---|---|---|
| `commit_score` | commits_last_90_days | 100 |
| `contributor_score` | contributors | 30 |
| `issue_score` | issue_close_rate | already 0–1 |
| `star_score` | stars | 5000 |
| `fork_score` | forks | 1000 |

---

### `app/trust_score.py` — Rule-Based Scoring
- **Weighted formula:**

```
trust_score = (
  commit_score      × 0.25 +
  issue_score       × 0.20 +
  contributor_score × 0.20 +
  star_score        × 0.20 +
  fork_score        × 0.15
) × 100
```

- **Risk levels:**
  - ≥ 75 → **Low Risk**
  - 50–74 → **Medium Risk**
  - < 50 → **High Risk**

- **Maturity classification** (`classify_maturity`):
  - Compares avg commits in last 13 weeks vs prior 13 weeks
  - >20% increase → trend = "rising"
  - >20% decrease → trend = "falling"
  - "Mature": stars≥1000, contributors≥20, commits≥50, not falling
  - "Growing": rising trend + active
  - "Declining": falling trend
  - "Early": default / new project

- `explain_trust_score()` — returns the weights, thresholds, and each factor's contribution in points (for the Explanation panel in the frontend)

---

### `app/ml_model.py` — Machine Learning Prediction
- Loads `ml/model.pkl` (a pre-trained RandomForest) using **joblib**
- Uses **lazy loading** (model only loaded once on first request)
- Input features: `commit_score`, `contributor_score`, `issue_score` (3 features)
- Output:
  - `ml_label`: 1 = Reliable, 0 = Unreliable
  - `confidence`: probability score (0.0–1.0) from `predict_proba()`

---

### `ml/train_model.py` — Model Training Script
- Reads `ml/dataset.csv`
- Trains a `RandomForestClassifier(n_estimators=100, random_state=42)`
- Saves to `ml/model.pkl` with `joblib.dump()`
- Run manually once to generate the model file

---

### `ml/dataset.csv` — Training Data
```
commit_score, contributor_score, issue_score, label
0.9, 0.8, 0.9, 1  ← Reliable
0.7, 0.6, 0.8, 1  ← Reliable
0.8, 0.9, 0.7, 1  ← Reliable
0.2, 0.1, 0.3, 0  ← Unreliable
0.3, 0.2, 0.4, 0  ← Unreliable
0.1, 0.05, 0.2, 0 ← Unreliable
```
Label 1 = Reliable, Label 0 = Unreliable.

---

### `web/static/` — Frontend
- Pure HTML, CSS, JavaScript (no framework)
- Served by FastAPI using `StaticFiles` mount
- Features:
  - Animated trust score meter (ring gauge)
  - Dashboard panel: stars, forks, contributors, commits, issue close rate, security badges
  - Weekly commit timeline bar chart
  - Score explanation panel (shows weights + per-factor contributions)
  - Compare mode: analyze 2 repos side by side
  - Watchlist: save repos to localStorage for quick re-analysis
  - Shareable URL: `/report/{owner}/{repo}`

---

## 5. THE MANUAL STEPS YOU DID

### Setting up the GitHub Personal Access Token (PAT)
1. Went to GitHub → Settings → Developer Settings → Personal Access Tokens → Fine-grained tokens
2. Created a token with **read-only** permissions for public repositories
3. Copied the token into `.env` file as `GITHUB_TOKEN=ghp_...`
4. The code loads it via `python-dotenv`: `os.getenv("GITHUB_TOKEN")`
5. If token is missing, the app raises a `RuntimeError` immediately on startup (safety check)

### Why a GitHub token at all?
- Unauthenticated GitHub API: **60 requests/hour**
- Authenticated: **5,000 requests/hour**
- One repo analysis makes ~7–10 API calls, so auth is essential

### Training the ML model
- Ran `python ml/train_model.py` from the project root
- This reads `dataset.csv`, trains the RandomForest, and writes `model.pkl`
- This only needs to be done once; the app loads the pre-trained `.pkl` file

---

## 6. HOW TO RUN IT (say this confidently)

```bash
# 1. Clone and enter project
git clone https://github.com/cmd-d4ksh/GitCheck
cd GitCheck

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate       # Mac/Linux
venv\Scripts\activate          # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment
cp .env.example .env
# Then edit .env and paste your GitHub token

# 5. Run the server
uvicorn app.main:app --reload

# 6. Open browser
# http://localhost:8000
```

---

## 7. EXPECTED VIVA QUESTIONS & STRONG ANSWERS

---

### Q: What is GitCheck and why did you build it?
**A:** GitCheck is an AI-powered trust scoring system for GitHub repositories. The problem it solves is that developers often pick open-source libraries based on star count alone, which is misleading. A repo could be starred by thousands but abandoned for 3 years. GitCheck analyzes real signals — commit frequency, how many people contribute, how fast issues get resolved — and gives a structured trust score from 0 to 100, plus an ML-based reliability prediction.

---

### Q: Walk me through the architecture.
**A:** It's a 3-layer system. At the top is a **FastAPI backend** that exposes a REST API. When a user submits a GitHub URL, the backend calls **GitHub's REST API** to fetch raw repository data: stars, forks, contributors, commits over the last 90 days, the issue close rate, and security signals like whether they have a security policy, Dependabot, or CodeQL scanning. That raw data is passed to `features.py` which **normalizes everything to 0-to-1 scores**. Those normalized features then go into two parallel paths: a **rule-based weighted formula** in `trust_score.py` that produces a 0-100 score and risk level, and a **RandomForest ML model** in `ml_model.py` that gives a binary Reliable/Unreliable prediction with a confidence percentage. All of that is combined into a JSON response rendered on the frontend as a dashboard.

---

### Q: What ML model did you use and why?
**A:** I used a **RandomForestClassifier** from scikit-learn. I chose it because: (1) It works well with tabular/numerical data, (2) It's an ensemble method so it's more robust than a single decision tree, (3) It provides `predict_proba()` which gives a confidence score, not just a binary label. The model uses 100 decision trees with `random_state=42` for reproducibility.

---

### Q: What features does the ML model use?
**A:** The ML model uses 3 features: `commit_score` (normalized commit frequency over 90 days), `contributor_score` (normalized contributor count), and `issue_score` (issue close rate). These are the strongest health indicators. Star count and fork count are used in the rule-based scoring but not in the ML model, because those can be gamed or accumulated historically even if a project is now dead.

---

### Q: How is the trust score calculated?
**A:** It's a weighted linear combination of 5 normalized features multiplied by 100:
- Commit activity: 25% (most important — shows the project is alive)
- Issue close rate: 20% (shows maintainers are responsive)
- Contributor count: 20% (shows community health)
- Star count: 20% (shows community adoption)
- Fork count: 15% (shows active usage)

A score ≥75 is Low Risk, 50–74 is Medium Risk, below 50 is High Risk.

---

### Q: Why does the rule-based system exist alongside ML?
**A:** They complement each other. The ML model is a binary classifier — just Reliable or Unreliable — trained on patterns in the data. The rule-based system gives a continuous 0–100 score with human-readable weights that are interpretable and auditable. The final recommendation cross-references both: if the ML says Reliable AND the rule-based says Low Risk, we give a strong "Safe to use". If they disagree, we show a caution message. This **ensemble approach** makes the system more robust than relying on either alone.

---

### Q: What is feature normalization and why do you do it?
**A:** Raw numbers like "5000 stars" and "0.8 issue close rate" are on completely different scales and can't be directly compared or weighted. Normalization maps everything to the same 0.0–1.0 range using the formula `min(value / max_value, 1.0)`. For example, 50 commits out of a 100-commit max → 0.5. The `min()` cap ensures that even if a repo has 200 commits, the score doesn't exceed 1.0. This makes the weighted formula meaningful.

---

### Q: How do you handle GitHub API rate limits?
**A:** GitHub's REST API allows 5,000 authenticated requests per hour. Each analysis uses about 7–10 calls. I handle rate limits in two ways: (1) The `/rate-limit` endpoint lets users check remaining calls before analyzing; (2) If remaining calls drop below 10, the app sleeps until the rate limit resets (capped at 60 seconds). I also use pagination (up to 10 pages for commits, 5 for issues/contributors) with timeouts so no single request hangs.

---

### Q: What happens if someone passes a private or non-existent repo?
**A:** The app handles this gracefully. In `github_api.py`, a 404 response raises an exception with the message "Repository not found." A 403 raises "Access denied — the repository may be private." These exceptions are caught in `main.py` and returned as proper HTTP responses: 404 for not found, 403 for private, 504 for timeout. The frontend shows the error to the user cleanly instead of crashing.

---

### Q: What is uvicorn?
**A:** Uvicorn is an ASGI (Asynchronous Server Gateway Interface) server. FastAPI is an async framework and needs an ASGI server to run. Uvicorn is the standard choice — it's fast and supports async request handling. I run it with `--reload` in development so the server restarts automatically when I change code.

---

### Q: What is the `.env` file and why is it important?
**A:** The `.env` file stores secrets and configuration that shouldn't be hardcoded in source code — in this case, the GitHub API token. `python-dotenv` reads this file and loads its values as environment variables at startup. This is a security best practice: the `.env` file is listed in `.gitignore` so it's never committed to the repo, and anyone cloning the project uses `.env.example` as a template to create their own.

---

### Q: What is joblib and why use it over pickle?
**A:** `joblib` is used to serialize and deserialize the trained ML model to/from a `.pkl` file. It's preferred over Python's built-in `pickle` for ML models because it handles large NumPy arrays more efficiently — it can compress and memory-map them. Once the model is trained, I save it with `joblib.dump()` and load it at inference time with `joblib.load()`. This avoids re-training the model every time the server starts.

---

### Q: What does the maturity classification do?
**A:** It categorizes the repo into one of four lifecycle stages: **Mature** (established project, high stars/contributors, consistently active), **Growing** (rising commit trend in last 13 weeks vs previous 13 weeks), **Declining** (falling commit trend), or **Early** (new or low-activity project). It uses the weekly commit timeline from GitHub's `/stats/commit_activity` endpoint and calculates the percentage change in average weekly commits between the two halves of the last 26 weeks.

---

### Q: Why does the frontend use localStorage?
**A:** The Watchlist feature lets users save repos they want to monitor. Since GitCheck doesn't have a database or user accounts, localStorage is used as a lightweight client-side store. It's appropriate here because the watchlist is personal to the user's browser and doesn't need server-side persistence.

---

### Q: What are the limitations of your project?
**A (be honest and show you understand):**
1. **Small training dataset** — The ML model was trained on only 6 rows of synthetic data. In a production system, I'd scrape hundreds of real repos and label them properly.
2. **Public repos only** — The GitHub API doesn't expose data for private repos.
3. **No authentication/user accounts** — Currently stateless; watchlist is stored in browser localStorage.
4. **Static feature weights** — The trust score weights (25%, 20%, etc.) were chosen heuristically, not trained. A better approach would be to learn these weights from data.
5. **API rate limits** — Heavy usage could exhaust the 5,000 requests/hour limit.
6. **Synchronous API calls** — The GitHub fetching calls are sequential; making them concurrent with `asyncio` would speed things up.

---

### Q: What would you improve if you had more time?
**A:**
1. Train the ML model on a real labeled dataset of hundreds of repos
2. Add async/concurrent GitHub API calls to reduce analysis time
3. Add caching (Redis) so repeated analyses of the same repo don't hit GitHub again
4. Add a real database and user accounts for persistent watchlists
5. Deploy to a cloud provider (e.g., Railway, Render) with a public URL

---

### Q: What is FastAPI and why did you choose it over Flask?
**A:** FastAPI is a modern Python web framework designed for building APIs. I chose it over Flask because: (1) It has **automatic input validation** using Python type hints and Pydantic, (2) It generates **automatic interactive API documentation** at `/docs`, (3) It's built on **async/ASGI**, making it faster for I/O-heavy workloads like our GitHub API calls, (4) It has built-in error handling and HTTP exception support that made my code cleaner.

---

### Q: How does the frontend communicate with the backend?
**A:** The frontend (plain JavaScript) makes a `fetch()` call to `POST /analyze?repo_url=<encoded_url>`. The backend returns a JSON object with all the analysis data. The JS then reads the JSON and dynamically updates the DOM — filling in the score meter, badges, timeline chart, etc. The frontend is served as static files directly by FastAPI using `StaticFiles`, so there's no separate server needed.

---

## 8. QUICK REFERENCE — KEY NUMBERS TO MEMORIZE

| Thing | Value |
|---|---|
| Trust score range | 0 – 100 |
| Low risk threshold | ≥ 75 |
| Medium risk | 50 – 74 |
| High risk | < 50 |
| Commit score max (normalize) | 100 commits |
| Contributor score max | 30 contributors |
| Star score max | 5,000 stars |
| Fork score max | 1,000 forks |
| GitHub API rate limit (auth) | 5,000 req/hour |
| Request timeout | 10 seconds |
| ML model | RandomForestClassifier, 100 trees |
| ML features | commit_score, contributor_score, issue_score |
| Training samples | 6 rows (synthetic) |
| Maturity trend window | 13 weeks vs 13 weeks (26 total) |
| Maturity trend threshold | ±20% change |

---

## 9. SECURITY SIGNALS CHECKED (beyond just scoring)

| Signal | How Detected |
|---|---|
| Security Policy | `SECURITY.md` or `.github/SECURITY.md` exists |
| Dependabot | `.github/dependabot.yml` or `.github/dependabot.yaml` exists |
| Code Scanning | Workflow file contains "codeql" or "code scanning" |
| OSI License | `spdx_id` field matches a list of 14 known OSI-approved licenses |

---

## 10. TECH STACK SUMMARY

| Layer | Technology |
|---|---|
| Backend framework | FastAPI |
| ASGI server | Uvicorn |
| HTTP client | requests |
| ML library | scikit-learn (RandomForestClassifier) |
| Model serialization | joblib |
| Data manipulation | pandas |
| Environment config | python-dotenv |
| Frontend | Vanilla HTML/CSS/JavaScript |
| Data source | GitHub REST API v3 |

---

*Good luck tomorrow, Manan. You've got this.*
