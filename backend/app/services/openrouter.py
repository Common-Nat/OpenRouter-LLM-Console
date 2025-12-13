from __future__ import annotations
import httpx
from typing import Any, AsyncIterator, Dict, List, Optional
from ..core.config import settings

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

async def list_models() -> Dict[str, Any]:
    async with httpx.AsyncClient(base_url=settings.openrouter_base_url, timeout=30) as client:
        r = await client.get("/models", headers=_headers())
        if r.status_code != 200:
            raise OpenRouterError(r.status_code, f"OpenRouter /models failed: {r.text}")
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
    async with httpx.AsyncClient(base_url=settings.openrouter_base_url, timeout=None) as client:
        async with client.stream("POST", "/chat/completions", headers=_headers(), json=payload) as resp:
            if resp.status_code != 200:
                text = await resp.aread()
                raise OpenRouterError(resp.status_code, f"OpenRouter stream failed: {text.decode('utf-8','ignore')}")
            async for line in resp.aiter_lines():
                yield line
