# GitCheck Architecture

## System Design

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  /analyze - Main endpoint                        │   │
│  │  /rate-limit - Rate limit monitoring             │   │
│  │  /docs - Interactive API documentation           │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│              GitHub API Client                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Pagination Support (commits, issues, contrib)   │   │
│  │  Rate Limit Handling                             │   │
│  │  Timeout Management (10s)                        │   │
│  │  Error Handling (404, 403, network)              │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│           Feature Extraction & Scoring                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Commit Score (40% weight)                       │   │
│  │  Issue Close Rate (30% weight)                   │   │
│  │  Contributor Count (30% weight)                  │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│          ML Model & Rule-Based Scoring                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  ML Prediction (RandomForest)                    │   │
│  │  Trust Score Calculation (0-100)                 │   │
│  │  Risk Assessment (Low/Medium/High)               │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│            Response Generation                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Metadata (stars, forks, contributors)           │   │
│  │  Features & Scores                               │   │
│  │  Recommendations                                 │   │
│  │  Warnings (archived, empty repos)                │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

## Module Breakdown

### `github_api.py`
- Handles all GitHub API interactions
- Implements pagination for commits, issues, contributors
- Rate limit checking and backoff
- Timeout handling (10 seconds)
- Error handling for various HTTP status codes

### `features.py`
- Normalizes API metrics
- Calculates feature scores (0.0-1.0)
- Implements weighting system

### `ml_model.py`
- Loads pre-trained ML model (RandomForest)
- Generates binary predictions (Reliable/Unreliable)
- Provides confidence scores

### `trust_score.py`
- Rule-based scoring algorithm
- Generates trust score (0-100)
- Assigns risk levels (Low/Medium/High)

### `main.py`
- FastAPI application
- API endpoints
- Request validation
- Response generation
- Error handling and HTTP status codes

## Data Flow

1. User sends repository URL
2. API validates input
3. GitHub API client fetches metadata
4. Features are extracted and normalized
5. ML model and rule-based scoring run in parallel
6. Recommendations generated
7. Response returned with full analysis

## Configuration

- GitHub token: `.env` file
- Timeout: 10 seconds per request
- Page limits: 10 pages for commits, 5 for issues/contributors
- Port: 8000 (default)

## Dependencies

See `requirements.txt` for complete list:
- fastapi (web framework)
- uvicorn (ASGI server)
- requests (HTTP client)
- python-dotenv (environment variables)
- scikit-learn (ML models)
- pandas (data manipulation)
- joblib (model serialization)
