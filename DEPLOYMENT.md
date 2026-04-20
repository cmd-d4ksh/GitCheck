# GitCheck Deployment

This project is deployed to Vercel and serves the same FastAPI application that runs locally.

## Current Production

- Production URL: `https://git-check-jade.vercel.app`
- Local URL: `http://127.0.0.1:8000`

## Deployment Shape

- `app/main.py` contains the FastAPI app
- `api/index.py` exposes that app to Vercel's Python runtime
- `web/static/` contains the frontend assets
- `vercel.json` rewrites all traffic to the Python entrypoint and serves `/static/*`

## Required Environment Variable

Set this in Vercel Project Settings:

```bash
GITHUB_TOKEN=your_github_personal_access_token
```

Use a fine-grained token with read access to public repository metadata.

## Local Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Vercel Deploy

### First-time setup

```bash
npx vercel login
npx vercel link
```

### Production deploy

```bash
npx vercel --prod
```

## Validation Checklist

- `GET /api/health` returns `{"status":"ok"}`
- frontend loads from `/`
- `GET /api/analyze` works with a public repository URL
- `GITHUB_TOKEN` is present in Production, Preview, and Development environments

## Notes

- Vercel may enable runtime dependency installation if the Python bundle is large.
- If deploys slow down, reduce unused repo assets and keep runtime dependencies minimal.
