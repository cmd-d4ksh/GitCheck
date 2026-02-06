# API Reference

## Base URL

```
http://localhost:8000
```

## Authentication

All requests require a valid GitHub token in the `.env` file.

## Endpoints

### 1. Health Check

**GET** `/`

Check if the API is running.

**Response:**
```json
{
  "status": "GitCheck API is running"
}
```

**Status Code:** 200

---

### 2. Analyze Repository

**POST** `/analyze`

Analyze a GitHub repository and return trust score.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| repo_url | string | Yes | Full GitHub repository URL |

**Example Request:**
```bash
POST /analyze?repo_url=https://github.com/python/cpython
```

**Response:**
```json
{
  "repository": "python/cpython",
  "metadata": {
    "stars": 71386,
    "forks": 34031,
    "open_issues": 9206,
    "contributors": 354,
    "archived": false
  },
  "features": {
    "commit_score": 1.0,
    "contributor_score": 1.0,
    "issue_score": 0.14
  },
  "ml_analysis": {
    "prediction": "Reliable",
    "confidence": 0.72
  },
  "rule_based_analysis": {
    "trust_score": 74,
    "risk_level": "Medium"
  },
  "warnings": null,
  "recommendation": "🟡 Generally safe, but monitor for updates. Some metrics are concerning."
}
```

**Status Codes:**
- 200: Success
- 400: Invalid request/repository
- 403: Repository is private
- 404: Repository not found
- 504: Request timeout

---

### 3. Rate Limit Status

**GET** `/rate-limit`

Check GitHub API rate limit status.

**Response:**
```json
{
  "remaining": 4500,
  "reset_time": 1707302400,
  "status": "healthy"
}
```

**Status Values:**
- "healthy" - More than 100 requests remaining
- "warning" - 10-100 requests remaining
- "critical" - Less than 10 requests remaining

**Status Code:** 200

---

## Response Fields

### Metadata Object
| Field | Type | Description |
|-------|------|-------------|
| stars | int | Number of GitHub stars |
| forks | int | Number of forks |
| open_issues | int | Number of open issues |
| contributors | int | Number of contributors |
| archived | bool | Whether repository is archived |

### Features Object
| Field | Type | Range | Description |
|-------|------|-------|-------------|
| commit_score | float | 0.0-1.0 | Recent commit activity |
| contributor_score | float | 0.0-1.0 | Contributor count score |
| issue_score | float | 0.0-1.0 | Issue resolution rate |

### ML Analysis Object
| Field | Type | Values | Description |
|-------|------|--------|-------------|
| prediction | string | "Reliable", "Unreliable" | ML model prediction |
| confidence | float | 0.0-1.0 | Confidence in prediction |

### Rule Based Analysis Object
| Field | Type | Range | Values | Description |
|-------|------|-------|--------|-------------|
| trust_score | int | 0-100 | Score | Overall trust score |
| risk_level | string | - | "Low", "Medium", "High" | Risk assessment |

---

## Error Handling

### 400 Bad Request

```json
{
  "detail": "Invalid repo_url parameter"
}
```

### 403 Forbidden

```json
{
  "detail": "Cannot analyze private repositories. GitCheck supports public repos only."
}
```

### 404 Not Found

```json
{
  "detail": "Repository not found. Check the URL and ensure the repo is public."
}
```

### 504 Gateway Timeout

```json
{
  "detail": "Request timeout. GitHub API is slow. Try again later."
}
```

---

## Rate Limiting

- Limit: 5,000 requests per hour (with authentication)
- Check `/rate-limit` before bulk operations
- Backoff strategy implemented for approaching limits

---

## Examples

### Python

```python
import requests

url = "http://localhost:8000/analyze"
params = {"repo_url": "https://github.com/django/django"}

response = requests.post(url, params=params)
data = response.json()

print(f"Trust Score: {data['rule_based_analysis']['trust_score']}")
print(f"Risk Level: {data['rule_based_analysis']['risk_level']}")
```

### JavaScript

```javascript
const repo_url = "https://github.com/nodejs/node";
const response = await fetch(
  `http://localhost:8000/analyze?repo_url=${encodeURIComponent(repo_url)}`,
  { method: 'POST' }
);
const data = await response.json();
console.log(data.rule_based_analysis);
```

### cURL

```bash
curl -X POST "http://localhost:8000/analyze?repo_url=https://github.com/facebook/react"
```
