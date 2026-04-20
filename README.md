# GitCheck

GitCheck analyzes public GitHub repositories and scores how safe they look to adopt in production.

It combines live GitHub activity signals, feature extraction, and a weighted rule-based scoring system to explain repository health in a way that is easy to review quickly.

## Live App

- Production: `https://git-check-jade.vercel.app`
- Local app: `http://127.0.0.1:8000`
- Interactive docs: `http://127.0.0.1:8000/docs`

## What GitCheck Measures

- Recent commit activity
- Push recency and trend direction
- Contributor diversity and bus factor
- Issue closure and PR merge behavior
- Release cadence
- License presence
- Stars and forks as light adoption signals

## Core Endpoints

- `GET /` serves the frontend
- `GET /api/health` returns service health
- `GET /api/rate-limit` shows GitHub API budget
- `GET /api/analyze?repo_url=<owner/repo-or-url>` analyzes one repository
- `POST /api/analyze` accepts `{ "repo_url": "..." }`
- `POST /api/compare` compares up to 5 repositories

## Quick Start

### Prerequisites

- Python 3.10+
- A GitHub personal access token for better API limits

### Setup

```bash
git clone https://github.com/cmd-d4ksh/GitCheck.git
cd GitCheck
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add your GitHub token to `.env`:

```bash
GITHUB_TOKEN=your_token_here
```

### Run Locally

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Then open:

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/docs`

## Example Requests

Analyze a repository:

```bash
curl "http://127.0.0.1:8000/api/analyze?repo_url=https://github.com/fastapi/fastapi"
```

Compare repositories:

```bash
curl -X POST "http://127.0.0.1:8000/api/compare" \
  -H "Content-Type: application/json" \
  -d '{"repo_urls":["fastapi/fastapi","django/django","pallets/flask"]}'
```

## Response Highlights

GitCheck returns:

- repository metadata
- activity metrics
- normalized features
- overall score
- risk level and status
- category breakdowns
- highlights, risks, penalties, and recommendation text

## Deployment

GitCheck is deployed on Vercel using:

- `api/index.py` as the Python serverless entrypoint
- `vercel.json` rewrites to route all app traffic through FastAPI
- `web/static/` for the frontend assets

See [DEPLOYMENT.md](/Users/dakshshah/Documents/GitHub/GitCheck/DEPLOYMENT.md) and [docs/DEPLOYMENT.md](/Users/dakshshah/Documents/GitHub/GitCheck/docs/DEPLOYMENT.md) for the full flow.

## Project Layout

```text
app/            FastAPI app, GitHub client, scoring logic
api/            Vercel Python entrypoint
web/static/     Frontend HTML, CSS, and JS
ml/             Bundled training artifacts and legacy model file
docs/           Supporting documentation
vercel.json     Vercel routing configuration
```

## Notes

- The bundled ML model is kept for compatibility, but the primary scoring path is rule-based.
- Authenticated GitHub requests dramatically improve rate limits.
- Vercel is currently the production deployment target.
