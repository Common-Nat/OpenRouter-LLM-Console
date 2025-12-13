from __future__ import annotations
import logging
import httpx
from typing import Any, AsyncIterator, Dict, List
from ..core.config import settings

logger = logging.getLogger(__name__)


class OpenRouterError(RuntimeError):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code


def _headers() -> Dict[str, str]:
    if not settings.openrouter_api_key:
        # allow boot without key; calls will fail with explicit error
        return {}
    return {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "HTTP-Referer": settings.openrouter_http_referer,
        "X-Title": settings.openrouter_x_title,
        "Content-Type": "application/json",
    }


ASYNC_TIMEOUT = 30


async def list_models() -> Dict[str, Any]:
    logger.info("Requesting OpenRouter models", extra={"action": "openrouter_request", "endpoint": "/models"})
    async with httpx.AsyncClient(base_url=settings.openrouter_base_url, timeout=ASYNC_TIMEOUT) as client:
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
