from fastapi import APIRouter, Depends, HTTPException, Query, Request
import aiosqlite
from ...db import get_db
from ... import repo
from ...schemas import SessionCreate, SessionUpdate, SessionOut, MessageOut
from ...core.ratelimit import limiter, RATE_LIMITS

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("", response_model=SessionOut)
@limiter.limit(RATE_LIMITS["sessions"])
async def create_session(request: Request, payload: SessionCreate, db: aiosqlite.Connection = Depends(get_db)):
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

@router.get("/{session_id}", response_model=SessionOut)
async def get_session(session_id: str, db: aiosqlite.Connection = Depends(get_db)):
    row = await repo.get_session(db, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    return dict(row)

@router.put("/{session_id}", response_model=SessionOut)
async def update_session(session_id: str, payload: SessionUpdate, db: aiosqlite.Connection = Depends(get_db)):
    # Check if session exists
    existing = await repo.get_session(db, session_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Update with only provided fields
    updated = await repo.update_session(db, session_id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Return updated session
    row = await repo.get_session(db, session_id)
    return dict(row) if row else {}

@router.delete("/{session_id}")
async def delete_session(session_id: str, db: aiosqlite.Connection = Depends(get_db)):
    deleted = await repo.delete_session(db, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session deleted successfully"}

@router.get("/{session_id}/messages", response_model=list[MessageOut])
async def session_messages(session_id: str, db: aiosqlite.Connection = Depends(get_db)):
    rows = await repo.list_messages(db, session_id)
    return [dict(r) for r in rows]
