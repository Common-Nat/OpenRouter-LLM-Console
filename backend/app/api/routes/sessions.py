from fastapi import APIRouter, Depends, HTTPException, Query
import aiosqlite
from ...db import get_db
from ... import repo
from ...schemas import SessionCreate, SessionOut, MessageOut

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("", response_model=SessionOut)
async def create_session(payload: SessionCreate, db: aiosqlite.Connection = Depends(get_db)):
    sid = await repo.create_session(db, payload.model_dump())
    # fetch created row
    rows = await repo.list_sessions(db, limit=1)
    created = next((r for r in rows if r["id"] == sid), None)
    if not created:
        # fallback
        return {"id": sid, "session_type": payload.session_type, "title": payload.title, "profile_id": payload.profile_id, "created_at": ""}
    return dict(created)

@router.get("", response_model=list[SessionOut])
async def list_sessions(limit: int = Query(default=50, ge=1, le=500), db: aiosqlite.Connection = Depends(get_db)):
    rows = await repo.list_sessions(db, limit=limit)
    return [dict(r) for r in rows]

@router.get("/{session_id}/messages", response_model=list[MessageOut])
async def session_messages(session_id: str, db: aiosqlite.Connection = Depends(get_db)):
    rows = await repo.list_messages(db, session_id)
    return [dict(r) for r in rows]
