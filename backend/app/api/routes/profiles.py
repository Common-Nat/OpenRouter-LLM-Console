from fastapi import APIRouter, Depends
import aiosqlite
from ...db import get_db
from ... import repo
from ...schemas import ProfileCreate, ProfileOut

router = APIRouter(prefix="/profiles", tags=["profiles"])

@router.post("", response_model=ProfileOut)
async def create_profile(payload: ProfileCreate, db: aiosqlite.Connection = Depends(get_db)):
    pid = await repo.create_profile(db, payload.model_dump())
    return {"id": pid, **payload.model_dump()}

@router.get("", response_model=list[ProfileOut])
async def list_profiles(db: aiosqlite.Connection = Depends(get_db)):
    rows = await repo.list_profiles(db)
    return [dict(r) for r in rows]
