"""Reliability scoring — weighted multi-dimensional score out of 100.

Categories:
    Activity        — is it moving? (commits, recency, trend)
    Community       — who is contributing? (contributors, bus factor)
    Maintenance     — is it being cared for? (issue/PR responsiveness, releases)
    Popularity      — adoption signal (stars, forks) — small weight; stars aren't maintenance
    Hygiene         — license, not archived, issues enabled

Every score is accompanied by a breakdown so users understand *why* the score
looks the way it does.
"""

from __future__ import annotations

from typing import Any

WEIGHTS: dict[str, float] = {
    "commit_score":         0.12,
    "recency_score":        0.18,
    "trend_score":          0.06,
    "contributor_score":    0.10,
    "bus_factor_score":     0.06,
    "responsiveness_score": 0.14,
    "issue_score":          0.06,
    "pr_score":             0.04,
    "release_score":        0.04,
    "license_score":        0.04,
    "star_score":           0.10,
    "fork_score":           0.06,
}

assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "Weights must sum to 1.0"

CATEGORY_MAP: dict[str, str] = {
    "commit_score":         "Activity",
    "recency_score":        "Activity",
    "trend_score":          "Activity",
    "contributor_score":    "Community",
    "bus_factor_score":     "Community",
    "responsiveness_score": "Maintenance",
    "issue_score":          "Maintenance",
    "pr_score":             "Maintenance",
    "release_score":        "Maintenance",
    "license_score":        "Hygiene",
    "star_score":           "Popularity",
    "fork_score":           "Popularity",
}

LABELS: dict[str, str] = {
    "commit_score":         "Commit volume (90d)",
    "recency_score":        "Recent push",
    "trend_score":          "Activity trend",
    "contributor_score":    "Contributor count",
    "bus_factor_score":     "Bus factor",
    "responsiveness_score": "Maintainer response",
    "issue_score":          "Issue close rate",
    "pr_score":             "PR merge rate",
    "release_score":        "Release cadence",
    "license_score":        "Licensed",
    "star_score":           "Stars",
    "fork_score":           "Forks",
}

THRESHOLDS: dict[str, int] = {
    "excellent": 85,
    "low_risk": 70,
    "medium_risk": 50,
}


def _risk_for_score(score: int) -> str:
    if score >= THRESHOLDS["low_risk"]:
        return "Low"
    if score >= THRESHOLDS["medium_risk"]:
        return "Medium"
    return "High"


def _status_for(score: int, days_since_push: int | None, archived: bool) -> str:
    if archived:
        return "Archived"
    if days_since_push is None:
        return "Unknown"
    if days_since_push > 540:
        return "Abandoned"
    if days_since_push > 180:
        return "Stale"
    if score >= THRESHOLDS["excellent"]:
        return "Thriving"
    if score >= THRESHOLDS["low_risk"]:
        return "Active"
    if score >= THRESHOLDS["medium_risk"]:
        return "Moderate"
    return "Risky"


def calculate_trust_score(features: dict[str, float], repo_data: dict[str, Any]) -> dict[str, Any]:
    """Produce the final score, risk level, health status, and a per-feature breakdown."""

    if repo_data.get("is_empty"):
        return {
            "score": 0,
            "risk_level": "High",
            "status": "Empty",
            "warning": "Repository appears to be empty.",
            "breakdown": [],
            "penalties": [],
        }

    raw_weighted = sum(WEIGHTS[key] * features.get(key, 0.0) for key in WEIGHTS)
    score = raw_weighted * 100

    penalties: list[dict[str, Any]] = []

    if repo_data.get("archived"):
        penalties.append({"name": "Archived", "delta": -25, "detail": "Repository is archived."})
        score -= 25
    elif (repo_data.get("days_since_push") or 0) > 365:
        penalties.append({"name": "Inactive 1y+", "delta": -15, "detail": "No pushes in the last year."})
        score -= 15
    elif (repo_data.get("days_since_push") or 0) > 180:
        penalties.append({"name": "Stale", "delta": -5, "detail": "No pushes in the last 6 months."})
        score -= 5

    if repo_data.get("disabled"):
        penalties.append({"name": "Disabled", "delta": -20, "detail": "Repository is disabled by GitHub."})
        score -= 20

    score = max(0, min(100, round(score)))
    risk_level = _risk_for_score(score)
    status = _status_for(score, repo_data.get("days_since_push"), bool(repo_data.get("archived")))

    breakdown = [
        {
            "feature": key,
            "label": LABELS[key],
            "category": CATEGORY_MAP[key],
            "weight": WEIGHTS[key],
            "raw": round(features.get(key, 0.0), 4),
            "contribution": round(WEIGHTS[key] * features.get(key, 0.0) * 100, 2),
        }
        for key in WEIGHTS
    ]
    breakdown.sort(key=lambda item: item["contribution"], reverse=True)

    return {
        "score": score,
        "risk_level": risk_level,
        "status": status,
        "breakdown": breakdown,
        "penalties": penalties,
    }


