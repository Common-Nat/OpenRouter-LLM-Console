from fastapi import APIRouter, Depends, HTTPException, Request, Query
from typing import Optional, List
import aiosqlite
from ...db import get_db
from ... import repo
from ...schemas import MessageCreate, MessageOut, MessageSearchRequest, MessageSearchResult
from ...core.ratelimit import limiter, RATE_LIMITS
from ...core.errors import APIError

router = APIRouter(prefix="/messages", tags=["messages"])

@router.post("", response_model=MessageOut)
@limiter.limit(RATE_LIMITS["messages"])
async def create_message(request: Request, payload: MessageCreate, db: aiosqlite.Connection = Depends(get_db)):
    session = await repo.get_session(db, payload.session_id)
    if not session:
        raise APIError.not_found(
            APIError.SESSION_NOT_FOUND,
            resource_type="session",
            resource_id=payload.session_id
        )

    mid = await repo.add_message(db, payload.session_id, payload.role, payload.content)
    rows = await repo.list_messages(db, payload.session_id)
    msg = next((r for r in rows if r["id"] == mid), None)
    return dict(msg) if msg else {"id": mid, "session_id": payload.session_id, "role": payload.role, "content": payload.content, "created_at": ""}


@router.get("/search", response_model=List[MessageSearchResult])
@limiter.limit(RATE_LIMITS["messages"])
async def search_messages(
    request: Request,
    query: str = Query(..., min_length=1, description="Search query"),
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    session_type: Optional[str] = Query(None, description="Filter by session type"),
    model_id: Optional[str] = Query(None, description="Filter by model ID"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: aiosqlite.Connection = Depends(get_db)
):
    """
    Full-text search across messages with filters.
    
    Supports FTS5 query syntax:
    - "exact phrase" for phrase matching
    - -term to exclude
    - prefix* for prefix matching
    - term1 OR term2 for alternatives
    """
    try:
        results = await repo.search_messages(
            db,
            query,
            session_id=session_id,
            session_type=session_type,
            model_id=model_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        return [dict(row) for row in results]
    except Exception as e:
        # Handle FTS5 syntax errors gracefully
        if "fts5" in str(e).lower() or "syntax" in str(e).lower():
            raise APIError.validation_error(
                "search_query_invalid",
                "Invalid search query syntax",
                details={"error": str(e)}
            )
        raise
