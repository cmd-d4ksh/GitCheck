import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

GITHUB_API_BASE = "https://api.github.com"
TOKEN = os.getenv("GITHUB_TOKEN")

# 🔴 SAFETY CHECK (VERY IMPORTANT)
if not TOKEN:
    raise RuntimeError("GITHUB_TOKEN not found. Did you create the .env file?")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",   # correct for fine-grained PAT
    "Accept": "application/vnd.github+json",
    "User-Agent": "GitCheck-App"
}


def parse_repo_url(repo_url: str):
    parts = repo_url.rstrip("/").split("/")
    return parts[-2], parts[-1]


def get_commit_activity(owner: str, repo: str, days: int = 90):
    since = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits"
    params = {"since": since, "per_page": 100}

    response = requests.get(url, headers=HEADERS, params=params)

    if response.status_code != 200:
        print("Commit API error:", response.status_code, response.text)
        return 0

    return len(response.json())


def get_issue_close_rate(owner: str, repo: str):
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues"
    params = {"state": "all", "per_page": 100}

    response = requests.get(url, headers=HEADERS, params=params)

    if response.status_code != 200:
        print("Issue API error:", response.status_code, response.text)
        return 0

    issues = response.json()
    issues_only = [i for i in issues if "pull_request" not in i]

    total = len(issues_only)
    closed = len([i for i in issues_only if i.get("state") == "closed"])

    return round(closed / total, 2) if total > 0 else 0


def get_contributor_count(owner: str, repo: str):
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contributors"

    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print("Contributor API error:", response.status_code, response.text)
        return 0

    return len(response.json())


def get_repo_metadata(repo_url: str):
    owner, repo = parse_repo_url(repo_url)
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"

    response = requests.get(url, headers=HEADERS)

    # 🔥 IMPORTANT: SHOW REAL GITHUB ERROR
    if response.status_code != 200:
        raise Exception(
            f"GitHub API error {response.status_code}: {response.text}"
        )

    data = response.json()

    return {
        "full_name": data["full_name"],
        "stars": data["stargazers_count"],
        "forks": data["forks_count"],
        "open_issues": data["open_issues_count"],
        "watchers": data["watchers_count"],
        "commits_last_90_days": get_commit_activity(owner, repo),
        "issue_close_rate": get_issue_close_rate(owner, repo),
        "contributors": get_contributor_count(owner, repo)
    }
