from typing import AsyncIterator, Optional
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
import aiosqlite
from ...db import get_db
from ... import repo
from ...services.openrouter import process_streaming_response
from ...core.config import settings
from ...core.sse import sse_data
from ...core.logging_config import request_id_ctx_var
from ...core.ratelimit import limiter, RATE_LIMITS
from ...core.errors import APIError

router = APIRouter(prefix="", tags=["stream"])


async def _error_stream(
    error_code: str,
    status: int,
    message: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None
) -> AsyncIterator[str]:
    """Helper to yield structured SSE error event instead of raising HTTPException for streams."""
    yield sse_data(
        {
            "error_code": error_code,
            "status": status,
            "message": message,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "request_id": request_id_ctx_var.get("-"),
        },
        event="error",
    )


@router.get("/stream")
@limiter.limit(RATE_LIMITS["stream"])
async def stream(
    request: Request,
    session_id: str = Query(...),
    model_id: str = Query(...),
    temperature: Optional[float] = Query(None, ge=0.0, le=2.0),
    max_tokens: Optional[int] = Query(None, ge=1, le=32768),
    profile_id: Optional[int] = Query(None),
    db: aiosqlite.Connection = Depends(get_db),
):
    # Validation: return SSE error events instead of HTTPException
    # so EventSource receives proper error events, not HTTP errors
    if not settings.openrouter_api_key:
        return StreamingResponse(
            _error_stream(
                APIError.MISSING_API_KEY,
                400,
                "OpenRouter API key is not configured"
            ),
            media_type="text/event-stream",
        )

    session = await repo.get_session(db, session_id)
    if not session:
        return StreamingResponse(
            _error_stream(
                APIError.SESSION_NOT_FOUND,
                404,
                "Session not found",
                resource_type="session",
                resource_id=session_id
            ),
            media_type="text/event-stream",
        )

    resolved_profile_id = profile_id if profile_id is not None else session["profile_id"]
    profile = None
    if resolved_profile_id is not None:
        profile = await repo.get_profile(db, int(resolved_profile_id))
        if not profile:
            return StreamingResponse(
                _error_stream(
                    APIError.PROFILE_NOT_FOUND,
                    404,
                    "Profile not found",
                    resource_type="profile",
                    resource_id=str(resolved_profile_id)
                ),
                media_type="text/event-stream",
            )

    resolved_temperature = temperature if temperature is not None else (profile["temperature"] if profile else 0.7)
    resolved_max_tokens = max_tokens if max_tokens is not None else (profile["max_tokens"] if profile else 2048)

    resolved_model_id = model_id
    profile_preset = profile.get("openrouter_preset") if profile else None
    if profile_preset:
        preset_suffix = profile_preset if str(profile_preset).startswith("@preset/") else f"@preset/{profile_preset}"
        if "@preset/" not in resolved_model_id:
            resolved_model_id = f"{resolved_model_id}{preset_suffix}"

    # Build messages for OpenRouter from DB
    rows = await repo.list_messages(db, session_id)
    messages = [{"role": r["role"], "content": r["content"]} for r in rows]
    if profile and profile.get("system_prompt"):
        messages = [{"role": "system", "content": profile["system_prompt"]}, *messages]

    try:
        return StreamingResponse(
            process_streaming_response(
                session_id=session_id,
                resolved_model_id=resolved_model_id,
                messages=messages,
                resolved_temperature=resolved_temperature,
                resolved_max_tokens=resolved_max_tokens,
                resolved_profile_id=resolved_profile_id,
                db=db,
            ),
            media_type="text/event-stream",
        )
    except Exception:
        # If exception occurs before streaming starts, return error stream
        return StreamingResponse(
            _error_stream(
                "STREAM_ERROR",
                500,
                "An error occurred while initializing the stream",
            ),
            media_type="text/event-stream",
        )
