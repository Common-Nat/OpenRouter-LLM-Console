from fastapi import APIRouter, Depends, HTTPException
import aiosqlite

from ...db import get_db
from ... import repo
from ...schemas import ModelUsageSummary, UsageLogCreate, UsageLogOut


router = APIRouter(prefix="/usage", tags=["usage"])


@router.post("", response_model=UsageLogOut, status_code=201)
async def create_usage_log(payload: UsageLogCreate, db: aiosqlite.Connection = Depends(get_db)):
    usage_id = await repo.insert_usage_log(db, **payload.model_dump())

    rows = await repo.list_usage_by_session(db, payload.session_id)
    created = next((r for r in rows if r["id"] == usage_id), None)
    if not created:
        raise HTTPException(status_code=404, detail="Usage log not found after creation")
    return dict(created)


@router.get("/sessions/{session_id}", response_model=list[UsageLogOut])
async def usage_by_session(session_id: str, db: aiosqlite.Connection = Depends(get_db)):
    rows = await repo.list_usage_by_session(db, session_id)
    return [dict(r) for r in rows]


@router.get("/models", response_model=list[ModelUsageSummary])
async def usage_by_model(db: aiosqlite.Connection = Depends(get_db)):
    rows = await repo.aggregate_usage_by_model(db)
    return [dict(r) for r in rows]