def category_summary(breakdown: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Roll up per-feature contributions into category totals (Activity, Community, ...)."""
    totals: dict[str, dict[str, float]] = {}
    for row in breakdown:
        cat = row["category"]
        entry = totals.setdefault(cat, {"category": cat, "contribution": 0.0, "weight": 0.0})
        entry["contribution"] += row["contribution"]
        entry["weight"] += row["weight"] * 100

    summary = []
    for entry in totals.values():
        pct_of_max = (entry["contribution"] / entry["weight"] * 100) if entry["weight"] else 0
        summary.append({
            "category": entry["category"],
            "contribution": round(entry["contribution"], 2),
            "max": round(entry["weight"], 2),
            "percent": round(pct_of_max, 1),
        })
    order = ["Activity", "Community", "Maintenance", "Popularity", "Hygiene"]
    summary.sort(key=lambda x: order.index(x["category"]) if x["category"] in order else 99)
    return summary


def summarize_highlights(features: dict[str, float], repo_data: dict[str, Any]) -> list[str]:
    """Positive things to highlight — max 5."""
    highlights: list[str] = []
    if (repo_data.get("commits_last_90_days") or 0) >= 50:
        highlights.append(f"Active development — {repo_data['commits_last_90_days']} commits in the last 90 days")
    if features.get("recency_score", 0) >= 0.9:
        highlights.append("Pushed within the last month")
    if features.get("trend_score", 0) >= 0.85:
        highlights.append("Commit activity is accelerating")
    if (repo_data.get("contributors") or 0) >= 15:
        highlights.append(f"Diverse contributor base — {repo_data['contributors']} contributors")
    if features.get("issue_score", 0) >= 0.7:
        rate = int(round(features["issue_score"] * 100))
        highlights.append(f"Strong issue responsiveness — {rate}% close rate")
    if features.get("pr_score", 0) >= 0.6:
        rate = int(round(features["pr_score"] * 100))
        highlights.append(f"Healthy PR workflow — {rate}% merge rate")
    if (repo_data.get("release_count") or 0) >= 3:
        highlights.append(f"Regular releases — {repo_data['release_count']} tagged releases")
    if (repo_data.get("stars") or 0) >= 1000:
        highlights.append(f"Strong adoption — {repo_data['stars']:,} stars")
    if repo_data.get("license"):
        highlights.append(f"Licensed ({repo_data['license']})")
    return highlights[:5]


def summarize_risks(features: dict[str, float], repo_data: dict[str, Any]) -> list[str]:
    """Concerning signals — max 5."""
    risks: list[str] = []
    if repo_data.get("archived"):
        risks.append("Repository is archived and no longer maintained")
    if repo_data.get("disabled"):
        risks.append("Repository is disabled by GitHub")

    days = repo_data.get("days_since_push")
    if days is not None:
        if days > 540:
            risks.append(f"No pushes in {days} days — likely abandoned")
        elif days > 180:
            risks.append(f"No recent pushes ({days} days since last push)")

    if (repo_data.get("commits_last_90_days") or 0) < 5 and not repo_data.get("archived"):
        risks.append(f"Very low recent activity — only {repo_data.get('commits_last_90_days', 0)} commits in 90 days")

    if features.get("trend_score", 0.5) <= 0.25:
        risks.append("Commit activity is declining sharply")

    if (repo_data.get("contributors") or 0) <= 1:
        risks.append("Single contributor — high bus factor risk")
    elif features.get("bus_factor_score", 0) <= 0.3 and (repo_data.get("contributors") or 0) > 0:
        risks.append("Contributions heavily concentrated in one author")

    issues = repo_data.get("issues") or {}
    if (repo_data.get("open_issues") or 0) > 300 and features.get("issue_score", 1) < 0.5:
        risks.append(f"Large unresolved issue backlog ({repo_data['open_issues']} open)")

    if (issues.get("opened_recently", 0) or 0) > 0 and (issues.get("closed_recently", 0) or 0) == 0:
        risks.append("Issues opened in the last 30 days but none closed")

    if not repo_data.get("license"):
        risks.append("No license detected — legal ambiguity for reuse")

    return risks[:5]


def recommend(score: int, status: str, risk_level: str) -> str:
    if status in ("Archived", "Abandoned"):
        return f"Avoid for production — {status.lower()}. Look for an actively maintained fork."
    if status == "Empty":
        return "Cannot assess — repository is empty."
    if risk_level == "Low" and status in ("Thriving", "Active"):
        return "Safe to adopt — strong health across activity, community, and maintenance."
    if risk_level == "Low":
        return "Generally safe — healthy signals with some minor concerns."
    if risk_level == "Medium":
        return "Adopt with monitoring — mixed signals. Verify maintainer responsiveness before committing."
    return "Use with caution — weak maintenance signals. Consider alternatives or forking."
