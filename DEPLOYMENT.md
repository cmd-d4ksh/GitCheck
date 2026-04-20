# GitCheck Deployment Guide

## Prerequisites

- GitHub account with a fine-grained personal access token (read-only on repos)
- Vercel account
- Local: `pip install vercel`, Git, Python 3.9+

---

## Deploy to Vercel

### Step 1: Create a GitHub Personal Access Token

1. Go to [github.com/settings/tokens](https://github.com/settings/tokens)
2. Click **Generate new token (classic)** or **Fine-grained personal access token**
   - **Fine-grained (recommended)**: 
     - Repository access: Public Repositories (read-only)
     - Permissions: Metadata, Pull requests, Issues, Commit statuses
   - **Classic**: Select scopes `public_repo` and `read:user`
3. Save the token safely — you'll need it in Step 5.

### Step 2: Push to GitHub

```bash
git push origin claude/lucid-edison-b66624
# or merge to main if ready for production
git push origin main
```

### Step 3: Install Vercel CLI

```bash
npm install -g vercel
# or
pip install vercel
```

### Step 4: Link Your Repo to Vercel

```bash
vercel
```

During setup:
- **Set scope**: Select your personal account or organization
- **Link to repo**: `GitCheck` (or create new)
- **Build & develop settings**: Let it auto-detect, then modify (see next step)

### Step 5: Configure Environment Variables

In the Vercel dashboard ([vercel.com/dashboard](https://vercel.com/dashboard)):

1. Find your GitCheck project
2. Go to **Settings** → **Environment Variables**
3. Add:
   - **Name**: `GITHUB_TOKEN`
   - **Value**: Paste your token from Step 1
   - **Environments**: Production, Preview, Development (select all)
4. Click **Save**

### Step 6: Deploy

**Option A: Automatic (Recommended)**
```bash
# Push to GitHub — Vercel auto-deploys on push
git push origin main
```

**Option B: Manual**
```bash
vercel --prod
```

---

## Production Checklist

- [ ] GitHub token created and added to Vercel env vars
- [ ] Repo pushed to GitHub (main or feature branch)
- [ ] Vercel project created and linked
- [ ] `vercel.json` configured (included in repo)
- [ ] Environment variable `GITHUB_TOKEN` set
- [ ] Build succeeds: `vercel build`
- [ ] Preview deployment works
- [ ] Hit prod deploy: `vercel --prod`
- [ ] Test live at `your-project.vercel.app`

---

## Troubleshooting

### "GITHUB_TOKEN not found"
- Check Vercel **Settings** → **Environment Variables**
- Ensure `GITHUB_TOKEN` is set for Production environment
- Redeploy after adding

### "GitHub rate limit exceeded"
- Token is invalid or expired
- Replace token in Vercel environment variables
- Check if token has `public_repo` scope

### Build fails: "No module named 'app'"
- Ensure `requirements.txt` is in repo root
- Check that Python 3.9+ is used
- Redeploy

### Frontend shows 404 on routes
- Check `vercel.json` rewrites are in place
- Ensure `web/static/` files are being served
- Clear Vercel cache and redeploy

---

## Local Testing Before Deploy

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env with your token
echo "GITHUB_TOKEN=your_token_here" > .env

# Run locally
uvicorn app.main:app --reload

# Visit http://localhost:8000
```

---

## Custom Domain

In Vercel dashboard:

1. **Settings** → **Domains**
2. Click **Add** → Enter your domain
3. Follow DNS instructions for your registrar
4. Wait for propagation (~24 hours)

---

## Scaling & Limits

- **Vercel Hobby**: 100GB bandwidth/month, OK for low traffic
- **Vercel Pro**: $20/month, better for production
- **GitHub API**: 60 req/hour (unauthenticated), 5000/hour (authenticated)
  - If token auth fails, falls back to unauthenticated

---

## Support

- Vercel docs: [vercel.com/docs](https://vercel.com/docs)
- GitHub API docs: [docs.github.com/api](https://docs.github.com/api)
- GitCheck repo: [github.com/cmd-d4ksh/GitCheck](https://github.com/cmd-d4ksh/GitCheck)
