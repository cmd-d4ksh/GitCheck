WEIGHTS = {
    "commit_score": 0.25,
    "issue_score": 0.2,
    "contributor_score": 0.2,
    "star_score": 0.2,
    "fork_score": 0.15
}

THRESHOLDS = {
    "low_risk_min": 75,
    "medium_risk_min": 50
}


def calculate_trust_score(features: dict, repo_data: dict = None):
    """
    Calculate trust score based on features.
    Returns Low/Medium/High risk assessment.
    """
    
    # Check if repo has any activity at all
    has_minimal_activity = (
        features.get("commit_score", 0) > 0 or
        features.get("contributor_score", 0) > 0
    )
    
    if not has_minimal_activity:
        # New or inactive repository
        return {
            "trust_score": 25,
            "risk_level": "High",
            "warning": "Repository has very low activity. Proceed with caution."
        }
    
    score = (
        WEIGHTS["commit_score"] * features.get("commit_score", 0) +
        WEIGHTS["issue_score"] * features.get("issue_score", 0) +
        WEIGHTS["contributor_score"] * features.get("contributor_score", 0) +
        WEIGHTS["star_score"] * features.get("star_score", 0) +
        WEIGHTS["fork_score"] * features.get("fork_score", 0)
    ) * 100

    score = round(score)

    if score >= THRESHOLDS["low_risk_min"]:
        risk = "Low"
    elif score >= THRESHOLDS["medium_risk_min"]:
        risk = "Medium"
    else:
        risk = "High"

    return {
        "trust_score": score,
        "risk_level": risk
    }


def explain_trust_score(features: dict):
    """Explain how the trust score is computed."""
    contributions = {
        "commit": round(WEIGHTS["commit_score"] * features.get("commit_score", 0) * 100, 1),
        "issues": round(WEIGHTS["issue_score"] * features.get("issue_score", 0) * 100, 1),
        "contributors": round(WEIGHTS["contributor_score"] * features.get("contributor_score", 0) * 100, 1),
        "stars": round(WEIGHTS["star_score"] * features.get("star_score", 0) * 100, 1),
        "forks": round(WEIGHTS["fork_score"] * features.get("fork_score", 0) * 100, 1)
    }

    return {
        "weights": WEIGHTS,
        "thresholds": THRESHOLDS,
        "contributions": contributions
    }
