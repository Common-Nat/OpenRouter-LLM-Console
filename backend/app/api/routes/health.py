from fastapi import APIRouter, Request
from ...core.ratelimit import limiter, RATE_LIMITS
router = APIRouter()

@router.get("/health")
@limiter.limit(RATE_LIMITS["health_check"])
async def health(request: Request):
    return {"ok": True}
