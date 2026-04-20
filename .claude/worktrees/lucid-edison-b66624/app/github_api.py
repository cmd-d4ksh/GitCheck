"""GitHub API client for GitCheck.

Robust, read-only GitHub client that:
- Parses many URL formats (https, ssh-like, with/without .git, with trailing paths)
- Uses the Search API for accurate total counts (issues, PRs, contributors)
- Caches results per-repo for CACHE_TTL_SECONDS to avoid redundant calls
- Handles rate limits gracefully and propagates clear errors to the API layer
- Works without a token (lower rate limit), preferred with one
"""

from __future__ import annotations

import os
import re
import time
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import requests
from dotenv import load_dotenv


env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

GITHUB_API_BASE = "https://api.github.com"
TOKEN = os.getenv("GITHUB_TOKEN")
REQUEST_TIMEOUT = 15
CACHE_TTL_SECONDS = 300
UA = "GitCheck/1.0 (+https://github.com/cmd-d4ksh/GitCheck)"

HEADERS: dict[str, str] = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": UA,
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


class GitHubError(Exception):
    """Normalized GitHub error with status code classification."""

    def __init__(self, message: str, status: int = 500):
        super().__init__(message)
        self.status = status


_cache: dict[str, tuple[float, Any]] = {}
_cache_lock = threading.Lock()


def _cache_get(key: str) -> Optional[Any]:
    with _cache_lock:
        entry = _cache.get(key)
        if not entry:
            return None
        ts, value = entry
        if time.time() - ts > CACHE_TTL_SECONDS:
            _cache.pop(key, None)
            return None
        return value


def _cache_set(key: str, value: Any) -> None:
    with _cache_lock:
        _cache[key] = (time.time(), value)


_GITHUB_URL = re.compile(
    r"^(?:(?:https?://)?(?:www\.)?github\.com|git@github\.com)[/:]+"
    r"(?P<owner>[\w.\-]+)/(?P<repo>[\w.\-]+?)(?:\.git)?/?(?:[/?#].*)?$",
    re.IGNORECASE,
)
_SHORT = re.compile(r"^(?P<owner>[\w.\-]+)/(?P<repo>[\w.\-]+?)(?:\.git)?$")


def parse_repo_url(repo_url: str) -> tuple[str, str]:
    """Parse a GitHub URL or `owner/repo` shorthand. Raises GitHubError on invalid input."""
    if not repo_url or not isinstance(repo_url, str):
        raise GitHubError("Empty repository URL.", status=400)

    value = repo_url.strip()
    match = _GITHUB_URL.match(value) or _SHORT.match(value)
    if not match:
        raise GitHubError(
            "Invalid GitHub URL. Use https://github.com/owner/repo or owner/repo.",
            status=400,
        )
    return match.group("owner"), match.group("repo")


def _request(url: str, params: Optional[dict] = None) -> requests.Response:
    try:
        return requests.get(url, headers=HEADERS, params=params, timeout=REQUEST_TIMEOUT)
    except requests.Timeout as exc:
        raise GitHubError(f"GitHub API timeout while fetching {url}.", status=504) from exc
    except requests.RequestException as exc:
        raise GitHubError(f"Network error talking to GitHub: {exc}", status=502) from exc


def _raise_for_status(response: requests.Response, context: str) -> None:
    if response.status_code == 200 or response.status_code == 202:
        return
    if response.status_code == 404:
        raise GitHubError("Repository not found. Check the URL and ensure the repo is public.", status=404)
    if response.status_code == 401:
        raise GitHubError("GitHub rejected the credentials. Check GITHUB_TOKEN.", status=401)
    if response.status_code == 403:
        remaining = response.headers.get("X-RateLimit-Remaining")
        if remaining == "0":
            reset = response.headers.get("X-RateLimit-Reset")
            when = ""
            if reset:
                when = datetime.fromtimestamp(int(reset), tz=timezone.utc).strftime(" at %H:%M UTC")
            raise GitHubError(f"GitHub rate limit exceeded{when}. Add a GITHUB_TOKEN or wait.", status=429)
        raise GitHubError("Access denied by GitHub (private repo or forbidden).", status=403)
    if response.status_code == 409:
        raise GitHubError("Repository is empty or conflicted.", status=409)
    raise GitHubError(f"GitHub API error {response.status_code} for {context}.", status=502)


