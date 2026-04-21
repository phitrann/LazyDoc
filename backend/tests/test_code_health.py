import asyncio

from app.core.cache import TTLCache
from app.services.code_health import CodeHealthAnalyzer
from app.services.github_client import GitHubClient
from app.services.repo_analyzer import RepoAnalyzer


class FakeCodeHealthClient:
    def __init__(self) -> None:
        self.files = {
            "src/app.py": (
                'from .utils import helper\n'
                'API_TOKEN = "ghp_1234567890abcdef1234567890abcdef1234"\n'
                'exec(helper("x"))\n'
                'breakpoint()\n'
            ),
            "src/utils.py": (
                "from .app import main\n"
                "def helper(value):\n"
                "    return value\n"
            ),
        }

    async def get_file_contents(self, owner: str, repo: str, path: str, github_token: str | None = None) -> str:
        return self.files[path]

    async def get_repository(self, owner: str, repo: str, github_token: str | None = None) -> dict:
        return {
            "name": repo,
            "owner": {"login": owner},
            "description": "Example",
            "stargazers_count": 1,
            "forks_count": 0,
            "updated_at": "2026-04-14T12:00:00Z",
            "html_url": f"https://github.com/{owner}/{repo}",
            "default_branch": "main",
            "license": None,
        }

    async def get_languages(self, owner: str, repo: str, github_token: str | None = None) -> dict[str, int]:
        return {"Python": 120}

    async def get_commits(self, owner: str, repo: str, github_token: str | None = None) -> list[dict]:
        return []

    async def get_contributors(self, owner: str, repo: str, github_token: str | None = None) -> list[dict]:
        return []

    async def get_repo_tree(self, owner: str, repo: str, branch: str, github_token: str | None = None) -> list[dict]:
        return [
            {"path": "src/app.py", "type": "blob", "size": 100},
            {"path": "src/utils.py", "type": "blob", "size": 100},
            {"path": "docs/README.md", "type": "blob", "size": 100},
        ]


class SecurityOnlyClient:
    async def get_file_contents(self, owner: str, repo: str, path: str, github_token: str | None = None) -> str:
        if path == "src/app.py":
            return 'from .utils import helper\nAPI_TOKEN = "ghp_1234567890abcdef1234567890abcdef1234"\n'
        return "def helper():\n    return True\n"


class PythonImportClient:
    def __init__(self, files: dict[str, str]) -> None:
        self.files = files

    async def get_file_contents(self, owner: str, repo: str, path: str, github_token: str | None = None) -> str:
        return self.files[path]


def test_code_health_analyzer_detects_findings_and_cycles() -> None:
    analyzer = CodeHealthAnalyzer(client=FakeCodeHealthClient())

    result = asyncio.run(analyzer.analyze("owner", "repo", [{"path": "src/app.py", "type": "blob", "size": 100}, {"path": "src/utils.py", "type": "blob", "size": 100}], None))

    assert result is not None
    assert result["metrics"]["scanned_files"] == 2
    assert result["metrics"]["security_findings"] >= 1
    assert result["metrics"]["architecture_findings"] >= 1
    assert result["metrics"]["circular_dependencies"] >= 1
    assert result["findings"]
    assert any(finding["evidence"] for finding in result["findings"])
    assert result["grade"] in {"A", "B", "C", "D", "F"}


def test_code_health_security_penalty_only_counts_security_findings() -> None:
    analyzer = CodeHealthAnalyzer(client=SecurityOnlyClient())

    result = asyncio.run(
        analyzer.analyze(
            "owner",
            "repo",
            [
                {"path": "src/app.py", "type": "blob", "size": 100},
                {"path": "src/utils.py", "type": "blob", "size": 100},
            ],
            None,
        )
    )

    assert result is not None
    security_breakdown = next(item for item in result["breakdown"] if item["name"] == "Security")
    overall_breakdown = next(item for item in result["breakdown"] if item["name"] == "Overall")
    assert security_breakdown["impact"] == -10
    assert security_breakdown["drivers"] == ["1 High security finding (-10)"]
    assert overall_breakdown["impact"] == -10


def test_repo_analyzer_includes_code_health() -> None:
    client = FakeCodeHealthClient()
    analyzer = RepoAnalyzer(client=client, cache=TTLCache(ttl_seconds=60))

    result = asyncio.run(analyzer.analyze("owner", "repo"))

    assert result["code_health"]["findings"]
    assert result["code_health"]["metrics"]["security_findings"] >= 1
    assert result["code_health"]["metrics"]["architecture_findings"] >= 1


def test_code_health_resolves_absolute_python_package_imports() -> None:
    analyzer = CodeHealthAnalyzer(
        client=PythonImportClient(
            {
                "backend/app/api/documentation.py": "from app.utils import url_validator\n",
                "backend/app/utils/url_validator.py": "def parse_repository_url(value):\n    return value\n",
            }
        )
    )

    result = asyncio.run(
        analyzer.analyze(
            "owner",
            "repo",
            [
                {"path": "backend/app/api/documentation.py", "type": "blob", "size": 100},
                {"path": "backend/app/utils/url_validator.py", "type": "blob", "size": 100},
            ],
            None,
        )
    )

    assert result is not None
    assert result["metrics"]["coupling_index"] == 0.5


def test_code_health_resolves_parent_relative_python_imports() -> None:
    analyzer = CodeHealthAnalyzer(
        client=PythonImportClient(
            {
                "backend/app/api/documentation.py": "from ..utils import url_validator\n",
                "backend/app/utils/url_validator.py": "def parse_repository_url(value):\n    return value\n",
            }
        )
    )

    result = asyncio.run(
        analyzer.analyze(
            "owner",
            "repo",
            [
                {"path": "backend/app/api/documentation.py", "type": "blob", "size": 100},
                {"path": "backend/app/utils/url_validator.py", "type": "blob", "size": 100},
            ],
            None,
        )
    )

    assert result is not None
    assert result["metrics"]["coupling_index"] == 0.5


def test_code_health_detects_cycle_after_resolving_python_imports() -> None:
    analyzer = CodeHealthAnalyzer(
        client=PythonImportClient(
            {
                "backend/app/api/documentation.py": "from app.utils import url_validator\n",
                "backend/app/utils/url_validator.py": "from app.api import documentation\n",
            }
        )
    )

    result = asyncio.run(
        analyzer.analyze(
            "owner",
            "repo",
            [
                {"path": "backend/app/api/documentation.py", "type": "blob", "size": 100},
                {"path": "backend/app/utils/url_validator.py", "type": "blob", "size": 100},
            ],
            None,
        )
    )

    assert result is not None
    assert result["metrics"]["circular_dependencies"] >= 1
    assert any(finding["rule_name"] == "circular-dependency" for finding in result["findings"])
