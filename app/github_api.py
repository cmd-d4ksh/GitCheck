import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta
from pathlib import Path
import time

# Load .env from the project root directory
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

GITHUB_API_BASE = "https://api.github.com"
TOKEN = os.getenv("GITHUB_TOKEN")
REQUEST_TIMEOUT = 10  # seconds

# 🔴 SAFETY CHECK (VERY IMPORTANT)
if not TOKEN:
    raise RuntimeError(f"GITHUB_TOKEN not found. Please create .env file at {env_path}")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",   # correct for fine-grained PAT
    "Accept": "application/vnd.github+json",
    "User-Agent": "GitCheck-App"
}


def check_rate_limit():
    """Check GitHub API rate limit status"""
    url = f"{GITHUB_API_BASE}/rate_limit"
    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            remaining = data["resources"]["core"]["remaining"]
            reset_time = data["resources"]["core"]["reset"]
            return remaining, reset_time
    except Exception as e:
        print(f"Rate limit check failed: {e}")
    return None, None


def handle_rate_limit(remaining, reset_time):
    """Handle rate limiting with exponential backoff"""
    if remaining is not None and remaining < 10:
        sleep_time = max(0, reset_time - datetime.utcnow().timestamp())
        if sleep_time > 0:
            print(f"Rate limit approaching. Waiting {sleep_time:.0f} seconds...")
            time.sleep(min(sleep_time, 60))  # Cap at 60 seconds


def parse_repo_url(repo_url: str):
    parts = repo_url.rstrip("/").split("/")
    return parts[-2], parts[-1]


def get_commit_activity(owner: str, repo: str, days: int = 90):
    """Get total commits in the last N days with pagination"""
    since = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits"
    
    total_commits = 0
    page = 1
    max_pages = 10  # Limit to prevent excessive API calls
    
    while page <= max_pages:
        params = {"since": since, "per_page": 100, "page": page}
        
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=REQUEST_TIMEOUT)
            
            if response.status_code == 409:
                # Repository is empty
                return 0
            elif response.status_code != 200:
                print(f"Commit API error: {response.status_code}")
                return total_commits if total_commits > 0 else 0
            
            commits = response.json()
            if not commits:
                break
            
            total_commits += len(commits)
            
            # Check if there are more pages
            if len(commits) < 100:
                break
            
            page += 1
            
        except requests.Timeout:
            print(f"Timeout fetching commits (page {page}). Returning partial count: {total_commits}")
            break
        except Exception as e:
            print(f"Error fetching commits: {e}")
            break
    
    return total_commits


def get_issue_close_rate(owner: str, repo: str):
    """Get issue close rate with pagination"""
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues"
    
    total_issues = 0
    closed_issues = 0
    page = 1
    max_pages = 5  # Limit pagination to keep performance reasonable
    
    # First fetch all closed issues
    while page <= max_pages:
        params = {"state": "closed", "per_page": 100, "page": page}
        
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=REQUEST_TIMEOUT)
            
            if response.status_code != 200:
                print(f"Issue API error: {response.status_code}")
                break
            
            issues = response.json()
            if not issues:
                break
            
            # Filter out pull requests
            issues_only = [i for i in issues if "pull_request" not in i]
            closed_issues += len(issues_only)
            
            if len(issues) < 100:
                break
            
            page += 1
            
        except requests.Timeout:
            print(f"Timeout fetching closed issues (page {page})")
            break
        except Exception as e:
            print(f"Error fetching closed issues: {e}")
            break
    
    # Then fetch all open issues
    page = 1
    while page <= max_pages:
        params = {"state": "open", "per_page": 100, "page": page}
        
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=REQUEST_TIMEOUT)
            
            if response.status_code != 200:
                break
            
            issues = response.json()
            if not issues:
                break
            
            # Filter out pull requests
            issues_only = [i for i in issues if "pull_request" not in i]
            total_issues += len(issues_only)
            
            if len(issues) < 100:
                break
            
            page += 1
            
        except requests.Timeout:
            print(f"Timeout fetching open issues (page {page})")
            break
        except Exception as e:
            print(f"Error fetching open issues: {e}")
            break
    
    total_issues += closed_issues
    
    if total_issues == 0:
        return 0
    
    return round(closed_issues / total_issues, 2)


def get_contributor_count(owner: str, repo: str):
    """Get contributor count with pagination"""
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contributors"
    
    total_contributors = 0
    page = 1
    max_pages = 5
    
    while page <= max_pages:
        params = {"per_page": 100, "page": page}
        
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=REQUEST_TIMEOUT)
            
            if response.status_code == 204:
                # No contributors (empty repo)
                return 0
            elif response.status_code != 200:
                print(f"Contributor API error: {response.status_code}")
                return total_contributors if total_contributors > 0 else 0
            
            contributors = response.json()
            if not contributors:
                break
            
            total_contributors += len(contributors)
            
            if len(contributors) < 100:
                break
            
            page += 1
            
        except requests.Timeout:
            print(f"Timeout fetching contributors (page {page}). Returning: {total_contributors}")
            break
        except Exception as e:
            print(f"Error fetching contributors: {e}")
            break
    
    return total_contributors


def get_repo_metadata(repo_url: str):
    """Fetch repository metadata with safety checks"""
    owner, repo = parse_repo_url(repo_url)
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)

        # 🔥 IMPORTANT: SHOW REAL GITHUB ERROR
        if response.status_code == 404:
            raise Exception("Repository not found. Check the URL and ensure the repo is public.")
        elif response.status_code == 403:
            raise Exception("Access denied. The repository may be private.")
        elif response.status_code != 200:
            raise Exception(
                f"GitHub API error {response.status_code}: {response.text}"
            )

        data = response.json()
        
        # Check if repo is archived
        if data.get("archived"):
            print(f"⚠️  Warning: Repository {owner}/{repo} is archived.")
        
        # Check if repo is private (should be caught by 403 above, but double check)
        if data.get("private"):
            raise Exception("Cannot analyze private repositories. GitCheck supports public repos only.")
        
        # Check if repository is empty
        is_empty = data.get("size") == 0

        return {
            "full_name": data["full_name"],
            "stars": data["stargazers_count"],
            "forks": data["forks_count"],
            "open_issues": data["open_issues_count"],
            "watchers": data["watchers_count"],
            "archived": data.get("archived", False),
            "is_empty": is_empty,
            "commits_last_90_days": 0 if is_empty else get_commit_activity(owner, repo),
            "issue_close_rate": 0 if is_empty else get_issue_close_rate(owner, repo),
            "contributors": 0 if is_empty else get_contributor_count(owner, repo)
        }
        
    except requests.Timeout:
        raise Exception(f"Request timeout while fetching repository data for {owner}/{repo}")
    except requests.RequestException as e:
        raise Exception(f"Network error while fetching repository: {str(e)}")
