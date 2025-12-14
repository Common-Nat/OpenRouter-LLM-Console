from fastapi import APIRouter, Depends, HTTPException, Request
import aiosqlite
from ...db import get_db
from ... import repo
from ...schemas import MessageCreate, MessageOut
from ...core.ratelimit import limiter, RATE_LIMITS

router = APIRouter(prefix="/messages", tags=["messages"])

@router.post("", response_model=MessageOut)
@limiter.limit(RATE_LIMITS["messages"])
async def create_message(request: Request, payload: MessageCreate, db: aiosqlite.Connection = Depends(get_db)):
    session = await repo.get_session(db, payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    mid = await repo.add_message(db, payload.session_id, payload.role, payload.content)
    rows = await repo.list_messages(db, payload.session_id)
    msg = next((r for r in rows if r["id"] == mid), None)
    return dict(msg) if msg else {"id": mid, "session_id": payload.session_id, "role": payload.role, "content": payload.content, "created_at": ""}
