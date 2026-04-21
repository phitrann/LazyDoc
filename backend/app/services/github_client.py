from __future__ import annotations

import base64
from datetime import datetime, timezone

import httpx

from app.schemas.error import APIError


def github_cache_scope(github_token: str | None) -> str:
    return "authenticated" if github_token else "anonymous"


class GitHubClient:
    def __init__(self, token: str | None, timeout_seconds: float, base_url: str, user_agent: str) -> None:
        self._token = token
        self._timeout = timeout_seconds
        self._base_url = base_url.rstrip("/")
        self._headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": user_agent,
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            self._headers["Authorization"] = f"Bearer {token}"
        self.last_rate_limit: dict = {}

    def set_token(self, token: str | None) -> None:
        """Set the default GitHub token used when no per-request PAT is provided."""
        self._token = token

    def _headers_for_token(self, github_token: str | None = None) -> dict[str, str]:
        headers = dict(self._headers)
        token = github_token if github_token is not None else self._token
        if token:
            headers["Authorization"] = f"Bearer {token}"
        else:
            headers.pop("Authorization", None)
        return headers

    async def _request(self, path: str, params: dict[str, str] | None = None, github_token: str | None = None) -> dict:
        async with httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
            headers=self._headers_for_token(github_token),
        ) as client:
            try:
                response = await client.get(path, params=params)
            except httpx.TimeoutException as exc:
                raise APIError("GITHUB_TIMEOUT", "GitHub request timed out.", 504) from exc
            except httpx.RequestError as exc:
                raise APIError("GITHUB_UNAVAILABLE", "GitHub request failed.", 502) from exc
        
        self._extract_rate_limit(response)
        
        if response.status_code == 404:
            raise APIError("REPOSITORY_NOT_FOUND", "Repository not found.", 404)
        if response.status_code == 403:
            retry_after = self._retry_after_seconds(response)
            if retry_after is not None or "rate limit" in response.text.lower():
                raise APIError(
                    "RATE_LIMIT_EXCEEDED",
                    "GitHub API rate limit exceeded.",
                    403,
                    retry_after_seconds=retry_after,
                )
            raise APIError("GITHUB_FORBIDDEN", "GitHub access was forbidden.", 403)
        if response.is_error:
            raise APIError("GITHUB_ERROR", "GitHub API request failed.", 502)
        return response.json()

    def _extract_rate_limit(self, response: httpx.Response) -> None:
        """Extract and store rate-limit info from response headers."""
        remaining = response.headers.get("x-ratelimit-remaining")
        limit = response.headers.get("x-ratelimit-limit")
        reset = response.headers.get("x-ratelimit-reset")
        
        if remaining and limit and reset and all(s.isdigit() for s in [remaining, limit, reset]):
            reset_unix = int(reset)
            reset_seconds = max(int(reset_unix) - int(datetime.now(tz=timezone.utc).timestamp()), 0)
            self.last_rate_limit = {
                "remaining": int(remaining),
                "limit": int(limit),
                "reset_unix_timestamp": reset_unix,
                "reset_in_seconds": reset_seconds,
            }

    def get_rate_limit(self) -> dict | None:
        """Return last observed rate-limit info, or None if never seen."""
        return self.last_rate_limit if self.last_rate_limit else None

    def _retry_after_seconds(self, response: httpx.Response) -> int | None:
        retry_after = response.headers.get("retry-after")
        if retry_after and retry_after.isdigit():
            return int(retry_after)
        reset = response.headers.get("x-ratelimit-reset")
        if reset and reset.isdigit():
            reset_dt = datetime.fromtimestamp(int(reset), tz=timezone.utc)
            seconds = int((reset_dt - datetime.now(tz=timezone.utc)).total_seconds())
            return max(seconds, 0)
        return None

    async def get_repository(self, owner: str, repo: str, github_token: str | None = None) -> dict:
        return await self._request(f"/repos/{owner}/{repo}", github_token=github_token)

    async def get_languages(self, owner: str, repo: str, github_token: str | None = None) -> dict[str, int]:
        return await self._request(f"/repos/{owner}/{repo}/languages", github_token=github_token)

    async def get_commits(self, owner: str, repo: str, per_page: int = 100, github_token: str | None = None) -> list[dict]:
        data = await self._request(f"/repos/{owner}/{repo}/commits", params={"per_page": str(per_page)}, github_token=github_token)
        return list(data)

    async def get_contributors(self, owner: str, repo: str, per_page: int = 10, github_token: str | None = None) -> list[dict]:
        data = await self._request(f"/repos/{owner}/{repo}/contributors", params={"per_page": str(per_page)}, github_token=github_token)
        return list(data)

    async def get_repo_tree(self, owner: str, repo: str, branch: str, github_token: str | None = None) -> list[dict]:
        data = await self._request(
            f"/repos/{owner}/{repo}/git/trees/{branch}",
            params={"recursive": "1"},
            github_token=github_token,
        )
        return list(data.get("tree", []))

    async def get_readme(self, owner: str, repo: str, github_token: str | None = None) -> str | None:
        data = await self._request(f"/repos/{owner}/{repo}/readme", github_token=github_token)
        content = data.get("content")
        if not content:
            return None
        if data.get("encoding") == "base64":
            return base64.b64decode(content.replace("\n", "")).decode("utf-8", errors="replace")
        return str(content)

    async def get_file_contents(self, owner: str, repo: str, path: str, github_token: str | None = None) -> str:
        data = await self._request(f"/repos/{owner}/{repo}/contents/{path}", github_token=github_token)
        content = data.get("content")
        if not content:
            return ""
        if data.get("encoding") == "base64":
            return base64.b64decode(content.replace("\n", "")).decode("utf-8", errors="replace")
        return str(content)
