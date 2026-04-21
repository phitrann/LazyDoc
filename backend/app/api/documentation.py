import json

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse, StreamingResponse

from app.core.dependencies import get_documentation_generator
from app.schemas.error import APIError
from app.schemas.request import RepositoryRequest
from app.utils.url_validator import InvalidRepositoryURLError, parse_repository_url

router = APIRouter()


@router.post("/documentation")
async def generate_documentation(
    request: RepositoryRequest,
    generator = Depends(get_documentation_generator),
    x_github_token: str | None = Header(None),
) -> JSONResponse:
    try:
        owner, repo = parse_repository_url(request.repository_url)
    except InvalidRepositoryURLError as exc:
        error = APIError("INVALID_URL", str(exc), 400)
        return JSONResponse(
            status_code=error.status_code,
            content={"status": "error", "error_code": error.error_code, "message": error.message},
        )

    # Use provided token if available, otherwise fall back to configured token
    if x_github_token and hasattr(generator, '_client') and generator._client:
        generator._client.set_token(x_github_token)

    try:
        data = await generator.generate(owner, repo, force_refresh=request.force_regenerate)
    except APIError as exc:
        payload = {"status": "error", "error_code": exc.error_code, "message": exc.message}
        if exc.retry_after_seconds is not None:
            payload["retry_after_seconds"] = exc.retry_after_seconds
        return JSONResponse(status_code=exc.status_code, content=payload)

    warnings = data.pop("warnings", []) if isinstance(data, dict) else []
    status = "partial" if warnings else "success"
    response_payload = {"status": status, "data": data, "warnings": warnings}
    
    if hasattr(generator, '_client') and generator._client:
        rate_limit = generator._client.get_rate_limit()
        if rate_limit:
            response_payload["rate_limit"] = rate_limit
    
    return JSONResponse(status_code=200, content=response_payload)


def _to_sse(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


@router.post("/documentation/stream")
async def stream_documentation_ai(
    request: RepositoryRequest,
    generator=Depends(get_documentation_generator),
    x_github_token: str | None = Header(None),
):
    try:
        owner, repo = parse_repository_url(request.repository_url)
    except InvalidRepositoryURLError as exc:
        error = APIError("INVALID_URL", str(exc), 400)
        return JSONResponse(
            status_code=error.status_code,
            content={"status": "error", "error_code": error.error_code, "message": error.message},
        )

    # Use provided token if available, otherwise fall back to configured token
    if x_github_token and hasattr(generator, '_client') and generator._client:
        generator._client.set_token(x_github_token)

    async def event_stream():
        try:
            async for event in generator.stream_ai_section(owner, repo, force_refresh=request.force_regenerate):
                event_type = str(event.get("event", "message"))
                payload = {key: value for key, value in event.items() if key != "event"}
                yield _to_sse(event_type, payload)
                if event_type == "error":
                    break
        except APIError as exc:
            payload = {"error_code": exc.error_code, "message": exc.message}
            if exc.retry_after_seconds is not None:
                payload["retry_after_seconds"] = exc.retry_after_seconds
            yield _to_sse("error", payload)
        yield _to_sse("done", {"status": "done"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
