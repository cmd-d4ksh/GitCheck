# API Reference

## Base URLs

- Local: `http://127.0.0.1:8000`
- Production: `https://git-check-jade.vercel.app`

## Endpoints

### `GET /`

Returns the frontend HTML application.

### `GET /api/health`

Basic health check.

Example response:

```json
{
  "status": "ok"
}
```

### `GET /api/rate-limit`

Returns the current GitHub API budget.

Example response:

```json
{
  "remaining": 4921,
  "reset_at": 1770000000,
  "status": "healthy"
}
```

### `GET /api/analyze`

Query parameter:

- `repo_url`: full GitHub URL or `owner/repo`

Example:

```bash
curl "http://127.0.0.1:8000/api/analyze?repo_url=fastapi/fastapi"
```

### `POST /api/analyze`

Request body:

```json
{
  "repo_url": "https://github.com/fastapi/fastapi"
}
```

### `POST /api/compare`

Request body:

```json
{
  "repo_urls": [
    "fastapi/fastapi",
    "django/django",
    "pallets/flask"
  ]
}
```

Accepts between 1 and 5 repository values.

## Analyze Response Shape

Key fields returned by `/api/analyze`:

```json
{
  "repository": "fastapi/fastapi",
  "url": "https://github.com/fastapi/fastapi",
  "description": "FastAPI framework, high performance, easy to learn, fast to code, ready for production",
  "language": "Python",
  "topics": [],
  "license": "MIT License",
  "default_branch": "master",
  "latest_release": null,
  "metadata": {
    "stars": 0,
    "forks": 0,
    "watchers": 0,
    "open_issues": 0,
    "contributors": 0,
    "archived": false,
    "disabled": false,
    "created_at": null,
    "updated_at": null,
    "pushed_at": null,
    "days_since_push": 0,
    "age_days": 0
  },
  "activity": {
    "commits_last_90_days": 0,
    "weekly_commits": [],
    "issue_close_rate": 0.0,
    "pr_merge_rate": 0.0,
    "issues": {},
    "pull_requests": {},
    "release_count": 0
  },
  "top_contributors": [],
  "features": {},
  "score": 0,
  "risk_level": "Low",
  "status": "Active",
  "breakdown": [],
  "penalties": [],
  "categories": [],
  "highlights": [],
  "risks": [],
  "recommendation": "Safe to adopt",
  "warnings": []
}
```

## Error Responses

GitCheck returns normalized JSON errors in this shape:

```json
{
  "detail": "Repository not found. Check the URL and ensure the repo is public."
}
```

Common status codes:

- `400` invalid repo input
- `401` invalid GitHub token
- `403` forbidden or private repo access denied
- `404` repository not found
- `409` empty/conflicted repository
- `429` GitHub rate limit exceeded
- `502` upstream/network issue
- `504` GitHub timeout
