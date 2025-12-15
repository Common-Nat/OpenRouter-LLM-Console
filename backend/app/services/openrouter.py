from __future__ import annotations
import asyncio
import json
import logging
import httpx
from typing import Any, AsyncIterator, Dict, List, Optional
import aiosqlite
from ..core.config import settings
from ..core.sse import sse_data
from ..core.logging_config import request_id_ctx_var
from .. import repo

logger = logging.getLogger(__name__)


class OpenRouterError(RuntimeError):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code


def _headers() -> Dict[str, str]:
    if not settings.openrouter_api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is not configured. "
            "Set the OPENROUTER_API_KEY environment variable."
        )
    return {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "HTTP-Referer": settings.openrouter_http_referer,
        "X-Title": settings.openrouter_x_title,
        "Content-Type": "application/json",
    }


async def list_models() -> Dict[str, Any]:
    logger.info("Requesting OpenRouter models", extra={"action": "openrouter_request", "endpoint": "/models"})
    async with httpx.AsyncClient(base_url=settings.openrouter_base_url, timeout=settings.openrouter_timeout) as client:
        r = await client.get("/models", headers=_headers())
        if r.status_code != 200:
            logger.warning(
                "OpenRouter /models returned non-200",
                extra={"action": "openrouter_response", "endpoint": "/models", "status_code": r.status_code},
            )
            raise OpenRouterError(r.status_code, f"OpenRouter /models failed: {r.text}")
        logger.info(
            "Received OpenRouter /models response",
            extra={"action": "openrouter_response", "endpoint": "/models", "status_code": r.status_code},
        )
        return r.json()


async def stream_chat_completions(
    *,
    model: str,
    messages: List[Dict[str, str]],
    temperature: float,
    max_tokens: int,
) -> AsyncIterator[str]:
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    logger.info(
        "Streaming chat completions to OpenRouter",
        extra={
            "action": "openrouter_request",
            "endpoint": "/chat/completions",
            "model": model,
            "message_count": len(messages),
        },
    )
    async with httpx.AsyncClient(base_url=settings.openrouter_base_url, timeout=None) as client:
        async with client.stream("POST", "/chat/completions", headers=_headers(), json=payload) as resp:
            if resp.status_code != 200:
                text = await resp.aread()
                logger.warning(
                    "OpenRouter stream returned non-200",
                    extra={
                        "action": "openrouter_response",
                        "endpoint": "/chat/completions",
                        "status_code": resp.status_code,
                    },
                )
                raise OpenRouterError(resp.status_code, f"OpenRouter stream failed: {text.decode('utf-8','ignore')}")

            try:
                async for line in resp.aiter_lines():
                    yield line
            except Exception:
                logger.exception(
                    "OpenRouter stream terminated unexpectedly",
                    extra={"action": "openrouter_response", "endpoint": "/chat/completions"},
                )
                raise
            else:
                logger.info(
                    "OpenRouter stream completed",
                    extra={
                        "action": "openrouter_response",
                        "endpoint": "/chat/completions",
                        "status_code": resp.status_code,
                    },
                )


