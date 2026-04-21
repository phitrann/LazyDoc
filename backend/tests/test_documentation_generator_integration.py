"""
Integration tests for DocumentationGenerator using real LLM and embedding clients.

These tests require:
- LOCAL_LLM_BASE_URL pointing to a running LLM server (e.g., Ollama)
- LOCAL_EMBEDDING_BASE_URL pointing to a running embedding server (e.g., Ollama)
- GITHUB_TOKEN for accessing GitHub API

Run with:
  INTEGRATION_TESTS=1 pytest backend/tests/test_documentation_generator_integration.py -v
"""

import asyncio
import os

from app.core.cache import TTLCache
from app.core.config import settings
from app.services.documentation_generator import DocumentationGenerator
from app.services.github_client import GitHubClient
from app.services.local_models import LocalLLMClient, LocalEmbeddingClient
from app.services.repo_analyzer import RepoAnalyzer


def should_run_integration_tests() -> bool:
    """Check if integration tests should run."""
    return os.getenv("INTEGRATION_TESTS", "").lower() in ("1", "true", "yes")


def skip_if_no_integration_tests():
    """Skip test if integration tests are not enabled."""
    if not should_run_integration_tests():
        import pytest
        pytest.skip("Integration tests disabled. Set INTEGRATION_TESTS=1 to enable.")


def test_documentation_generator_with_real_llm_generates_content() -> None:
    """Test that documentation generation works with real LLM and embedding clients."""
    skip_if_no_integration_tests()

    llm_client = LocalLLMClient(
        base_url=settings.local_llm_base_url,
        api_key=settings.openai_api_key,
        model=settings.local_llm_model,
    )
    embedding_client = LocalEmbeddingClient(
        base_url=settings.local_embedding_base_url,
        api_key=settings.openai_api_key,
        model=settings.local_embedding_model,
    )
    github_client = GitHubClient(
        token=settings.github_token,
        timeout_seconds=settings.github_timeout_seconds,
        base_url=settings.github_api_base_url,
        user_agent=settings.github_user_agent,
    )
    analyzer = RepoAnalyzer(client=github_client, cache=TTLCache(ttl_seconds=60))
    generator = DocumentationGenerator(
        client=github_client,
        analyzer=analyzer,
        llm_client=llm_client,
        embedding_client=embedding_client,
        cache=TTLCache(ttl_seconds=60),
    )

    events_received: list[str] = []

    async def run_test() -> None:
        async for event in generator.stream_ai_section("phitrann", "LazyDoc", force_refresh=True):
            event_type = event.get("event", "unknown")
            events_received.append(event_type)

    asyncio.run(run_test())

    # Verify stream path works correctly
    assert "stage" in events_received, "Should emit stage events"
    assert "ai_update" in events_received, "Should emit AI update events"
    assert "complete" in events_received, "Should emit complete event"
    
    # Token events may or may not be emitted depending on LLM server batching
    # The important thing is that the content is generated


def test_documentation_generator_with_real_clients_generates_full_report() -> None:
    """Test full report generation with real GitHub and LLM clients."""
    skip_if_no_integration_tests()

    llm_client = LocalLLMClient(
        base_url=settings.local_llm_base_url,
        api_key=settings.openai_api_key,
        model=settings.local_llm_model,
    )
    embedding_client = LocalEmbeddingClient(
        base_url=settings.local_embedding_base_url,
        api_key=settings.openai_api_key,
        model=settings.local_embedding_model,
    )
    github_client = GitHubClient(
        token=settings.github_token,
        timeout_seconds=settings.github_timeout_seconds,
        base_url=settings.github_api_base_url,
        user_agent=settings.github_user_agent,
    )
    analyzer = RepoAnalyzer(client=github_client, cache=TTLCache(ttl_seconds=60))
    generator = DocumentationGenerator(
        client=github_client,
        analyzer=analyzer,
        llm_client=llm_client,
        embedding_client=embedding_client,
        cache=TTLCache(ttl_seconds=60),
    )

    result = asyncio.run(generator.generate("phitrann", "LazyDoc", force_refresh=True))

    assert result["overview"]["name"] == "LazyDoc"
    assert result["overview"]["owner"] == "phitrann"
    assert result["readme_summary"] is not None
    assert len(result["readme_summary"]) > 10, "README summary should be substantive"
    assert len(result["recommendations"]) > 0, "Should have recommendations"
    assert len(result["risk_observations"]) > 0, "Should have risk observations"
    assert len(result["sections"]) > 0, "Should have generated sections"
    assert len(result["markdown"]) > 50, "Should have meaningful markdown"


def test_documentation_generator_readme_context_selection_with_real_embedding() -> None:
    """Test that README context selection works with real embedding client."""
    skip_if_no_integration_tests()

    embedding_client = LocalEmbeddingClient(
        base_url=settings.local_embedding_base_url,
        api_key=settings.openai_api_key,
        model=settings.local_embedding_model,
    )

    # Create a minimal generator just to test _select_readme_context
    generator = DocumentationGenerator(
        client=None,  # type: ignore
        analyzer=None,  # type: ignore
        llm_client=None,  # type: ignore
        embedding_client=embedding_client,
        cache=TTLCache(ttl_seconds=60),
    )

    long_readme = "\n".join([f"Section {i}: Lorem ipsum dolor sit amet, consectetur adipiscing elit." for i in range(50)])
    analysis = {
        "overview": {"owner": "test", "name": "test-repo"},
    }

    context = asyncio.run(generator._select_readme_context(long_readme, analysis))

    assert len(context) > 0, "Should select some README context"
    assert len(context) < len(long_readme), "Should select subset of README"
    assert context.count("\n") > 3, "Should select multiple paragraphs"
