from datetime import datetime, timezone

import pytest

from app.core.cache import TTLCache
from app.services.repo_analyzer import RepoAnalyzer


class FakeGitHubClient:
    async def get_repository(self, owner: str, repo: str) -> dict:
        return {
            "name": repo,
            "owner": {"login": owner},
            "description": "Example repository",
            "stargazers_count": 10,
            "forks_count": 2,
            "updated_at": "2026-04-14T12:00:00Z",
            "html_url": f"https://github.com/{owner}/{repo}",
            "default_branch": "main",
            "license": {"spdx_id": "MIT"},
        }

    async def get_languages(self, owner: str, repo: str) -> dict[str, int]:
        return {"Python": 80, "TypeScript": 20}

    async def get_commits(self, owner: str, repo: str, per_page: int = 100) -> list[dict]:
        return [
            {"commit": {"author": {"date": "2026-04-14T10:00:00Z", "name": "A"}}},
            {"commit": {"author": {"date": "2026-04-10T10:00:00Z", "name": "B"}}},
        ]

    async def get_contributors(self, owner: str, repo: str, per_page: int = 10) -> list[dict]:
        return [{"login": "a"}, {"login": "b"}]

    async def get_repo_tree(self, owner: str, repo: str, branch: str) -> list[dict]:
        return [
            {"path": "README.md", "type": "blob"},
            {"path": "src/app.py", "type": "blob"},
            {"path": "tests/test_app.py", "type": "blob"},
            {"path": "package.json", "type": "blob"},
            {"path": "src", "type": "tree"},
            {"path": "tests", "type": "tree"},
        ]


@pytest.mark.asyncio
async def test_repo_analyzer_returns_report() -> None:
    analyzer = RepoAnalyzer(client=FakeGitHubClient(), cache=TTLCache(ttl_seconds=60))
    result = await analyzer.analyze("owner", "repo")

    assert result["overview"]["name"] == "repo"
    assert result["insights"]["primary_language"] == "Python"
    assert result["structure"]["has_readme"] is True
    assert result["activity"]["recent_commits_last_30_days"] == 2


@pytest.mark.asyncio
async def test_repo_analyzer_caches_results() -> None:
    analyzer = RepoAnalyzer(client=FakeGitHubClient(), cache=TTLCache(ttl_seconds=60))
    first = await analyzer.analyze("owner", "repo")
    second = await analyzer.analyze("owner", "repo")
    assert first == second
