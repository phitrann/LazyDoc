import asyncio
import json

import pytest

from app.core.cache import TTLCache
from app.schemas.error import APIError
from app.services.documentation_generator import DocumentationGenerator


class FakeAnalyzer:
    async def analyze(self, owner: str, repo: str, github_token: str | None = None) -> dict:
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


class NoneAnalyzer:
    async def analyze(self, owner: str, repo: str, github_token: str | None = None) -> dict | None:
        return None


class FakeGitHubClient:
    async def get_readme(self, owner: str, repo: str, github_token: str | None = None) -> str | None:
        return "# Demo\n\nThis repository demonstrates the docs generator."


class CountingAnalyzer(FakeAnalyzer):
    def __init__(self) -> None:
        self.calls = 0
        self.star_count = 10

    async def analyze(self, owner: str, repo: str, github_token: str | None = None) -> dict:
        self.calls += 1
        data = await super().analyze(owner, repo, github_token=github_token)
        data["overview"]["stars"] = self.star_count
        return data


class CountingGitHubClient(FakeGitHubClient):
    def __init__(self) -> None:
        self.calls = 0

    async def get_readme(self, owner: str, repo: str, github_token: str | None = None) -> str | None:
        self.calls += 1
        return await super().get_readme(owner, repo, github_token=github_token)


class FakeLLMClient:
    async def generate_json(self, system_prompt: str, user_prompt: str, max_tokens: int = 512) -> str:
        if "structured repository documentation insights" in system_prompt:
            return '{"recommendations": ["Improve installation docs"], "risk_observations": ["Low contributor diversity"]}'
        return "This repository demonstrates the docs generator."


class FailingLLMClient:
    async def generate_json(self, system_prompt: str, user_prompt: str, max_tokens: int = 512) -> str:
        raise RuntimeError("Connection error.")

    async def stream_text(self, system_prompt: str, user_prompt: str, max_tokens: int = 512):
        if False:
            yield ""


class MutableLLMClient:
    def __init__(self) -> None:
        self.readme_summary = "Initial README summary."
        self.recommendations = ["Initial recommendation."]
        self.risk_observations = ["Initial risk."]

    async def generate_json(self, system_prompt: str, user_prompt: str, max_tokens: int = 512) -> str:
        if "structured repository documentation insights" in system_prompt:
            return json.dumps(
                {
                    "recommendations": self.recommendations,
                    "risk_observations": self.risk_observations,
                }
            )
        if "structured repository documentation recommendations" in system_prompt:
            return json.dumps({"recommendations": self.recommendations})
        if "structured repository documentation security and risk observations" in system_prompt:
            return json.dumps({"risk_observations": self.risk_observations})
        return self.readme_summary

    async def stream_text(self, system_prompt: str, user_prompt: str, max_tokens: int = 512):
        yield self.readme_summary


class DuplicateWarningAnalyzer(FakeAnalyzer):
    async def analyze(self, owner: str, repo: str, github_token: str | None = None) -> dict:
        data = await super().analyze(owner, repo, github_token=github_token)
        data["warnings"] = ["GitHub API rate limit exceeded.", "GitHub API rate limit exceeded."]
        return data


class FakeEmbeddingClient:
    async def create_embedding(self, text: str) -> list[float]:
        return [float(len(text) % 7 + 1), float(len(text) % 5 + 1), 1.0]


def test_documentation_generator_builds_report() -> None:
    generator = DocumentationGenerator(
        client=FakeGitHubClient(),
        analyzer=FakeAnalyzer(),
        llm_client=FakeLLMClient(),
        embedding_client=FakeEmbeddingClient(),
        cache=TTLCache(ttl_seconds=60),
    )

    result = asyncio.run(generator.generate("owner", "repo"))

    assert result["overview"]["name"] == "repo"
    assert result["readme_summary"] is not None
    assert result["sections"][0]["title"] == "Repository Overview"
    assert "# repo Documentation Report" in result["markdown"]
    assert "Recommendations" in result["markdown"]
    assert result["markdown"].count("## README Summary") == 1
    assert "- This repository demonstrates the docs generator." not in result["markdown"]
    assert result["markdown"].count("## Recommendations") == 1
    assert result["markdown"].count("## Security & Risk Observations") == 1


def test_documentation_generator_uses_clean_fallback_warnings_for_model_connection_errors() -> None:
    generator = DocumentationGenerator(
        client=FakeGitHubClient(),
        analyzer=FakeAnalyzer(),
        llm_client=FailingLLMClient(),
        embedding_client=FakeEmbeddingClient(),
        cache=TTLCache(ttl_seconds=60),
    )

    result = asyncio.run(generator.generate("owner", "repo"))

    warnings = result["warnings"]
    assert "README summary model fallback: connection unavailable. Used deterministic fallback." in warnings
    assert "Insight generation fallback: connection unavailable. Used deterministic fallback." in warnings


def test_documentation_generator_rejects_missing_analysis() -> None:
    generator = DocumentationGenerator(
        client=FakeGitHubClient(),
        analyzer=NoneAnalyzer(),
        llm_client=FakeLLMClient(),
        embedding_client=FakeEmbeddingClient(),
        cache=TTLCache(ttl_seconds=60),
    )

    with pytest.raises(APIError) as exc_info:
        asyncio.run(generator.generate("owner", "repo"))

    assert exc_info.value.error_code == "UPSTREAM_UNAVAILABLE"


def test_documentation_generator_dedupes_repeated_warnings() -> None:
    generator = DocumentationGenerator(
        client=FakeGitHubClient(),
        analyzer=DuplicateWarningAnalyzer(),
        llm_client=FailingLLMClient(),
        embedding_client=FakeEmbeddingClient(),
        cache=TTLCache(ttl_seconds=60),
    )

    result = asyncio.run(generator.generate("owner", "repo"))

    assert result["warnings"].count("GitHub API rate limit exceeded.") == 1


def test_documentation_generator_can_regenerate_single_ai_section() -> None:
    llm_client = MutableLLMClient()
    generator = DocumentationGenerator(
        client=FakeGitHubClient(),
        analyzer=FakeAnalyzer(),
        llm_client=llm_client,
        embedding_client=FakeEmbeddingClient(),
        cache=TTLCache(ttl_seconds=60),
    )

    initial = asyncio.run(generator.generate("owner", "repo"))
    llm_client.recommendations = ["Updated recommendation."]

    updated = asyncio.run(generator.generate("owner", "repo", ai_section="recommendations"))

    assert updated["readme_summary"] == initial["readme_summary"]
    assert updated["recommendations"] == ["Updated recommendation."]
    assert updated["risk_observations"] == initial["risk_observations"]


def test_documentation_generator_force_refreshes_base_report_for_single_ai_section() -> None:
    llm_client = MutableLLMClient()
    analyzer = CountingAnalyzer()
    client = CountingGitHubClient()
    generator = DocumentationGenerator(
        client=client,
        analyzer=analyzer,
        llm_client=llm_client,
        embedding_client=FakeEmbeddingClient(),
        cache=TTLCache(ttl_seconds=60),
    )

    initial = asyncio.run(generator.generate("owner", "repo"))
    analyzer.star_count = 42
    llm_client.recommendations = ["Updated recommendation."]

    updated = asyncio.run(generator.generate("owner", "repo", force_refresh=True, ai_section="recommendations"))

    assert initial["overview"]["stars"] == 10
    assert updated["overview"]["stars"] == 42
    assert updated["recommendations"] == ["Updated recommendation."]
    assert analyzer.calls == 2
    assert client.calls == 2
