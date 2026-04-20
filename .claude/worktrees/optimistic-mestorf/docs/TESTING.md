# Testing Guide

## Overview

This guide covers testing strategies for GitCheck to ensure reliability and quality.

## Unit Tests

### Running Tests

```bash
# Install pytest
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test
pytest tests/test_github_api.py
```

### Test Structure

```
tests/
├── __init__.py
├── test_github_api.py      # GitHub API interactions
├── test_features.py        # Feature extraction
├── test_trust_score.py     # Trust score calculation
├── test_ml_model.py        # ML predictions
└── conftest.py             # Pytest configuration
```

## Mocking GitHub API

```python
import pytest
from unittest.mock import patch, MagicMock

@patch('app.github_api.requests.get')
def test_get_repo_metadata(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'full_name': 'python/cpython',
        'stargazers_count': 71386,
        'forks_count': 34031,
        'open_issues_count': 9206,
        'watchers_count': 500000,
        'archived': False,
        'private': False,
        'size': 1000
    }
    mock_get.return_value = mock_response
    
    # Test code here
    assert True
```

## Integration Tests

Test API endpoints directly:

```bash
# Start server
python -m uvicorn app.main:app &

# Test endpoints
curl http://localhost:8000/
curl -X POST "http://localhost:8000/analyze?repo_url=https://github.com/python/cpython"
```

## Test Coverage Goals

- API Layer: 90%+
- GitHub Client: 85%+
- Feature Extraction: 95%+
- Trust Score: 95%+
- ML Model: 80%+

## Continuous Integration

Set up GitHub Actions for automated testing on push/PR:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pytest --cov=app
```

## Performance Testing

```bash
# Install locust
pip install locust

# Create loadtest.py and run
locust -f loadtest.py
```

## Manual Testing Checklist

- [ ] Public repository analysis
- [ ] Private repository rejection
- [ ] Archived repository warning
- [ ] Empty repository handling
- [ ] Rate limit check
- [ ] Timeout scenarios
- [ ] Invalid URL handling
- [ ] Network error handling
- [ ] Large repository (10k+ commits)
- [ ] Small repository (few commits)
