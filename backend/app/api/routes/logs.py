"""
Frontend logging endpoint

Receives structured logs from the frontend for debugging and monitoring.
"""
import logging
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.core.ratelimit import limiter

logger = logging.getLogger(__name__)

router = APIRouter()


class LogEntry(BaseModel):
    """Frontend log entry"""
    level: str = Field(..., description="Log level: debug, info, warn, error, critical")
    message: str = Field(..., description="Log message")
    meta: dict = Field(default_factory=dict, description="Additional metadata")
    context: dict = Field(default_factory=dict, description="Context (session, route, etc)")


class FrontendLogsRequest(BaseModel):
    """Batch of frontend logs"""
    logs: List[LogEntry]


@router.post("")
@limiter.limit("60/minute")  # Allow 60 log requests per minute per IP
async def receive_frontend_logs(
    request: Request,
    logs_request: FrontendLogsRequest,
):
    """
    Receive frontend logs and write them to backend logs.
    
    This endpoint allows the frontend to send structured logs to the backend
    for centralized monitoring and debugging. Logs are rate-limited to prevent spam.
    """
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    for log_entry in logs_request.logs:
        # Map frontend log levels to Python logging levels
        level_map = {
            'debug': 'debug',
            'info': 'info',
            'warn': 'warning',
            'error': 'error',
            'critical': 'critical',
        }
        
        log_level = level_map.get(log_entry.level.lower(), 'info')
        log_method = getattr(logger, log_level)
        
        # Log with structured extra data
        log_method(
            f"[FRONTEND] {log_entry.message}",
            extra={
                "action": "frontend_log",
                "request_id": request_id,
                "frontend_level": log_entry.level,
                "frontend_session": log_entry.context.get("sessionId"),
                "frontend_route": log_entry.context.get("route"),
                "frontend_timestamp": log_entry.context.get("timestamp"),
                "frontend_meta": log_entry.meta,
            }
        )
    
    return {
        "success": True,
        "received": len(logs_request.logs),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
