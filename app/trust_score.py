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
        0.4 * features["commit_score"] +
        0.3 * features["issue_score"] +
        0.3 * features["contributor_score"]
    ) * 100

    score = round(score)

    if score >= 75:
        risk = "Low"
    elif score >= 50:
        risk = "Medium"
    else:
        risk = "High"

    return {
        "trust_score": score,
        "risk_level": risk
    }
