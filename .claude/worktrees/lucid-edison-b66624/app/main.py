"""GitCheck API — FastAPI entrypoint."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.features import extract_features
from app.github_api import GitHubError, check_rate_limit, get_repo_metadata, parse_repo_url
from app.trust_score import (
    calculate_trust_score,
    category_summary,
    recommend,
    summarize_highlights,
    summarize_risks,
)

app = FastAPI(
    title="GitCheck",
    description="Reliability scoring for open-source GitHub repositories.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "web" / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class AnalyzeRequest(BaseModel):
    repo_url: str = Field(
        ...,
        description="GitHub repo URL or owner/repo shorthand",
        examples=["https://github.com/fastapi/fastapi"],
    )


class CompareRequest(BaseModel):
    repo_urls: list[str] = Field(..., min_length=1, max_length=5)


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/rate-limit")
def rate_limit() -> dict[str, Any]:
    remaining, reset = check_rate_limit()
    if remaining is None:
        raise HTTPException(status_code=502, detail="Unable to reach GitHub rate-limit API.")
    status = "healthy" if remaining > 100 else "warning" if remaining > 10 else "critical"
    return {"remaining": remaining, "reset_at": reset, "status": status}


def _build_report(repo_url: str) -> dict[str, Any]:
    repo_data = get_repo_metadata(repo_url)
    features = extract_features(repo_data)
    scoring = calculate_trust_score(features, repo_data)

    warnings: list[str] = []
    if repo_data.get("archived"):
        warnings.append("Repository is archived.")
    if repo_data.get("is_empty"):
        warnings.append("Repository is empty.")
    if repo_data.get("disabled"):
        warnings.append("Repository is disabled.")

    return {
        "repository": repo_data["full_name"],
        "url": repo_data.get("html_url"),
        "description": repo_data.get("description"),
        "language": repo_data.get("language"),
        "topics": repo_data.get("topics", []),
        "license": repo_data.get("license"),
        "default_branch": repo_data.get("default_branch"),
        "latest_release": repo_data.get("latest_release"),
        "metadata": {
            "stars": repo_data["stars"],
            "forks": repo_data["forks"],
            "watchers": repo_data["watchers"],
            "open_issues": repo_data["open_issues"],
            "contributors": repo_data["contributors"],
            "archived": repo_data.get("archived", False),
            "disabled": repo_data.get("disabled", False),
            "created_at": repo_data.get("created_at"),
            "updated_at": repo_data.get("updated_at"),
            "pushed_at": repo_data.get("pushed_at"),
            "days_since_push": repo_data.get("days_since_push"),
            "age_days": repo_data.get("age_days"),
        },
        "activity": {
            "commits_last_90_days": repo_data.get("commits_last_90_days"),
            "weekly_commits": repo_data.get("weekly_commits"),
            "issue_close_rate": repo_data.get("issue_close_rate"),
            "pr_merge_rate": repo_data.get("pr_merge_rate"),
            "issues": repo_data.get("issues"),
            "pull_requests": repo_data.get("pull_requests"),
            "release_count": repo_data.get("release_count"),
        },
        "top_contributors": repo_data.get("top_contributors", []),
        "features": features,
        "score": scoring["score"],
        "risk_level": scoring["risk_level"],
        "status": scoring["status"],
        "breakdown": scoring["breakdown"],
        "penalties": scoring["penalties"],
        "categories": category_summary(scoring["breakdown"]),
        "highlights": summarize_highlights(features, repo_data),
        "risks": summarize_risks(features, repo_data),
        "recommendation": recommend(scoring["score"], scoring["status"], scoring["risk_level"]),
        "warnings": warnings,
    }


def _error_response(exc: Exception) -> HTTPException:
    if isinstance(exc, GitHubError):
        return HTTPException(status_code=exc.status, detail=str(exc))
    return HTTPException(status_code=500, detail=f"Unexpected error: {exc}")


@app.post("/api/analyze")
def analyze_json(body: AnalyzeRequest) -> dict[str, Any]:
    try:
        parse_repo_url(body.repo_url)
        return _build_report(body.repo_url)
    except HTTPException:
        raise
    except Exception as exc:
        raise _error_response(exc) from exc


@app.get("/api/analyze")
def analyze_get(
    repo_url: str = Query(..., description="GitHub URL or owner/repo shorthand"),
) -> dict[str, Any]:
    try:
        parse_repo_url(repo_url)
        return _build_report(repo_url)
    except HTTPException:
        raise
    except Exception as exc:
        raise _error_response(exc) from exc


@app.post("/api/compare")
def compare(body: CompareRequest) -> dict[str, Any]:
    reports: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    seen: set[str] = set()
    for url in body.repo_urls:
        if url in seen:
            continue
        seen.add(url)
        try:
            reports.append(_build_report(url))
        except GitHubError as exc:
            errors.append({"repo_url": url, "error": str(exc), "status": str(exc.status)})
        except Exception as exc:
            errors.append({"repo_url": url, "error": str(exc), "status": "500"})

    reports.sort(key=lambda item: item["score"], reverse=True)
    return {"results": reports, "errors": errors}


@app.exception_handler(GitHubError)
def github_error_handler(_request, exc: GitHubError):
    return JSONResponse(status_code=exc.status, content={"detail": str(exc)})
