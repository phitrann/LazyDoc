from fastapi.testclient import TestClient

from app.core.dependencies import get_documentation_generator
from app.core.dependencies import get_analyzer
from app.main import app
from app.schemas.error import APIError


class MockGitHubClient:
    """Mock GitHub client with rate_limit tracking."""
    def get_rate_limit(self):
        return {
            "remaining": 5000,
            "limit": 5000,
            "reset_unix_timestamp": 1713699600,
            "reset_in_seconds": 900,
        }


class FakeAnalyzer:
    def __init__(self, mode: str = "success") -> None:
        self.mode = mode
        self._client = MockGitHubClient()

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


class FakeDocumentationGenerator:
    def __init__(self, mode: str = "success") -> None:
        self.mode = mode
        self.last_force_refresh = False
        self._client = MockGitHubClient()

    async def generate(self, owner: str, repo: str, force_refresh: bool = False) -> dict:
        self.last_force_refresh = force_refresh
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
            "sections": [
                {
                    "title": "Repository Overview",
                    "summary": "Summary",
                    "content": ["A", "B"],
                }
            ],
            "markdown": "# Example",
            "readme_summary": "README summary",
            "recommendations": ["Improve docs"],
            "risk_observations": ["Low bus factor"],
        }

    async def stream_ai_section(self, owner: str, repo: str, force_refresh: bool = False):
        self.last_force_refresh = force_refresh
        if self.mode == "error":
            raise APIError("RATE_LIMIT_EXCEEDED", "GitHub API rate limit exceeded.", 403, retry_after_seconds=120)
        yield {
            "event": "stage",
            "stage": "analysis_complete",
            "message": "Repository analysis complete.",
        }
        yield {
            "event": "ai_update",
            "data": {
                "readme_summary": "README summary",
            },
        }
        yield {
            "event": "token",
            "field": "readme_summary",
            "token": "README ",
        }
        yield {
            "event": "token",
            "field": "readme_summary",
            "token": "summary",
        }
        yield {
            "event": "complete",
            "data": {
                "readme_summary": "README summary",
                "recommendations": ["Improve docs"],
                "risk_observations": ["Low bus factor"],
                "sections": [
                    {
                        "title": "Repository Overview",
                        "summary": "Summary",
                        "content": ["A", "B"],
                    }
                ],
                "markdown": "# Example",
                "warnings": [],
            },
            "cached": False,
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


def test_documentation_endpoint_success() -> None:
    app.dependency_overrides[get_documentation_generator] = lambda: FakeDocumentationGenerator("success")
    response = client.post("/api/documentation", json={"repository_url": "https://github.com/owner/repo"})
    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["markdown"] == "# Example"
    assert payload["data"]["sections"][0]["title"] == "Repository Overview"


def test_documentation_endpoint_invalid_url() -> None:
    app.dependency_overrides[get_documentation_generator] = lambda: FakeDocumentationGenerator("success")
    response = client.post("/api/documentation", json={"repository_url": "https://example.com/owner/repo"})
    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_URL"


def test_documentation_endpoint_rate_limited() -> None:
    app.dependency_overrides[get_documentation_generator] = lambda: FakeDocumentationGenerator("error")
    response = client.post("/api/documentation", json={"repository_url": "https://github.com/owner/repo"})
    app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error_code"] == "RATE_LIMIT_EXCEEDED"
    assert response.json()["retry_after_seconds"] == 120


def test_documentation_endpoint_force_regenerate() -> None:
    fake = FakeDocumentationGenerator("success")
    app.dependency_overrides[get_documentation_generator] = lambda: fake
    response = client.post(
        "/api/documentation",
        json={"repository_url": "https://github.com/owner/repo", "force_regenerate": True},
    )
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert fake.last_force_refresh is True


def test_documentation_stream_endpoint_success() -> None:
    app.dependency_overrides[get_documentation_generator] = lambda: FakeDocumentationGenerator("success")
    response = client.post("/api/documentation/stream", json={"repository_url": "https://github.com/owner/repo"})
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert "event: stage" in response.text
    assert "event: ai_update" in response.text
    assert "event: token" in response.text
    assert "event: complete" in response.text
    assert "event: done" in response.text


def test_documentation_stream_endpoint_invalid_url() -> None:
    app.dependency_overrides[get_documentation_generator] = lambda: FakeDocumentationGenerator("success")
    response = client.post("/api/documentation/stream", json={"repository_url": "https://example.com/owner/repo"})
    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_URL"


def test_documentation_stream_endpoint_rate_limited() -> None:
    app.dependency_overrides[get_documentation_generator] = lambda: FakeDocumentationGenerator("error")
    response = client.post("/api/documentation/stream", json={"repository_url": "https://github.com/owner/repo"})
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "event: error" in response.text
    assert "RATE_LIMIT_EXCEEDED" in response.text
