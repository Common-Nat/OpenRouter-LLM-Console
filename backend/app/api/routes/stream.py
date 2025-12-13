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
    temperature: float = Query(0.7, ge=0.0, le=2.0),
    max_tokens: int = Query(2048, ge=1, le=32768),
    db: aiosqlite.Connection = Depends(get_db),
):
    if not settings.openrouter_api_key:
        raise HTTPException(status_code=400, detail="OPENROUTER_API_KEY is not set")

    # Build messages for OpenRouter from DB
    rows = await repo.list_messages(db, session_id)
    messages = [{"role": r["role"], "content": r["content"]} for r in rows]

    async def gen():
        assistant_accum = ""
        yield sse_data({"type": "meta", "message": "stream_start"})
        try:
            async for line in stream_chat_completions(model=model_id, messages=messages, temperature=temperature, max_tokens=max_tokens):
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
