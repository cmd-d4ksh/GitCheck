# Running the API

## Local

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open:

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/docs`

## Production

- `https://git-check-jade.vercel.app`
- `https://git-check-jade.vercel.app/api/health`

## Quick Checks

```bash
curl http://127.0.0.1:8000/api/health
curl "http://127.0.0.1:8000/api/analyze?repo_url=fastapi/fastapi"
curl https://git-check-jade.vercel.app/api/health
```

## Notes

- Root `/` serves the frontend, not a JSON status payload.
- API routes live under `/api/*`.
- Swagger docs are available locally at `/docs`.
