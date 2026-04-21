import pytest

from app.utils.url_validator import InvalidRepositoryURLError, parse_repository_url


def test_parse_repository_url_accepts_standard_url() -> None:
    owner, repo = parse_repository_url("https://github.com/owner/repo")
    assert owner == "owner"
    assert repo == "repo"


def test_parse_repository_url_accepts_missing_scheme() -> None:
    owner, repo = parse_repository_url("github.com/Owner/Repo")
    assert owner == "owner"
    assert repo == "repo"


def test_parse_repository_url_accepts_git_suffix() -> None:
    owner, repo = parse_repository_url("https://github.com/Owner/Repo.git")
    assert owner == "owner"
    assert repo == "repo"


def test_parse_repository_url_rejects_bad_host() -> None:
    with pytest.raises(InvalidRepositoryURLError):
        parse_repository_url("https://example.com/owner/repo")


def test_parse_repository_url_rejects_missing_repo_name() -> None:
    with pytest.raises(InvalidRepositoryURLError):
        parse_repository_url("https://github.com/owner/.git")


def test_parse_repository_url_rejects_nested_path() -> None:
    with pytest.raises(InvalidRepositoryURLError):
        parse_repository_url("https://github.com/owner/repo/issues/1")
