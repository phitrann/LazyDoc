from app.core.cache import TTLCache
from app.core.config import settings
from app.services.github_client import GitHubClient
from app.services.repo_analyzer import RepoAnalyzer

_cache = TTLCache[dict](ttl_seconds=settings.cache_ttl_seconds)
_analyzer: RepoAnalyzer | None = None


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
