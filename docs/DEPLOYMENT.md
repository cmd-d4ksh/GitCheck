# Deployment Guide

## Local Development

### Prerequisites
- Python 3.10+
- GitHub personal access token
- Virtual environment

### Setup

```bash
# Clone repository
git clone https://github.com/cmd-d4ksh/GitCheck.git
cd GitCheck

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GITHUB_TOKEN
```

### Running Locally

```bash
# Start the API server
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Server will be available at http://127.0.0.1:8000
# API docs: http://127.0.0.1:8000/docs
```

## Production Deployment

### Using Gunicorn

```bash
# Install gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Using Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run
docker build -t gitcheck .
docker run -p 8000:8000 --env-file .env gitcheck
```

### Using Supervisor (for continuous uptime)

```ini
[program:gitcheck]
command=/path/to/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
directory=/path/to/GitCheck
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/gitcheck.log
```

## Environment Variables

Create `.env` file with:

```
GITHUB_TOKEN=your_github_personal_access_token_here
```

## Monitoring

- Check rate limits: `GET /rate-limit`
- Health check: `GET /`
- Monitor logs for errors
- Set up alerts for API failures

## Security Considerations

1. **API Rate Limiting**: Implement rate limiting middleware
2. **Token Rotation**: Rotate GitHub tokens regularly
3. **HTTPS**: Always use HTTPS in production
4. **Logging**: Don't log sensitive information
5. **Error Messages**: Don't expose internal errors to users

## Scaling

- Use load balancer (nginx, HAProxy)
- Run multiple uvicorn workers
- Implement caching layer (Redis)
- Database for storing analysis results
- Background job queue for heavy computations
