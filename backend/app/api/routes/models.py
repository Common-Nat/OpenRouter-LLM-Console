from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
import aiosqlite

from ...db import get_db
from ... import repo
from ...schemas import ModelOut
from ...services import openrouter
from ...core.config import settings

router = APIRouter(prefix="/models", tags=["models"])

@router.post("/sync")
async def sync_models(db: aiosqlite.Connection = Depends(get_db)):
    if not settings.openrouter_api_key:
        raise HTTPException(status_code=400, detail="OPENROUTER_API_KEY is not set")

    data = await openrouter.list_models()

    # OpenRouter returns a `data` array. Map fields conservatively.
    models = []
    for m in data.get("data", []):
        pricing = m.get("pricing") or {}
        models.append({
            "openrouter_id": m.get("id"),
            "name": m.get("name") or m.get("id"),
            "context_length": m.get("context_length"),
            "pricing_prompt": _to_float(pricing.get("prompt")),
            "pricing_completion": _to_float(pricing.get("completion")),
            "is_reasoning": bool((m.get("features") or {}).get("reasoning")) or bool(m.get("is_reasoning")),
        })
    count = await repo.upsert_models(db, models)
    return {"synced": count}

def _to_float(v):
    try:
        return float(v) if v is not None else None
    except Exception:
        return None

@router.get("", response_model=list[ModelOut])
async def list_models(
    reasoning: Optional[bool] = Query(default=None),
    max_price: Optional[float] = Query(default=None, ge=0),
    min_context: Optional[int] = Query(default=None, ge=1),
    db: aiosqlite.Connection = Depends(get_db),
):
    rows = await repo.list_models(db, reasoning=reasoning, max_price=max_price, min_context=min_context)
    return [{
        "id": r["id"],
        "openrouter_id": r["openrouter_id"],
        "name": r["name"],
        "context_length": r["context_length"],
        "pricing_prompt": r["pricing_prompt"],
        "pricing_completion": r["pricing_completion"],
        "is_reasoning": bool(r["is_reasoning"]),
    } for r in rows]