def check_rate_limit() -> tuple[Optional[int], Optional[int]]:
    """Return (remaining_core_calls, reset_unix)."""
    try:
        response = _request(f"{GITHUB_API_BASE}/rate_limit")
        if response.status_code != 200:
            return None, None
        core = response.json().get("resources", {}).get("core", {})
        return core.get("remaining"), core.get("reset")
    except GitHubError:
        return None, None


def _search_count(query: str) -> int:
    """Use Search API to get accurate total count (single request)."""
    cache_key = f"search::{query}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    response = _request(f"{GITHUB_API_BASE}/search/issues", params={"q": query, "per_page": 1})
    if response.status_code != 200:
        return 0
    total = int(response.json().get("total_count", 0))
    _cache_set(cache_key, total)
    return total


def get_commit_count_since(owner: str, repo: str, since_iso: str) -> int:
    """Get exact commit count since a date using Link header pagination.

    Strategy: request per_page=1 and parse the 'last' link rel for the total count.
    Falls back to counting one page when the Link header is absent.
    """
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits"
    response = _request(url, params={"since": since_iso, "per_page": 1})
    if response.status_code == 409:
        return 0
    if response.status_code != 200:
        return 0

    link = response.headers.get("Link", "")
    match = re.search(r"[?&]page=(\d+)>; rel=\"last\"", link)
    if match:
        return int(match.group(1))
    data = response.json()
    return len(data) if isinstance(data, list) else 0


def get_commit_activity_timeline(owner: str, repo: str, retries: int = 4) -> Optional[list[dict]]:
    """Weekly commit totals for the last 52 weeks (GitHub stats endpoint).

    GitHub returns 202 while generating stats — we retry with backoff so the
    first analysis for a cold repo still gets the chart.
    """
    cache_key = f"timeline::{owner}/{repo}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/stats/commit_activity"
    for attempt in range(retries + 1):
        response = _request(url)
        if response.status_code == 202:
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
                continue
            return None
        if response.status_code != 200:
            return None
        data = response.json()
        if not isinstance(data, list):
            return None
        timeline = [{"week": item.get("week"), "total": item.get("total", 0)} for item in data]
        _cache_set(cache_key, timeline)
        return timeline
    return None


def get_contributor_count(owner: str, repo: str) -> int:
    """Accurate contributor count via Link header pagination with anon=1."""
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contributors"
    response = _request(url, params={"per_page": 1, "anon": "1"})
    if response.status_code == 204:
        return 0
    if response.status_code != 200:
        return 0

    link = response.headers.get("Link", "")
    match = re.search(r"[?&]page=(\d+)>; rel=\"last\"", link)
    if match:
        return int(match.group(1))
    data = response.json()
    return len(data) if isinstance(data, list) else 0


def get_top_contributors(owner: str, repo: str, limit: int = 5) -> list[dict]:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contributors"
    response = _request(url, params={"per_page": limit})
    if response.status_code != 200:
        return []
    data = response.json()
    if not isinstance(data, list):
        return []
    return [
        {
            "login": item.get("login") or "(anonymous)",
            "contributions": item.get("contributions", 0),
            "avatar_url": item.get("avatar_url"),
            "html_url": item.get("html_url"),
        }
        for item in data[:limit]
    ]


def get_issue_stats(owner: str, repo: str) -> dict[str, int]:
    """Get open/closed issue counts and recent activity via Search API (accurate + fast)."""
    base = f"repo:{owner}/{repo} is:issue"
    thirty_days = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    return {
        "open": _search_count(f"{base} is:open"),
        "closed": _search_count(f"{base} is:closed"),
        "closed_recently": _search_count(f"{base} is:closed closed:>={thirty_days}"),
        "opened_recently": _search_count(f"{base} created:>={thirty_days}"),
    }


def get_pr_stats(owner: str, repo: str) -> dict[str, int]:
    base = f"repo:{owner}/{repo} is:pr"
    thirty_days = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    return {
        "open": _search_count(f"{base} is:open"),
        "merged": _search_count(f"{base} is:merged"),
        "closed": _search_count(f"{base} is:closed"),
        "merged_recently": _search_count(f"{base} is:merged merged:>={thirty_days}"),
    }


