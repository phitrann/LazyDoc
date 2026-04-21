from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse

from app.core.dependencies import get_analyzer
from app.schemas.error import APIError
from app.schemas.request import RepositoryRequest
from app.utils.url_validator import InvalidRepositoryURLError, parse_repository_url

router = APIRouter()


@router.post("/research")
async def research_repository(
    request: RepositoryRequest,
    analyzer = Depends(get_analyzer),
    x_github_token: str | None = Header(None),
) -> JSONResponse:
    try:
        owner, repo = parse_repository_url(request.repository_url)
    except InvalidRepositoryURLError as exc:
        error = APIError("INVALID_URL", str(exc), 400)
        return JSONResponse(status_code=error.status_code, content={"status": "error", "error_code": error.error_code, "message": error.message})

    try:
        data = await analyzer.analyze(owner, repo, github_token=x_github_token)
    except APIError as exc:
        payload = {"status": "error", "error_code": exc.error_code, "message": exc.message}
        if exc.retry_after_seconds is not None:
            payload["retry_after_seconds"] = exc.retry_after_seconds
        return JSONResponse(status_code=exc.status_code, content=payload)

    warnings = data.pop("warnings", []) if isinstance(data, dict) else []
    status = "partial" if warnings else "success"
    response_payload = {"status": status, "data": data, "warnings": warnings}
    
    if hasattr(analyzer, '_client') and analyzer._client:
        rate_limit = analyzer._client.get_rate_limit()
        if rate_limit:
            response_payload["rate_limit"] = rate_limit
    
    return JSONResponse(status_code=200, content=response_payload)
