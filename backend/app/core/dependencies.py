from app.core.cache import TTLCache
from app.core.config import settings
from app.services.github_client import GitHubClient
from app.services.documentation_generator import DocumentationGenerator
from app.services.repo_analyzer import RepoAnalyzer
from app.services.local_models import LocalEmbeddingClient, LocalLLMClient

_cache = TTLCache[dict](ttl_seconds=settings.cache_ttl_seconds)
_analyzer: RepoAnalyzer | None = None
_documentation_generator: DocumentationGenerator | None = None
_llm_client: LocalLLMClient | None = None
_embedding_client: LocalEmbeddingClient | None = None


def get_analyzer() -> RepoAnalyzer:
    global _analyzer
    if _analyzer is None:
        client = GitHubClient(
            token=settings.github_token,
            timeout_seconds=settings.github_timeout_seconds,
            base_url=settings.github_api_base_url,
            user_agent=settings.github_user_agent,
        )
        _analyzer = RepoAnalyzer(client=client, cache=_cache)
    return _analyzer


def get_documentation_generator() -> DocumentationGenerator:
    global _documentation_generator
    if _documentation_generator is None:
        client = GitHubClient(
            token=settings.github_token,
            timeout_seconds=settings.github_timeout_seconds,
            base_url=settings.github_api_base_url,
            user_agent=settings.github_user_agent,
        )
        _documentation_generator = DocumentationGenerator(
            client=client,
            analyzer=get_analyzer(),
            llm_client=get_llm_client(),
            embedding_client=get_embedding_client(),
            cache=_cache,
        )
    return _documentation_generator


def get_llm_client() -> LocalLLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LocalLLMClient(
            base_url=settings.local_llm_base_url,
            api_key=settings.openai_api_key,
            model=settings.local_llm_model,
        )
    return _llm_client


def get_embedding_client() -> LocalEmbeddingClient:
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = LocalEmbeddingClient(
            base_url=settings.local_embedding_base_url,
            api_key=settings.openai_api_key,
            model=settings.local_embedding_model,
        )
    return _embedding_client
