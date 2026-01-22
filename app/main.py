from fastapi import FastAPI, HTTPException
from app.github_api import get_repo_metadata
from app.features import extract_features
from app.trust_score import calculate_trust_score

app = FastAPI(
    title="GitCheck",
    description="AI-Based Trust & Reliability Scoring System",
    version="0.2"
)


@app.get("/")
def root():
    return {"status": "GitCheck API is running"}


@app.post("/analyze")
def analyze_repo(repo_url: str):
    try:
        repo_data = get_repo_metadata(repo_url)
        features = extract_features(repo_data)
        trust = calculate_trust_score(features)

        return {
            "repository": repo_data["full_name"],
            "features": features,
            "analysis": trust
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
