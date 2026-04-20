# GitCheck Architecture

## High-Level Flow

```text
Frontend (web/static)
        |
        v
FastAPI app (app/main.py)
        |
        v
GitHub API client (app/github_api.py)
        |
        v
Feature extraction (app/features.py)
        |
        v
Weighted scoring engine (app/trust_score.py)
        |
        v
Structured report returned to UI/API clients
```

## Main Pieces

### `app/main.py`

- serves the frontend
- exposes `/api/health`, `/api/rate-limit`, `/api/analyze`, and `/api/compare`
- formats the final analysis report

### `app/github_api.py`

- parses repository input
- calls GitHub APIs
- handles rate limits, pagination, caching, and normalized errors

### `app/features.py`

- converts raw GitHub metrics into normalized feature scores
- models activity, maintenance, popularity, and bus-factor signals

### `app/trust_score.py`

- applies weighted scoring
- assigns status and risk level
- produces highlights, risks, penalties, and recommendation text

### `app/ml_model.py`

- loads the bundled legacy model if needed
- not part of the primary scoring path today

### `api/index.py`

- Vercel Python entrypoint
- imports the FastAPI app for production deployment

## Deployment Shape

```text
Browser
  -> Vercel
  -> vercel.json rewrite
  -> api/index.py
  -> FastAPI app
  -> GitHub API
```

Static frontend assets are served from `web/static/`.

## Scoring Model

GitCheck emphasizes:

- activity
- community resilience
- maintainer responsiveness
- project hygiene
- lightweight adoption signals

The final output includes both a total score and an explanation of why that score was assigned.
