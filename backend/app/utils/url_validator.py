from urllib.parse import urlparse


class InvalidRepositoryURLError(ValueError):
    pass


def parse_repository_url(repository_url: str) -> tuple[str, str]:
    candidate = repository_url.strip()
    if not candidate:
        raise InvalidRepositoryURLError("Repository URL is required.")
    if "://" not in candidate:
        candidate = f"https://{candidate}"
    parsed = urlparse(candidate)
    host = parsed.netloc.lower()
    if host not in {"github.com", "www.github.com"}:
        raise InvalidRepositoryURLError("Repository URL must point to github.com.")
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 2:
        raise InvalidRepositoryURLError("Repository URL must be in the form https://github.com/owner/repo.")
    owner, repo = parts
    if repo.endswith(".git"):
        repo = repo[:-4]
    return owner.lower(), repo.lower()
