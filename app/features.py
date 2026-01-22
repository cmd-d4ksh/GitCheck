def normalize(value, max_value):
    if max_value == 0:
        return 0
    return min(value / max_value, 1.0)


def extract_features(repo_data: dict):
    commit_score = normalize(repo_data["commits_last_90_days"], 100)
    contributor_score = normalize(repo_data["contributors"], 30)
    issue_score = repo_data["issue_close_rate"]

    return {
        "commit_score": round(commit_score, 2),
        "contributor_score": round(contributor_score, 2),
        "issue_score": round(issue_score, 2)
    }
