from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    github_token: str | None = os.getenv("GITHUB_TOKEN") or None
    github_timeout_seconds: float = float(os.getenv("GITHUB_TIMEOUT_SECONDS", "15"))
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "1800"))
    github_user_agent: str = os.getenv("GITHUB_USER_AGENT", "AutoDocResearchTool/1.0")
    github_api_base_url: str = os.getenv("GITHUB_API_BASE_URL", "https://api.github.com")
    local_llm_base_url: str = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:8001/v1")
    local_embedding_base_url: str = os.getenv("LOCAL_EMBEDDING_BASE_URL", "http://localhost:8002/v1")
    local_llm_model: str = os.getenv("LOCAL_LLM_MODEL", "Qwen/Qwen3.5-4B")
    local_embedding_model: str = os.getenv("LOCAL_EMBEDDING_MODEL", "BAAI/bge-m3")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "not_used")


settings = Settings()
