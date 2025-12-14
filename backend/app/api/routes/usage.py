from fastapi import APIRouter, Depends, HTTPException, Request
import aiosqlite

from ...db import get_db
from ... import repo
from ...schemas import ModelUsageSummary, UsageLogCreate, UsageLogOut
from ...core.ratelimit import limiter, RATE_LIMITS
from ...core.errors import APIError


router = APIRouter(prefix="/usage", tags=["usage"])


@router.post("", response_model=UsageLogOut, status_code=201)
async def create_usage_log(payload: UsageLogCreate, db: aiosqlite.Connection = Depends(get_db)):
    usage_id = await repo.insert_usage_log(db, **payload.model_dump())

    rows = await repo.list_usage_by_session(db, payload.session_id)
    created = next((r for r in rows if r["id"] == usage_id), None)
    if not created:
        raise APIError.not_found(
            APIError.USAGE_LOG_NOT_FOUND,
            resource_type="usage_log",
            resource_id=usage_id,
            message="Usage log not found after creation"
        )
    return dict(created)


@router.get("/sessions/{session_id}", response_model=list[UsageLogOut])
@limiter.limit(RATE_LIMITS["usage_logs"])
async def usage_by_session(request: Request, session_id: str, db: aiosqlite.Connection = Depends(get_db)):
    rows = await repo.list_usage_by_session(db, session_id)
    return [dict(r) for r in rows]


@router.get("/models", response_model=list[ModelUsageSummary])
async def usage_by_model(db: aiosqlite.Connection = Depends(get_db)):
    rows = await repo.aggregate_usage_by_model(db)
    return [dict(r) for r in rows]
