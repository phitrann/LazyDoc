from __future__ import annotations

import asyncio
import json
from math import sqrt
from textwrap import shorten
from typing import AsyncIterator, Callable

from app.core.cache import TTLCache
from app.services.github_client import GitHubClient
from app.services.local_models import LocalEmbeddingClient, LocalLLMClient
from app.services.repo_analyzer import RepoAnalyzer


class DocumentationGenerator:
    def __init__(
        self,
        client: GitHubClient,
        analyzer: RepoAnalyzer,
        llm_client: LocalLLMClient,
        embedding_client: LocalEmbeddingClient,
        cache: TTLCache[dict],
    ) -> None:
        self._client = client
        self._analyzer = analyzer
        self._llm_client = llm_client
        self._embedding_client = embedding_client
        self._cache = cache

    async def generate(self, owner: str, repo: str, force_refresh: bool = False) -> dict:
        return await self._generate_report(owner, repo, force_refresh)

    async def stream_ai_section(self, owner: str, repo: str, force_refresh: bool = False) -> AsyncIterator[dict]:
        queue: asyncio.Queue[dict | None] = asyncio.Queue()

        def emit(event: dict) -> None:
            queue.put_nowait(event)

        async def produce() -> None:
            try:
                await self._generate_report(owner, repo, force_refresh, emit=emit)
            except Exception as exc:  # noqa: BLE001 - convert upstream failures into stream events.
                if hasattr(exc, "error_code") and hasattr(exc, "message"):
                    queue.put_nowait(
                        {
                            "event": "error",
                            "error_code": getattr(exc, "error_code"),
                            "message": getattr(exc, "message"),
                            "retry_after_seconds": getattr(exc, "retry_after_seconds", None),
                        }
                    )
                else:
                    queue.put_nowait({"event": "error", "error_code": "STREAM_FAILED", "message": str(exc)})
            finally:
                queue.put_nowait(None)

        producer = asyncio.create_task(produce())
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield event
        finally:
            await producer

    async def _generate_report(
        self,
        owner: str,
        repo: str,
        force_refresh: bool,
        emit: Callable[[dict], None] | None = None,
    ) -> dict:
        cache_key = f"docs:{owner}/{repo}"
        if not force_refresh:
            cached = self._cache.get(cache_key)
            if cached is not None:
                if emit:
                    emit(
                        {
                            "event": "complete",
                            "data": {
                                "readme_summary": cached.get("readme_summary"),
                                "recommendations": cached.get("recommendations", []),
                                "risk_observations": cached.get("risk_observations", []),
                                "sections": cached.get("sections", []),
                                "markdown": cached.get("markdown", ""),
                                "warnings": cached.get("warnings", []),
                            },
                            "cached": True,
                        }
                    )
                return cached

        warnings: list[str] = []
        analysis = await self._analyzer.analyze(owner, repo)
        analysis_warnings = list(analysis.pop("warnings", [])) if isinstance(analysis.get("warnings"), list) else []
        if emit:
            emit({"event": "stage", "stage": "analysis_complete", "message": "Repository analysis complete."})
        readme = await self._safe_call(warnings, self._client.get_readme(owner, repo), None)
        if emit:
            emit({"event": "stage", "stage": "readme_loaded", "message": "README content loaded."})

        readme_summary = await self._summarize_readme(readme, analysis, warnings, emit=emit)
        if emit:
            emit({"event": "ai_update", "data": {"readme_summary": readme_summary}})
        recommendations, risk_observations = await self._generate_insights(analysis, readme_summary, warnings)
        if emit:
            emit(
                {
                    "event": "ai_update",
                    "data": {
                        "recommendations": recommendations,
                        "risk_observations": risk_observations,
                    },
                }
            )
        sections = self._sections(analysis, readme_summary, recommendations, risk_observations)
        markdown = self._markdown(analysis, sections, readme_summary, recommendations, risk_observations)

        combined_warnings = [*analysis_warnings, *warnings]
        result = {
            **analysis,
            "sections": sections,
            "markdown": markdown,
            "readme_summary": readme_summary,
            "recommendations": recommendations,
            "risk_observations": risk_observations,
        }
        if combined_warnings:
            result["warnings"] = combined_warnings
        self._cache.set(cache_key, result)
        if emit:
            emit(
                {
                    "event": "complete",
                    "data": {
                        "readme_summary": readme_summary,
                        "recommendations": recommendations,
                        "risk_observations": risk_observations,
                        "sections": sections,
                        "markdown": markdown,
                        "warnings": combined_warnings,
                    },
                    "cached": False,
                }
            )
        return result

    async def _safe_call(self, warnings: list[str], coroutine, fallback):
        try:
            return await coroutine
        except Exception as exc:  # noqa: BLE001 - convert external errors to report warnings.
            warnings.append(str(exc))
            return fallback

    async def _summarize_readme(
        self,
        readme: str | None,
        analysis: dict,
        warnings: list[str],
        emit: Callable[[dict], None] | None = None,
    ) -> str | None:
        if not readme:
            return None
        paragraphs = [paragraph.strip() for paragraph in readme.splitlines() if paragraph.strip()]
        if not paragraphs:
            return None
        context = await self._select_readme_context(readme, analysis)
        prompt = (
            "Summarize this repository README in 3-5 concise sentences. "
            "Focus on purpose, installation or usage signals, and any notable constraints. "
            "Return plain text only.\n\n"
            f"Repository: {analysis['overview']['owner']}/{analysis['overview']['name']}\n\n"
            f"README context:\n{context}"
        )
        try:
            summary = ""
            if emit:
                streamed_parts: list[str] = []
                async for token in self._llm_client.stream_text(
                    system_prompt="You produce concise, accurate repository documentation summaries.",
                    user_prompt=prompt,
                    max_tokens=220,
                ):
                    streamed_parts.append(token)
                    emit({"event": "token", "field": "readme_summary", "token": token})
                summary = "".join(streamed_parts)
                if not summary.strip():
                    summary = await self._llm_client.generate_json(
                        system_prompt="You produce concise, accurate repository documentation summaries.",
                        user_prompt=prompt,
                        max_tokens=220,
                    )
            else:
                summary = await self._llm_client.generate_json(
                    system_prompt="You produce concise, accurate repository documentation summaries.",
                    user_prompt=prompt,
                    max_tokens=220,
                )
            summary = summary.strip()
            if summary:
                return summary
        except Exception as exc:  # noqa: BLE001 - fallback to deterministic summary when the local model is unavailable.
            warnings.append(self._model_fallback_warning("README summary model fallback", exc))

        fallback = " ".join(paragraphs[:3])
        return shorten(fallback, width=420, placeholder="...")

    async def _generate_insights(
        self,
        analysis: dict,
        readme_summary: str | None,
        warnings: list[str],
    ) -> tuple[list[str], list[str]]:
        prompt = self._insights_prompt(analysis, readme_summary)
        try:
            raw = await self._llm_client.generate_json(
                system_prompt=(
                    "You generate structured repository documentation insights. "
                    "Return valid JSON with keys recommendations and risk_observations, each an array of short strings."
                ),
                user_prompt=prompt,
                max_tokens=320,
            )
            payload = json.loads(raw)
            recommendations = [str(item).strip() for item in payload.get("recommendations", []) if str(item).strip()]
            risk_observations = [str(item).strip() for item in payload.get("risk_observations", []) if str(item).strip()]
            if recommendations or risk_observations:
                return recommendations[:4], risk_observations[:4]
        except Exception as exc:  # noqa: BLE001 - local model output can be unavailable or malformed.
            warnings.append(self._model_fallback_warning("Insight generation fallback", exc))

        return self._recommendations(analysis, readme_summary), self._risk_observations(analysis, readme_summary)

    def _model_fallback_warning(self, prefix: str, exc: Exception) -> str:
        message = str(exc).strip()
        normalized = message.lower()
        if any(token in normalized for token in ("connection", "connect", "refused", "unreachable")):
            reason = "connection unavailable"
        elif "timeout" in normalized:
            reason = "request timed out"
        else:
            reason = "model unavailable"
        return f"{prefix}: {reason}. Used deterministic fallback."

    async def _select_readme_context(self, readme: str, analysis: dict) -> str:
        paragraphs = [paragraph.strip() for paragraph in readme.splitlines() if paragraph.strip()]
        if len(paragraphs) <= 40:
            return "\n".join(paragraphs)

        overview = analysis["overview"]
        query = (
            f"Repository overview, usage, installation, architecture, testing, and contributing guidance for {overview['owner']}/{overview['name']}"
        )

        candidate_indexes = list(range(min(15, len(paragraphs))))
        middle_start = max(len(paragraphs) // 2 - 5, 0)
        candidate_indexes.extend(range(middle_start, min(middle_start + 10, len(paragraphs))))
        candidate_indexes.extend(range(max(len(paragraphs) - 15, 0), len(paragraphs)))
        candidate_indexes = list(dict.fromkeys(candidate_indexes))
        candidates = [paragraphs[index] for index in candidate_indexes]

        try:
            query_embedding = await self._embedding_client.create_embedding(query)
            scored_candidates: list[tuple[float, str]] = []
            for paragraph in candidates:
                paragraph_embedding = await self._embedding_client.create_embedding(paragraph)
                scored_candidates.append((self._cosine_similarity(query_embedding, paragraph_embedding), paragraph))
            scored_candidates.sort(key=lambda item: item[0], reverse=True)
            selected = [paragraph for _, paragraph in scored_candidates[:18]]
            return "\n".join(selected)
        except Exception:
            selected = paragraphs[:12] + paragraphs[len(paragraphs) // 2 : len(paragraphs) // 2 + 8] + paragraphs[-12:]
            deduplicated = list(dict.fromkeys(selected))
            return "\n".join(deduplicated[:32])

    def _cosine_similarity(self, left: list[float], right: list[float]) -> float:
        dot_product = sum(a * b for a, b in zip(left, right))
        left_norm = sqrt(sum(value * value for value in left))
        right_norm = sqrt(sum(value * value for value in right))
        if not left_norm or not right_norm:
            return 0.0
        return dot_product / (left_norm * right_norm)

    def _insights_prompt(self, analysis: dict, readme_summary: str | None) -> str:
        overview = analysis["overview"]
        insights = analysis["insights"]
        activity = analysis["activity"]
        structure = analysis["structure"]
        return (
            "Generate 3-4 practical recommendations and 2-4 risk observations for this repository. "
            "Keep each item short, specific, and grounded in the provided metadata.\n\n"
            f"Repository: {overview['owner']}/{overview['name']}\n"
            f"Primary language: {insights['primary_language'] or 'Unknown'}\n"
            f"Dependency files: {', '.join(insights['dependency_files']) or 'None'}\n"
            f"Recent commits last 30 days: {activity['recent_commits_last_30_days']}\n"
            f"Contributors: {activity['total_contributors']}\n"
            f"Active contributors last 30 days: {activity['active_contributors_last_30_days']}\n"
            f"README summary: {readme_summary or 'Unavailable'}\n"
            f"README present: {structure['has_readme']}\n"
            f"License present: {structure['has_license']}\n"
            f"Top directories: {', '.join(structure['top_directories']) or 'None'}\n\n"
            "Return JSON only with keys recommendations and risk_observations."
        )

    def _recommendations(self, analysis: dict, readme_summary: str | None) -> list[str]:
        recommendations: list[str] = []
        structure = analysis["structure"]
        insights = analysis["insights"]
        activity = analysis["activity"]

        if not structure["has_readme"]:
            recommendations.append("Add or improve the README so new contributors can understand the project faster.")
        if not structure["has_license"] and not insights["has_license"]:
            recommendations.append("Add a license file to clarify usage and redistribution rights.")
        if activity["recent_commits_last_30_days"] == 0:
            recommendations.append("Commit activity is low, so consider documenting maintenance expectations and release cadence.")
        if not insights["dependency_files"]:
            recommendations.append("No standard dependency manifest was detected, so double-check how the project is installed and built.")
        if readme_summary is None:
            recommendations.append("No README summary was available, so the repository may benefit from better top-level documentation.")
        if not recommendations:
            recommendations.append("The repository has a healthy baseline signal; keep the docs in sync with future code changes.")
        return recommendations[:4]

    def _risk_observations(self, analysis: dict, readme_summary: str | None) -> list[str]:
        observations: list[str] = []
        activity = analysis["activity"]
        structure = analysis["structure"]

        if activity["active_contributors_last_30_days"] <= 1:
            observations.append("Recent maintenance appears concentrated in one contributor, which can create continuity risk.")
        if structure["total_files"] > 500:
            observations.append("The repository tree is large, so documentation generation should sample carefully to stay responsive.")
        if readme_summary is None:
            observations.append("Lack of README content makes it harder to verify intent, setup steps, and project boundaries.")
        if not observations:
            observations.append("No immediate structural risk signals were detected from the available metadata.")
        return observations[:4]

    def _sections(
        self,
        analysis: dict,
        readme_summary: str | None,
        recommendations: list[str],
        risk_observations: list[str],
    ) -> list[dict]:
        overview = analysis["overview"]
        insights = analysis["insights"]
        activity = analysis["activity"]
        structure = analysis["structure"]

        return [
            {
                "title": "Repository Overview",
                "summary": f"{overview['name']} is owned by {overview['owner']} and last updated on {overview['last_updated']}",
                "content": [
                    f"Description: {overview['description'] or 'No description provided.'}",
                    f"Stars: {overview['stars']}",
                    f"Forks: {overview['forks']}",
                    f"Default branch: {overview['default_branch']}",
                    f"Last updated: {overview['last_updated']}",
                ],
            },
            {
                "title": "Project Insights",
                "summary": f"{insights['primary_language'] or 'Unknown'} is the main language, with {len(insights['dependency_files'])} dependency files detected.",
                "content": [
                    f"Primary language: {insights['primary_language'] or 'Unknown'}",
                    "Languages: " + (", ".join(f"{language['name']} ({language['percentage']}%)" for language in insights["languages"]) or "None detected"),
                    f"Dependency files: {', '.join(insights['dependency_files']) or 'None detected'}",
                    f"License: {insights['license_name'] or 'Not detected'}",
                ],
            },
            {
                "title": "Activity & Health",
                "summary": f"The repository recorded {activity['recent_commits_last_30_days']} commits over the last 30 days and {activity['total_contributors']} contributors overall.",
                "content": [
                    f"Commits in the last 7 days: {activity['recent_commits_last_7_days']}",
                    f"Commits in the last 30 days: {activity['recent_commits_last_30_days']}",
                    f"Last commit date: {activity['last_commit_date'] or 'Unknown'}",
                    f"Total contributors: {activity['total_contributors']}",
                    f"Active contributors in the last 30 days: {activity['active_contributors_last_30_days']}",
                ],
            },
            {
                "title": "Structure Summary",
                "summary": f"The tree contains {structure['total_files']} files and top directories {', '.join(structure['top_directories']) or 'were not detected'}.",
                "content": [
                    f"Total files: {structure['total_files']}",
                    f"README present: {'Yes' if structure['has_readme'] else 'No'}",
                    f"License present: {'Yes' if structure['has_license'] else 'No'}",
                    f"Top directories: {', '.join(structure['top_directories']) or 'None detected'}",
                ],
            },
            {
                "title": "README Summary",
                "summary": readme_summary or "No README content was available.",
                "content": [readme_summary or "README content was not detected or could not be summarized."],
            },
            {
                "title": "Recommendations",
                "summary": "Actionable suggestions derived from repository signals.",
                "content": recommendations,
            },
            {
                "title": "Security & Risk Observations",
                "summary": "Potential maintenance and documentation risks to review.",
                "content": risk_observations,
            },
        ]

    def _markdown(
        self,
        analysis: dict,
        sections: list[dict],
        readme_summary: str | None,
        recommendations: list[str],
        risk_observations: list[str],
    ) -> str:
        overview = analysis["overview"]
        lines = [
            f"# {overview['name']} Documentation Report",
            "",
            f"- Owner: {overview['owner']}",
            f"- Description: {overview['description'] or 'No description provided.'}",
            f"- Stars: {overview['stars']}",
            f"- Forks: {overview['forks']}",
            f"- Last updated: {overview['last_updated']}",
            "",
        ]
        for section in sections:
            lines.append(f"## {section['title']}")
            lines.append(section["summary"])
            lines.append("")
            for item in section["content"]:
                lines.append(f"- {item}")
            lines.append("")
        if readme_summary:
            lines.append("## README Summary")
            lines.append(readme_summary)
            lines.append("")
        if recommendations:
            lines.append("## Recommendations")
            lines.extend(f"- {recommendation}" for recommendation in recommendations)
            lines.append("")
        if risk_observations:
            lines.append("## Security & Risk Observations")
            lines.extend(f"- {observation}" for observation in risk_observations)
            lines.append("")
        return "\n".join(lines).strip() + "\n"
