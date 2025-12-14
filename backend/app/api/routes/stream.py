from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
import aiosqlite
from ...db import get_db
from ... import repo
from ...services.openrouter import process_streaming_response
from ...core.config import settings

router = APIRouter(prefix="", tags=["stream"])


@router.get("/stream")
async def stream(
    session_id: str = Query(...),
    model_id: str = Query(...),
    temperature: Optional[float] = Query(None, ge=0.0, le=2.0),
    max_tokens: Optional[int] = Query(None, ge=1, le=32768),
    profile_id: Optional[int] = Query(None),
    db: aiosqlite.Connection = Depends(get_db),
):
    if not settings.openrouter_api_key:
        raise HTTPException(status_code=400, detail="OPENROUTER_API_KEY is not set")

    session = await repo.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    resolved_profile_id = profile_id if profile_id is not None else session["profile_id"]
    profile = None
    if resolved_profile_id is not None:
        profile = await repo.get_profile(db, int(resolved_profile_id))
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

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
