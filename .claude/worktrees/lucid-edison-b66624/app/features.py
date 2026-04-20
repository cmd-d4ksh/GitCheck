"""Feature extraction — normalizes raw GitHub metrics into [0, 1] signals.

Each feature is a named signal documented inline with its intent. Normalization
uses soft caps that reflect "what a healthy project looks like", not extremes
(e.g., 100+ commits in 90 days is already strong; 10k+ stars doesn't need more weight).
"""

from __future__ import annotations

import math
from typing import Any


def _sat(value: float, cap: float) -> float:
    """Saturating normalization: value/cap clipped to [0, 1]."""
    if cap <= 0:
        return 0.0
    return max(0.0, min(1.0, value / cap))


def _log_sat(value: float, cap: float) -> float:
    """Log-scaled saturation — dampens the long tail (good for stars/forks)."""
    if value <= 0:
        return 0.0
    if cap <= 1:
        return 1.0
    return max(0.0, min(1.0, math.log1p(value) / math.log1p(cap)))


def _recency_score(days_since_push: int | None) -> float:
    """1.0 if pushed today, decays to 0 over ~18 months of inactivity."""
    if days_since_push is None:
        return 0.0
    if days_since_push <= 7:
        return 1.0
    if days_since_push <= 30:
        return 0.9
    if days_since_push <= 90:
        return 0.75
    if days_since_push <= 180:
        return 0.5
    if days_since_push <= 365:
        return 0.25
    if days_since_push <= 540:
        return 0.1
    return 0.0


def _trend_score(weekly_commits: list[dict] | None) -> float:
    """Compare the last 13 weeks against the prior 13 weeks to detect trend.

    Returns 0.5 for flat, >0.5 for growing, <0.5 for declining.
    """
    if not weekly_commits or len(weekly_commits) < 20:
        return 0.5
    totals = [w.get("total", 0) for w in weekly_commits]
    recent = sum(totals[-13:])
    prior = sum(totals[-26:-13])
    if recent + prior == 0:
        return 0.0
    if prior == 0:
        return 0.9
    ratio = recent / prior
    if ratio >= 1.5:
        return 1.0
    if ratio >= 1.1:
        return 0.85
    if ratio >= 0.9:
        return 0.65
    if ratio >= 0.6:
        return 0.4
    if ratio >= 0.3:
        return 0.25
    return 0.1


def _maintainer_responsiveness(repo: dict[str, Any]) -> float:
    """Proxy for maintainer responsiveness — blends issue and PR closure rates."""
    issue_rate = repo.get("issue_close_rate", 0.0) or 0.0
    pr_rate = repo.get("pr_merge_rate", 0.0) or 0.0
    issues = repo.get("issues", {}) or {}
    opened = issues.get("opened_recently", 0) or 0
    closed = issues.get("closed_recently", 0) or 0
    recent_activity = 0.0
    if opened + closed > 0:
        recent_activity = min(1.0, closed / max(1, opened))
    return round(0.45 * issue_rate + 0.35 * pr_rate + 0.20 * recent_activity, 4)


def _bus_factor_score(repo: dict[str, Any]) -> float:
    """How concentrated contributions are among top contributors.

    If the #1 contributor does >70% of work, bus factor is poor (score low).
    If contributions are spread across 5+ people, score is high.
    """
    contributors = repo.get("contributors", 0) or 0
    top = repo.get("top_contributors") or []
    if contributors == 0 or not top:
        return 0.0

    total = sum(c.get("contributions", 0) for c in top) or 1
    top_share = top[0].get("contributions", 0) / total if top else 1.0

    diversity = _sat(contributors, 15)
    concentration_penalty = 1.0 - max(0.0, (top_share - 0.5) / 0.5)
    return round(max(0.0, min(1.0, 0.6 * diversity + 0.4 * concentration_penalty)), 4)


def extract_features(repo: dict[str, Any]) -> dict[str, float]:
    """Return normalized [0, 1] features used by the scoring layer."""
    commits_90 = repo.get("commits_last_90_days", 0) or 0
    contributors = repo.get("contributors", 0) or 0
    stars = repo.get("stars", 0) or 0
    forks = repo.get("forks", 0) or 0
    issue_close_rate = repo.get("issue_close_rate", 0.0) or 0.0
    pr_merge_rate = repo.get("pr_merge_rate", 0.0) or 0.0

    commit_score = _sat(commits_90, 50)
    contributor_score = _sat(contributors, 20)
    star_score = _log_sat(stars, 10000)
    fork_score = _log_sat(forks, 2000)
    recency_score = _recency_score(repo.get("days_since_push"))
    trend_score = _trend_score(repo.get("weekly_commits"))
    responsiveness_score = _maintainer_responsiveness(repo)
    bus_factor_score = _bus_factor_score(repo)
    release_score = _sat(repo.get("release_count", 0), 5)
    license_score = 1.0 if repo.get("license") else 0.0

    return {
        "commit_score": round(commit_score, 4),
        "contributor_score": round(contributor_score, 4),
        "issue_score": round(issue_close_rate, 4),
        "pr_score": round(pr_merge_rate, 4),
        "star_score": round(star_score, 4),
        "fork_score": round(fork_score, 4),
        "recency_score": round(recency_score, 4),
        "trend_score": round(trend_score, 4),
        "responsiveness_score": round(responsiveness_score, 4),
        "bus_factor_score": round(bus_factor_score, 4),
        "release_score": round(release_score, 4),
        "license_score": round(license_score, 4),
    }
