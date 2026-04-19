import pytest

from app.core.cache import TTLCache
from app.services.documentation_generator import DocumentationGenerator


class FakeAnalyzer:
    async def analyze(self, owner: str, repo: str) -> dict:
        return {
            "overview": {
                "name": repo,
                "owner": owner,
                "description": "Example repository",
                "stars": 10,
                "forks": 2,
                "last_updated": "2026-04-14T12:00:00Z",
                "url": f"https://github.com/{owner}/{repo}",
                "default_branch": "main",
            },
            "insights": {
                "primary_language": "Python",
                "languages": [{"name": "Python", "percentage": 80.0}],
                "license_name": "MIT",
                "has_license": True,
                "dependency_files": ["requirements.txt"],
            },
            "activity": {
                "recent_commits_last_7_days": 2,
                "recent_commits_last_30_days": 4,
                "last_commit_date": "2026-04-14T12:00:00Z",
                "total_contributors": 3,
                "active_contributors_last_30_days": 2,
            },
            "structure": {
                "total_files": 12,
                "has_readme": True,
                "has_license": True,
                "top_directories": ["src", "tests"],
            },
        }


class FakeGitHubClient:
    async def get_readme(self, owner: str, repo: str) -> str | None:
        return "# Demo\n\nThis repository demonstrates the docs generator."


class FakeLLMClient:
    async def generate_json(self, system_prompt: str, user_prompt: str, max_tokens: int = 512) -> str:
        if "structured repository documentation insights" in system_prompt:
            return '{"recommendations": ["Improve installation docs"], "risk_observations": ["Low contributor diversity"]}'
        return "This repository demonstrates the docs generator."


class FakeEmbeddingClient:
    async def create_embedding(self, text: str) -> list[float]:
        return [float(len(text) % 7 + 1), float(len(text) % 5 + 1), 1.0]


@pytest.mark.asyncio
async def test_documentation_generator_builds_report() -> None:
    generator = DocumentationGenerator(
        client=FakeGitHubClient(),
        analyzer=FakeAnalyzer(),
        llm_client=FakeLLMClient(),
        embedding_client=FakeEmbeddingClient(),
        cache=TTLCache(ttl_seconds=60),
    )

    result = await generator.generate("owner", "repo")

    assert result["overview"]["name"] == "repo"
    assert result["readme_summary"] is not None
    assert result["sections"][0]["title"] == "Repository Overview"
    assert "# repo Documentation Report" in result["markdown"]
    assert "Recommendations" in result["markdown"]