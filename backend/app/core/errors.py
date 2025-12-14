"""Structured error handling for consistent API responses."""
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel
from fastapi import HTTPException

from .logging_config import request_id_ctx_var


class ErrorDetail(BaseModel):
    """Structured error response model."""
    error_code: str
    message: str
    request_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class APIError:
    """Standardized error codes and helper functions."""
    
    # Resource not found errors (404)
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    PROFILE_NOT_FOUND = "PROFILE_NOT_FOUND"
    DOCUMENT_NOT_FOUND = "DOCUMENT_NOT_FOUND"
    MESSAGE_NOT_FOUND = "MESSAGE_NOT_FOUND"
    USAGE_LOG_NOT_FOUND = "USAGE_LOG_NOT_FOUND"
    
    # Configuration errors (400/500)
    MISSING_API_KEY = "MISSING_API_KEY"
    MISSING_FILENAME = "MISSING_FILENAME"
    
    # File operation errors (500)
    FILE_SAVE_FAILED = "FILE_SAVE_FAILED"
    FILE_DELETE_FAILED = "FILE_DELETE_FAILED"
    
    # OpenRouter errors
    OPENROUTER_ERROR = "OPENROUTER_ERROR"
    STREAM_ERROR = "STREAM_ERROR"
    
    @staticmethod
    def not_found(
        error_code: str,
        resource_type: str,
        resource_id: Union[str, int],
        message: Optional[str] = None
    ) -> HTTPException:
        """Create a 404 not found exception with structured detail."""
        if message is None:
            message = f"{resource_type.capitalize()} not found"
        
        detail = ErrorDetail(
            error_code=error_code,
            message=message,
            request_id=request_id_ctx_var.get("-"),
            resource_type=resource_type,
            resource_id=str(resource_id)
        )
        return HTTPException(status_code=404, detail=detail.model_dump())
    
    @staticmethod
    def bad_request(
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> HTTPException:
        """Create a 400 bad request exception with structured detail."""
        detail = ErrorDetail(
            error_code=error_code,
            message=message,
            request_id=request_id_ctx_var.get("-"),
            details=details
        )
        return HTTPException(status_code=400, detail=detail.model_dump())
    
    @staticmethod
    def internal_error(
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> HTTPException:
        """Create a 500 internal server error with structured detail."""
        detail = ErrorDetail(
            error_code=error_code,
            message=message,
            request_id=request_id_ctx_var.get("-"),
            details=details
        )
        return HTTPException(status_code=500, detail=detail.model_dump())
