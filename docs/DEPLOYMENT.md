# Deployment Guide

## Overview

GitCheck runs as a FastAPI app locally and is deployed to Vercel in production.

- Local: `http://127.0.0.1:8000`
- Production: `https://git-check-jade.vercel.app`

## Files That Matter

- `app/main.py`: FastAPI application
- `api/index.py`: Vercel Python entrypoint
- `vercel.json`: rewrites and deployment routing
- `web/static/`: frontend files

## Vercel Requirements

### Environment variable

```bash
GITHUB_TOKEN=your_token_here
```

Add it to:

- Production
- Preview
- Development

### CLI flow

```bash
npx vercel whoami
npx vercel link
npx vercel env ls
npx vercel --prod
```

## Recommended Deploy Workflow

1. Verify the app locally with `uvicorn`.
2. Confirm `.env` works locally.
3. Ensure the Vercel project is linked.
4. Confirm `GITHUB_TOKEN` is set in Vercel.
5. Run `npx vercel --prod`.
6. Test `/` and `/api/health` on the production URL.

## Troubleshooting

### Build fails on Python function discovery

Make sure the Vercel entrypoint exists at:

```text
api/index.py
```

### Frontend loads but API fails

Check:

- Vercel env vars
- GitHub token validity
- production function logs with `npx vercel logs <deployment-url>`

### GitHub rate limit issues

- verify the token is valid
- verify it is assigned to the correct Vercel environments
- redeploy after changing env vars
