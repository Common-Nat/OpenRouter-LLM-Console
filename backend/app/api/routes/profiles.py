from fastapi import APIRouter, Depends, HTTPException, Response, Request
import aiosqlite
from ...db import get_db
from ... import repo
from ...schemas import ProfileCreate, ProfileOut
from ...core.ratelimit import limiter, RATE_LIMITS
from ...core.errors import APIError

router = APIRouter(prefix="/profiles", tags=["profiles"])

@router.post("", response_model=ProfileOut)
@limiter.limit(RATE_LIMITS["profiles"])
async def create_profile(request: Request, payload: ProfileCreate, db: aiosqlite.Connection = Depends(get_db)):
    pid = await repo.create_profile(db, payload.model_dump())
    return {"id": pid, **payload.model_dump()}

@router.get("", response_model=list[ProfileOut])
async def list_profiles(db: aiosqlite.Connection = Depends(get_db)):
    rows = await repo.list_profiles(db)
    return [dict(r) for r in rows]

@router.get("/{profile_id}", response_model=ProfileOut)
async def get_profile(profile_id: int, db: aiosqlite.Connection = Depends(get_db)):
    row = await repo.get_profile(db, profile_id)
    if not row:
        raise APIError.not_found(
            APIError.PROFILE_NOT_FOUND,
            resource_type="profile",
            resource_id=profile_id
        )
    return dict(row)

@router.put("/{profile_id}", response_model=ProfileOut)
async def update_profile(profile_id: int, payload: ProfileCreate, db: aiosqlite.Connection = Depends(get_db)):
    updated = await repo.update_profile(db, profile_id, payload.model_dump())
    if not updated:
        raise APIError.not_found(
            APIError.PROFILE_NOT_FOUND,
            resource_type="profile",
            resource_id=profile_id
        )
    row = await repo.get_profile(db, profile_id)
    return dict(row)

@router.delete("/{profile_id}", status_code=204)
async def delete_profile(profile_id: int, db: aiosqlite.Connection = Depends(get_db)):
    deleted = await repo.delete_profile(db, profile_id)
    if not deleted:
        raise APIError.not_found(
            APIError.PROFILE_NOT_FOUND,
            resource_type="profile",
            resource_id=profile_id
        )
    return Response(status_code=204)
