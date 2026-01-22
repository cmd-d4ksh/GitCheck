def calculate_trust_score(features: dict):
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
