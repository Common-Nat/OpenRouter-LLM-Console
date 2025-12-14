"""Rate limiting configuration using SlowAPI.

This module provides configurable rate limiting to protect endpoints from abuse.
Rate limits are applied per IP address and can be customized per endpoint.
All limits are configurable via environment variables.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize the limiter with IP-based rate limiting
# The key_func determines how to identify unique clients (by IP address)
limiter = Limiter(key_func=get_remote_address)

def get_rate_limits():
    """Get rate limits from settings (called at runtime to use env vars).
    
    Returns:
        dict: Rate limit strings for each endpoint type
    """
    from .config import settings
    
    return {
        # Critical resource-intensive endpoints
        "stream": settings.rate_limit_stream,
        "model_sync": settings.rate_limit_model_sync,
        "document_upload": settings.rate_limit_upload,
        
        # Standard CRUD operations
        "sessions": settings.rate_limit_sessions,
        "messages": settings.rate_limit_messages,
        "profiles": settings.rate_limit_profiles,
        
        # Read-only operations (more lenient)
        "models_list": settings.rate_limit_models_list,
        "usage_logs": settings.rate_limit_usage_logs,
        "health_check": settings.rate_limit_health_check,
    }

# Rate limit presets for different endpoint types
# Format: "X per Y" where X is number of requests and Y is time period
# Supported periods: second, minute, hour, day
# NOTE: These are loaded from environment variables via get_rate_limits()
RATE_LIMITS = get_rate_limits()