async def process_streaming_response(
    *,
    session_id: str,
    resolved_model_id: str,
    messages: List[Dict[str, str]],
    resolved_temperature: float,
    resolved_max_tokens: int,
    resolved_profile_id: Optional[int],
    db: aiosqlite.Connection,
    start_event_data: Optional[Dict[str, Any]] = None,
) -> AsyncIterator[str]:
    """
    Unified streaming response processor for OpenRouter chat completions.
    
    Handles token parsing, usage tracking, error handling, and database persistence.
    Yields SSE-formatted events: start, token, error, done.
    """
    assistant_accum = ""
    usage_counts = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    
    # Emit start event
    start_data = start_event_data or {"message": "stream_start"}
    yield sse_data(start_data, event="start")

    try:
        async for line in stream_chat_completions(
            model=resolved_model_id,
            messages=messages,
            temperature=resolved_temperature,
            max_tokens=resolved_max_tokens,
        ):
            if not line:
                continue
            
            # Strip "data: " prefix if present
            if line.startswith("data: "):
                chunk = line[len("data: "):].strip()
            else:
                chunk = line.strip()

            if chunk == "[DONE]":
                break

            token = None
            obj = None

            try:
                obj = json.loads(chunk)
                delta = (((obj.get("choices") or [{}])[0]).get("delta") or {})

                # Extract usage information
                usage = obj.get("usage") or delta.get("usage") or ((obj.get("choices") or [{}])[0].get("usage"))
                if isinstance(usage, dict):
                    usage_counts["prompt_tokens"] = int(usage.get("prompt_tokens") or usage_counts["prompt_tokens"] or 0)
                    usage_counts["completion_tokens"] = int(
                        usage.get("completion_tokens") or usage_counts["completion_tokens"] or 0
                    )
                    usage_counts["total_tokens"] = int(
                        usage.get("total_tokens")
                        or usage_counts["total_tokens"]
                        or usage_counts["prompt_tokens"] + usage_counts["completion_tokens"]
                    )

                # Extract content from various formats
                content = delta.get("content")
                content_parts = []
                if isinstance(content, str):
                    content_parts.append(content)
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, str):
                            content_parts.append(item)
                        elif isinstance(item, dict):
                            item_text = item.get("text") or item.get("content")
                            if isinstance(item_text, str):
                                content_parts.append(item_text)

                token = "".join(content_parts)

                # Fallback: check for tool calls
                if not token:
                    tool_calls = delta.get("tool_calls") or []
                    tool_text_parts = []
                    if isinstance(tool_calls, list):
                        for call in tool_calls:
                            if not isinstance(call, dict):
                                continue
                            if isinstance(call.get("function"), dict):
                                arguments = call["function"].get("arguments")
                                if isinstance(arguments, str):
                                    tool_text_parts.append(arguments)
                            call_text = call.get("text")
                            if isinstance(call_text, str):
                                tool_text_parts.append(call_text)

                    token = "".join(tool_text_parts)
            except Exception:
                obj = None

            # Yield token or raw chunk
            if token:
                assistant_accum += token
                yield sse_data({"token": token}, event="token")
            else:
                yield sse_data({"raw": chunk}, event="token")
                
    except asyncio.CancelledError:
        logger.info(
            "Stream cancelled by client",
            extra={
                "action": "stream_cancelled",
                "session_id": session_id,
                "model": resolved_model_id,
            },
        )
        return
    except OpenRouterError as e:
        logger.error(
            f"OpenRouter API error: {e}",
            extra={
                "action": "stream_error",
                "error_type": "openrouter_error",
                "status_code": e.status_code,
                "session_id": session_id,
                "model": resolved_model_id,
            },
        )
        yield sse_data(
            {
                "status": e.status_code,
                "message": str(e),
                "error": "openrouter_error",
                "request_id": request_id_ctx_var.get("-"),
            },
            event="error",
        )
        return
    except Exception:
        logger.exception(
            "Unexpected error during stream processing",
            extra={
                "action": "stream_error",
                "error_type": "internal_error",
                "session_id": session_id,
                "model": resolved_model_id,
            },
        )
        yield sse_data(
            {
                "status": 500,
                "message": "An internal error occurred while processing the stream",
                "error": "internal_error",
                "request_id": request_id_ctx_var.get("-"),
            },
            event="error",
        )
        return
    else:
        # Save assistant message if content exists
        if assistant_accum.strip():
            await repo.add_message(db, session_id, "assistant", assistant_accum)

        # Log usage
        await repo.insert_usage_log(
            db,
            session_id=session_id,
            model_id=resolved_model_id,
            prompt_tokens=usage_counts["prompt_tokens"],
            completion_tokens=usage_counts["completion_tokens"],
            profile_id=resolved_profile_id,
        )

        # Emit done event with optional extra data
        done_data = {
            "message": "stream_end",
            "assistant": assistant_accum,
            "usage": usage_counts,
        }
        if start_event_data:
            # Propagate any extra fields from start event (e.g., session_id, document_id)
            for key in start_event_data:
                if key not in done_data and key != "message":
                    done_data[key] = start_event_data[key]
        
        yield sse_data(done_data, event="done")
