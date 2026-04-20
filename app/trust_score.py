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
    
    has_minimal_activity = (
        features.get("commit_score", 0) > 0 or
        features.get("contributor_score", 0) > 0
    )
    
    if not has_minimal_activity:

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


def classify_maturity(features: dict, repo_data: dict):
    """Classify repository maturity based on activity, scale, and trend."""
    commits = repo_data.get("commits_last_90_days", 0) or 0
    contributors = repo_data.get("contributors", 0) or 0
    stars = repo_data.get("stars", 0) or 0
    weekly = repo_data.get("weekly_commits") or []

    trend = "stable"
    if len(weekly) >= 26:
        last = weekly[-13:]
        prev = weekly[-26:-13]
        last_avg = sum([w.get("total", 0) for w in last]) / max(len(last), 1)
        prev_avg = sum([w.get("total", 0) for w in prev]) / max(len(prev), 1)
        if prev_avg > 0:
            delta = (last_avg - prev_avg) / prev_avg
            if delta > 0.2:
                trend = "rising"
            elif delta < -0.2:
                trend = "falling"

    if stars >= 1000 and contributors >= 20 and commits >= 50:
        return "Mature" if trend != "falling" else "Declining"
    if trend == "rising" and (commits >= 10 or contributors >= 5):
        return "Growing"
    if trend == "falling":
        return "Declining"
    return "Early"