def get_releases(owner: str, repo: str) -> list[dict]:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/releases"
    response = _request(url, params={"per_page": 5})
    if response.status_code != 200:
        return []
    data = response.json()
    return data if isinstance(data, list) else []


def get_repo_metadata(repo_url: str) -> dict:
    """Fetch everything we need about a repo. Cached per-repo for CACHE_TTL_SECONDS.

    The commit-activity timeline is fetched and cached separately because GitHub
    generates it asynchronously — we always try to upgrade a cached repo record
    with a timeline if the first attempt returned 202.
    """
    owner, repo = parse_repo_url(repo_url)
    cache_key = f"repo::{owner}/{repo}"
    cached = _cache_get(cache_key)
    if cached is not None:
        if cached.get("weekly_commits") is None and not cached.get("is_empty"):
            fresh = get_commit_activity_timeline(owner, repo)
            if fresh is not None:
                cached = {**cached, "weekly_commits": fresh}
                _cache_set(cache_key, cached)
        return cached

    response = _request(f"{GITHUB_API_BASE}/repos/{owner}/{repo}")
    _raise_for_status(response, f"{owner}/{repo}")
    data = response.json()

    if data.get("private"):
        raise GitHubError("Cannot analyze private repositories. GitCheck supports public repos only.", status=403)

    is_empty = (data.get("size") or 0) == 0

    pushed_at = data.get("pushed_at")
    updated_at = data.get("updated_at")
    created_at = data.get("created_at")
    days_since_push = _days_since(pushed_at)
    age_days = _days_since(created_at) or 0

    since_iso = (datetime.now(timezone.utc) - timedelta(days=90)).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    commits_90 = 0 if is_empty else get_commit_count_since(owner, repo, since_iso)
    contributors = 0 if is_empty else get_contributor_count(owner, repo)
    weekly_commits = None if is_empty else get_commit_activity_timeline(owner, repo)
    issues = get_issue_stats(owner, repo) if not is_empty else {"open": 0, "closed": 0, "closed_recently": 0, "opened_recently": 0}
    prs = get_pr_stats(owner, repo) if not is_empty else {"open": 0, "merged": 0, "closed": 0, "merged_recently": 0}
    top_contributors = get_top_contributors(owner, repo) if not is_empty else []
    releases = get_releases(owner, repo) if not is_empty else []

    total_issues = issues["open"] + issues["closed"]
    issue_close_rate = round(issues["closed"] / total_issues, 3) if total_issues > 0 else 0.0

    total_prs = prs["merged"] + prs["closed"] + prs["open"]
    pr_merge_rate = round(prs["merged"] / total_prs, 3) if total_prs > 0 else 0.0

    license_info = data.get("license") or {}

    result = {
        "full_name": data["full_name"],
        "html_url": data.get("html_url"),
        "description": data.get("description") or "",
        "language": data.get("language"),
        "topics": data.get("topics") or [],
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "watchers": data.get("subscribers_count") or data.get("watchers_count", 0),
        "open_issues": data.get("open_issues_count", 0),
        "archived": bool(data.get("archived")),
        "disabled": bool(data.get("disabled")),
        "is_empty": is_empty,
        "default_branch": data.get("default_branch"),
        "license": license_info.get("spdx_id") or license_info.get("name"),
        "has_issues_enabled": bool(data.get("has_issues")),
        "pushed_at": pushed_at,
        "updated_at": updated_at,
        "created_at": created_at,
        "days_since_push": days_since_push,
        "age_days": age_days,
        "contributors": contributors,
        "top_contributors": top_contributors,
        "commits_last_90_days": commits_90,
        "weekly_commits": weekly_commits,
        "issues": issues,
        "issue_close_rate": issue_close_rate,
        "pull_requests": prs,
        "pr_merge_rate": pr_merge_rate,
        "release_count": len(releases),
        "latest_release": releases[0].get("tag_name") if releases else None,
        "owner": owner,
        "repo": repo,
    }

    _cache_set(cache_key, result)
    return result


def _days_since(iso_ts: Optional[str]) -> Optional[int]:
    if not iso_ts:
        return None
    try:
        dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return max(0, (datetime.now(timezone.utc) - dt).days)
