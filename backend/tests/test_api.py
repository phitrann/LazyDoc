from fastapi.testclient import TestClient

from app.core.dependencies import get_analyzer
from app.main import app
from app.schemas.error import APIError


class FakeAnalyzer:
    def __init__(self, mode: str = "success") -> None:
        self.mode = mode

    async def analyze(self, owner: str, repo: str) -> dict:
        if self.mode == "error":
            raise APIError("RATE_LIMIT_EXCEEDED", "GitHub API rate limit exceeded.", 403, retry_after_seconds=120)
        return {
            "overview": {
                "name": repo,
                "owner": owner,
                "description": "Example",
                "stars": 1,
                "forks": 0,
                "last_updated": "2026-04-14T12:00:00Z",
                "url": f"https://github.com/{owner}/{repo}",
                "default_branch": "main",
            },
            "insights": {
                "primary_language": "Python",
                "languages": [],
                "license_name": None,
                "has_license": False,
                "dependency_files": [],
            },
            "activity": {
                "recent_commits_last_7_days": 1,
                "recent_commits_last_30_days": 1,
                "last_commit_date": "2026-04-14T12:00:00Z",
                "total_contributors": 1,
                "active_contributors_last_30_days": 1,
            },
            "structure": {
                "total_files": 1,
                "has_readme": True,
                "has_license": False,
                "top_directories": ["src"],
            },
        }


client = TestClient(app)


def test_research_endpoint_success() -> None:
    app.dependency_overrides[get_analyzer] = lambda: FakeAnalyzer("success")
    response = client.post("/api/research", json={"repository_url": "https://github.com/owner/repo"})
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["data"]["overview"]["name"] == "repo"


def test_research_endpoint_invalid_url() -> None:
    app.dependency_overrides[get_analyzer] = lambda: FakeAnalyzer("success")
    response = client.post("/api/research", json={"repository_url": "https://example.com/owner/repo"})
    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_URL"


def test_research_endpoint_rate_limited() -> None:
    app.dependency_overrides[get_analyzer] = lambda: FakeAnalyzer("error")
    response = client.post("/api/research", json={"repository_url": "https://github.com/owner/repo"})
    app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error_code"] == "RATE_LIMIT_EXCEEDED"
    assert response.json()["retry_after_seconds"] == 120
