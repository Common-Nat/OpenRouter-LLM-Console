from fastapi import APIRouter, Depends
import aiosqlite
from ...db import get_db
from ... import repo
from ...schemas import MessageCreate, MessageOut

router = APIRouter(prefix="/messages", tags=["messages"])

@router.post("", response_model=MessageOut)
async def create_message(payload: MessageCreate, db: aiosqlite.Connection = Depends(get_db)):
    mid = await repo.add_message(db, payload.session_id, payload.role, payload.content)
    rows = await repo.list_messages(db, payload.session_id)
    msg = next((r for r in rows if r["id"] == mid), None)
    return dict(msg) if msg else {"id": mid, "session_id": payload.session_id, "role": payload.role, "content": payload.content, "created_at": ""}
