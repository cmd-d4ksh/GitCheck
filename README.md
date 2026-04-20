# GitCheck

**AI-Based Trust & Reliability Scoring System for Open-Source Projects**

![Version](https://img.shields.io/badge/version-0.2-blue)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

GitCheck is a production-oriented intelligence system that evaluates open-source repositories and generates data-driven trust scores. Built with FastAPI, machine learning, and real GitHub metrics, it helps developers make informed decisions when selecting dependencies.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

Selecting a dependable open-source dependency is critical in modern software development. Traditional metrics like stars or forks often fail to reflect active maintenance, community support, or production-readiness.

GitCheck addresses this gap by:
- **Analyzing real GitHub activity** — commits, contributors, issues, and pull requests
- **Extracting intelligent features** — maintenance patterns, sustainability signals, and collaboration health
- **Applying ML-powered scoring** — predicting long-term reliability and project maturity
- **Providing actionable insights** — clear scores and detailed explanations for decision-making

Perfect for developers, technical leads, and teams making critical dependency decisions.

---

## Key Features

### 🔍 Repository Intelligence
- Automatic GitHub data collection via the GitHub API
- Real-time analysis of contribution patterns and maintenance activity
- Detection of project stagnation and risk indicators

### 🤖 ML-Powered Scoring
- Intelligent feature extraction from repository metrics
- Trained models for reliable trust prediction
- Classification of project maturity levels

### 📊 Comprehensive Analysis
- **Contribution Dynamics** — Commit frequency, contributor consistency, engagement trends
- **Maintenance Health** — Issue response times, PR handling, update recency
- **Sustainability Signals** — Long-term trends, activity volatility, ecosystem impact

### 🎯 Interactive Dashboard
- Clean, responsive web interface
- Real-time repository analysis
- Detailed trust score explanations and recommendations

### ⚡ Production-Ready API
- FastAPI with automatic documentation
- Rate limit monitoring and error handling
- RESTful endpoints for integration

---

## Tech Stack

- **Backend:** FastAPI, Uvicorn
- **Data Processing:** Pandas, Scikit-learn
- **External APIs:** GitHub REST API
- **ML Models:** Scikit-learn (trained classification & regression)
- **Frontend:** HTML5, CSS3, JavaScript
- **Environment:** Python 3.9+

---

## Quick Start

### Prerequisites
- Python 3.9 or higher
- Git
- GitHub API token (optional but recommended for higher rate limits)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/cmd-d4ksh/GitCheck
cd GitCheck
```

2. **Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your GitHub API token (optional but recommended)
```

5. **Run the application**
```bash
uvicorn app.main:app --reload
```

6. **Access the application**
- Web Dashboard: http://localhost:8000
- API Documentation: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

---

## Project Structure

```
GitCheck/
├── app/                          # Core backend application
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entry point
│   ├── github_api.py             # GitHub API integration
│   ├── features.py               # Feature extraction pipeline
│   ├── ml_model.py               # ML model prediction logic
│   └── trust_score.py            # Trust scoring & classification
│
├── ml/                           # Machine learning pipeline
│   ├── train_model.py            # Model training script
│   └── dataset.csv               # Training dataset
│
├── web/                          # Frontend application
│   └── static/
│       ├── index.html            # Main dashboard page
│       ├── css/style.css         # Styling
│       └── js/app.js             # Frontend logic
│
├── docs/                         # Comprehensive documentation
│   ├── API_REFERENCE.md          # API endpoint documentation
│   ├── API_RUNNING.md            # API deployment guide
│   ├── ARCHITECTURE.md           # System architecture overview
│   ├── TESTING.md                # Testing strategies & examples
│   ├── DEPLOYMENT.md             # Production deployment guide
│   ├── CONTRIBUTING.md           # Contribution guidelines
│   ├── PRODUCTION_READY_CHECKLIST.md
│   └── FAQ.md                    # Frequently asked questions
│
├── .env.example                  # Environment variable template
├── .gitignore                    # Git ignore rules
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

---

## API Reference

### Base URL
```
http://localhost:8000
```

### Health & Status Endpoints

#### Check API Health
```bash
GET /api/health
```
Response:
```json
{
  "status": "GitCheck API is running"
}
```

#### Check GitHub Rate Limit
```bash
GET /rate-limit
```
Response:
```json
{
  "remaining": 4500,
  "reset_time": "2026-04-20T12:30:00Z",
  "status": "healthy"
}
```

### Repository Analysis Endpoints

#### Get Trust Score Report
```bash
GET /api/score/{owner}/{repo}
```

**Parameters:**
- `owner` (string, path): GitHub repository owner
- `repo` (string, path): Repository name

**Response:**
```json
{
  "trust_score": 8.5,
  "maturity_level": "production-ready",
  "recommendation": "Safe to adopt",
  "details": {
    "contribution_health": 8.2,
    "maintenance_activity": 8.7,
    "sustainability": 8.4
  }
}
```

### Full API Documentation

**Complete API documentation is available at:**
- **Swagger UI:** `/api/docs` (when running application)
- **ReDoc:** `/api/redoc` (alternative documentation view)

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# GitHub API Configuration
GITHUB_TOKEN=your_github_api_token_here
GITHUB_API_URL=https://api.github.com

# Application Settings
DEBUG=false
LOG_LEVEL=info
```

### Getting a GitHub API Token

1. Go to [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token"
3. Select scopes: `public_repo`, `read:user`
4. Copy the token and add to `.env`

---

## Documentation

Comprehensive documentation is available in the `docs/` directory:

| Document | Purpose |
|----------|---------|
| [API_REFERENCE.md](docs/API_REFERENCE.md) | Complete API endpoint specifications |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design & data flow diagrams |
| [TESTING.md](docs/TESTING.md) | Testing strategies & test cases |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Production deployment setup |
| [CONTRIBUTING.md](docs/CONTRIBUTING.md) | Development guidelines |
| [FAQ.md](docs/FAQ.md) | Common questions & troubleshooting |
| [PRODUCTION_READY_CHECKLIST.md](docs/PRODUCTION_READY_CHECKLIST.md) | Pre-production verification |

---

## Development

### Running Tests
```bash
pytest tests/
```

### Training ML Models
```bash
python ml/train_model.py
```

### Development Server with Hot Reload
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines on:
- Code style and formatting
- Testing requirements
- Pull request process
- Issue reporting

---

## License

This project is licensed under the MIT License — see LICENSE file for details.

---

## Support & Questions

- **Issues:** Report bugs on [GitHub Issues](https://github.com/cmd-d4ksh/GitCheck/issues)
- **Documentation:** Check [FAQ.md](docs/FAQ.md) for common questions
- **Architecture:** See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for system design details

---

**Built with ❤️ for the open-source community**






