from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.core.dependencies import get_documentation_generator
from app.schemas.error import APIError
from app.schemas.request import RepositoryRequest
from app.utils.url_validator import InvalidRepositoryURLError, parse_repository_url

router = APIRouter()


@router.post("/documentation")
async def generate_documentation(
    request: RepositoryRequest,
    generator = Depends(get_documentation_generator),
) -> JSONResponse:
    try:
        owner, repo = parse_repository_url(request.repository_url)
    except InvalidRepositoryURLError as exc:
        error = APIError("INVALID_URL", str(exc), 400)
        return JSONResponse(
            status_code=error.status_code,
            content={"status": "error", "error_code": error.error_code, "message": error.message},
        )

    try:
        data = await generator.generate(owner, repo, force_refresh=request.force_regenerate)
    except APIError as exc:
        payload = {"status": "error", "error_code": exc.error_code, "message": exc.message}
        if exc.retry_after_seconds is not None:
            payload["retry_after_seconds"] = exc.retry_after_seconds
        return JSONResponse(status_code=exc.status_code, content=payload)

    warnings = data.pop("warnings", []) if isinstance(data, dict) else []
    status = "partial" if warnings else "success"
    return JSONResponse(status_code=200, content={"status": status, "data": data, "warnings": warnings})