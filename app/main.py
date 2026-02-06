from fastapi import FastAPI, HTTPException
from app.github_api import get_repo_metadata, check_rate_limit
from app.features import extract_features
from app.trust_score import calculate_trust_score
from app.ml_model import predict_trust

app = FastAPI(
    title="GitCheck",
    description="AI-Based Trust & Reliability Scoring System",
    version="0.2"
)


@app.get("/")
def root():
    return {"status": "GitCheck API is running"}


@app.get("/rate-limit")
def get_rate_limit():
    """Check current GitHub API rate limit"""
    remaining, reset_time = check_rate_limit()
    if remaining is None:
        raise HTTPException(status_code=500, detail="Could not check rate limit")
    
    return {
        "remaining": remaining,
        "reset_time": reset_time,
        "status": "healthy" if remaining > 100 else "warning" if remaining > 10 else "critical"
    }


@app.post("/analyze")
def analyze_repo(repo_url: str):
    """
    Analyze a GitHub repository and return trust score.
    
    - Supports public repositories only
    - Requires valid GitHub repository URL
    - Returns ML and rule-based risk assessments
    """
    if not repo_url or not isinstance(repo_url, str):
        raise HTTPException(status_code=400, detail="Invalid repo_url parameter")
    
    try:
        # Fetch repository metadata
        repo_data = get_repo_metadata(repo_url)
        
        # Extract features for scoring
        features = extract_features(repo_data)

        # Get ML prediction
        ml_result = predict_trust(features)

        # Get rule-based score
        rule_score = calculate_trust_score(features, repo_data)
        
        # Flag archived repos
        warnings = []
        if repo_data.get("archived"):
            warnings.append("Repository is archived and no longer maintained")
        
        if repo_data.get("is_empty"):
            warnings.append("Repository appears to be empty")

        return {
            "repository": repo_data["full_name"],
            "metadata": {
                "stars": repo_data["stars"],
                "forks": repo_data["forks"],
                "open_issues": repo_data["open_issues"],
                "contributors": repo_data["contributors"],
                "archived": repo_data.get("archived", False)
            },
            "features": features,
            "ml_analysis": {
                "prediction": "Reliable" if ml_result["ml_label"] == 1 else "Unreliable",
                "confidence": ml_result["confidence"]
            },
            "rule_based_analysis": rule_score,
            "warnings": warnings if warnings else None,
            "recommendation": generate_recommendation(ml_result, rule_score)
        }

    except Exception as e:
        error_msg = str(e)
        
        # Provide helpful error messages
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        elif "private" in error_msg.lower() or "denied" in error_msg.lower():
            raise HTTPException(status_code=403, detail=error_msg)
        elif "timeout" in error_msg.lower():
            raise HTTPException(status_code=504, detail="Request timeout. GitHub API is slow. Try again later.")
        else:
            raise HTTPException(status_code=400, detail=error_msg)


def generate_recommendation(ml_result, rule_score):
    """Generate actionable recommendation based on scores"""
    ml_reliable = ml_result["ml_label"] == 1
    rule_risk = rule_score["risk_level"]
    
    # Consensus scoring
    if ml_reliable and rule_risk == "Low":
        return "✅ Safe to use. Repository shows strong health indicators."
    elif ml_reliable or rule_risk == "Low":
        return "🟡 Generally safe, but monitor for updates. Some metrics are concerning."
    elif not ml_reliable or rule_risk == "High":
        return "⚠️  Use with caution. Repository shows poor maintenance indicators."
    else:
        return "❓ Mixed signals. Review activity and community engagement before using."
