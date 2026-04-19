from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone, timedelta

from app.core.cache import TTLCache
from app.schemas.error import APIError
from app.services.github_client import GitHubClient


class RepoAnalyzer:
    def __init__(self, client: GitHubClient, cache: TTLCache[dict]) -> None:
        self._client = client
        self._cache = cache

    async def analyze(self, owner: str, repo: str) -> dict:
        cache_key = f"{owner}/{repo}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        warnings: list[str] = []
        repository = await self._client.get_repository(owner, repo)
        languages = await self._safe_call(warnings, self._client.get_languages(owner, repo), {})
        commits = await self._safe_call(warnings, self._client.get_commits(owner, repo), [])
        contributors = await self._safe_call(warnings, self._client.get_contributors(owner, repo), [])
        tree = await self._safe_call(warnings, self._client.get_repo_tree(owner, repo, repository["default_branch"]), [])

        now = datetime.now(tz=timezone.utc)
        seven_days_ago = now - timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)
        commit_dates = [self._commit_date(commit) for commit in commits if self._commit_date(commit) is not None]
        recent_7 = [commit_date for commit_date in commit_dates if commit_date >= seven_days_ago]
        recent_30 = [commit_date for commit_date in commit_dates if commit_date >= thirty_days_ago]

        language_total = sum(languages.values()) or 0
        language_items = [
            {"name": language, "percentage": round((bytes_count / language_total) * 100, 1) if language_total else 0.0}
            for language, bytes_count in sorted(languages.items(), key=lambda item: item[1], reverse=True)[:5]
        ]
        primary_language = language_items[0]["name"] if language_items else repository.get("language")
        dependency_files = self._dependency_files(tree)
        top_directories = self._top_directories(tree)
        has_readme = any(entry.get("path", "").lower().startswith("readme") for entry in tree)
        has_license = bool(repository.get("license"))

        result = {
            "overview": {
                "name": repository["name"],
                "owner": repository["owner"]["login"],
                "description": repository.get("description"),
                "stars": repository.get("stargazers_count", 0),
                "forks": repository.get("forks_count", 0),
                "last_updated": repository.get("updated_at"),
                "url": repository.get("html_url"),
                "default_branch": repository.get("default_branch", "main"),
            },
            "insights": {
                "primary_language": primary_language,
                "languages": language_items,
                "license_name": repository.get("license", {}).get("spdx_id") if repository.get("license") else None,
                "has_license": has_license,
                "dependency_files": dependency_files,
            },
            "activity": {
                "recent_commits_last_7_days": len(recent_7),
                "recent_commits_last_30_days": len(recent_30),
                "last_commit_date": commit_dates[0].isoformat().replace("+00:00", "Z") if commit_dates else None,
                "total_contributors": len(contributors),
                "active_contributors_last_30_days": self._active_contributors(commits, thirty_days_ago),
            },
            "structure": {
                "total_files": sum(1 for entry in tree if entry.get("type") == "blob"),
                "has_readme": has_readme,
                "has_license": has_license,
                "top_directories": top_directories,
            },
        }
        if warnings:
            result["warnings"] = warnings
        self._cache.set(cache_key, result)
        return result

    async def _safe_call(self, warnings: list[str], coroutine, fallback):
        try:
            return await coroutine
        except APIError as exc:
            warnings.append(exc.message)
            return fallback

    def _commit_date(self, commit: dict) -> datetime | None:
        date_str = (((commit or {}).get("commit") or {}).get("author") or {}).get("date")
        if not date_str:
            return None
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))

    def _active_contributors(self, commits: list[dict], cutoff: datetime) -> int:
        authors = set()
        for commit in commits:
            commit_date = self._commit_date(commit)
            if commit_date is None or commit_date < cutoff:
                continue
            author = ((commit.get("commit") or {}).get("author") or {}).get("name")
            if author:
                authors.add(author)
        return len(authors)

    def _dependency_files(self, tree: list[dict]) -> list[str]:
        names = {entry.get("path") for entry in tree}
        return [
            name
            for name in ["requirements.txt", "pyproject.toml", "package.json", "pnpm-lock.yaml", "poetry.lock", "Cargo.toml", "Gemfile"]
            if name in names
        ]

    def _top_directories(self, tree: list[dict]) -> list[str]:
        counter: Counter[str] = Counter()
        for entry in tree:
            path = entry.get("path", "")
            if "/" not in path:
                continue
            top = path.split("/")[0]
            counter[top] += 1
        return [name for name, _ in counter.most_common(3)]
