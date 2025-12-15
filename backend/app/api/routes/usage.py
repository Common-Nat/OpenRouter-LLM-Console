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


@router.get("/timeline")
@limiter.limit(RATE_LIMITS["usage_logs"])
async def usage_timeline(
    request: Request,
    start_date: str = None,
    end_date: str = None,
    granularity: str = "day",
    db: aiosqlite.Connection = Depends(get_db)
):
    """Get time-series usage data grouped by period.
    
    Args:
        start_date: ISO date (YYYY-MM-DD), optional
        end_date: ISO date (YYYY-MM-DD), optional
        granularity: 'day', 'week', or 'month' (default: 'day')
    """
    rows = await repo.get_usage_timeline(db, start_date, end_date, granularity)
    return [dict(r) for r in rows]


@router.get("/stats")
@limiter.limit(RATE_LIMITS["usage_logs"])
async def usage_stats(
    request: Request,
    start_date: str = None,
    end_date: str = None,
    db: aiosqlite.Connection = Depends(get_db)
):
    """Get summary statistics for usage within date range.
    
    Args:
        start_date: ISO date (YYYY-MM-DD), optional
        end_date: ISO date (YYYY-MM-DD), optional
    """
    row = await repo.get_usage_stats(db, start_date, end_date)
    if row:
        return dict(row)
    return {
        "total_requests": 0,
        "total_tokens": 0,
        "total_prompt_tokens": 0,
        "total_completion_tokens": 0,
        "total_cost": 0,
        "avg_cost_per_request": 0,
        "first_request": None,
        "last_request": None,
        "unique_models": 0,
        "unique_sessions": 0
    }
