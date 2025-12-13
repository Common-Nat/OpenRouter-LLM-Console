from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
import aiosqlite
import json
from ...db import get_db
from ... import repo
from ...core.sse import sse_data
from ...services.openrouter import stream_chat_completions, OpenRouterError
from ...core.config import settings

router = APIRouter(prefix="", tags=["stream"])

@router.get("/stream")
async def stream(
    session_id: str = Query(...),
    model_id: str = Query(...),
    temperature: float | None = Query(None, ge=0.0, le=2.0),
    max_tokens: int | None = Query(None, ge=1, le=32768),
    profile_id: int | None = Query(None),
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

    # Build messages for OpenRouter from DB
    rows = await repo.list_messages(db, session_id)
    messages = [{"role": r["role"], "content": r["content"]} for r in rows]
    if profile and profile.get("system_prompt"):
        messages = [{"role": "system", "content": profile["system_prompt"]}, *messages]

    async def gen():
        assistant_accum = ""
        yield sse_data({"type": "meta", "message": "stream_start"})
        try:
            async for line in stream_chat_completions(model=model_id, messages=messages, temperature=resolved_temperature, max_tokens=resolved_max_tokens):
                if not line:
                    continue
                if line.startswith("data: "):
                    chunk = line[len("data: "):].strip()
                else:
                    chunk = line.strip()

                if chunk == "[DONE]":
                    break

                # Forward raw chunks, but also attempt to extract token deltas for convenience
                token = None
                try:
                    obj = json.loads(chunk)
                    delta = (((obj.get("choices") or [{}])[0]).get("delta") or {})
                    token = delta.get("content")
                except Exception:
                    obj = None

                if token:
                    assistant_accum += token
                    yield sse_data({"type": "token", "token": token})
                else:
                    yield sse_data({"type": "raw", "data": chunk})
        except OpenRouterError as e:
            yield sse_data({"type": "error", "status": e.status_code, "message": str(e)}, event="error")
            return
        except Exception as e:
            yield sse_data({"type": "error", "message": str(e)}, event="error")
            return
        finally:
            if assistant_accum.strip():
                await repo.add_message(db, session_id, "assistant", assistant_accum)
            yield sse_data({"type": "meta", "message": "stream_end"})

    return StreamingResponse(gen(), media_type="text/event-stream")
