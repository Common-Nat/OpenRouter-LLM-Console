"""Rate limiting configuration using SlowAPI.

This module provides configurable rate limiting to protect endpoints from abuse.
Rate limits are applied per IP address and can be customized per endpoint.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize the limiter with IP-based rate limiting
# The key_func determines how to identify unique clients (by IP address)
limiter = Limiter(key_func=get_remote_address)

# Rate limit presets for different endpoint types
# Format: "X per Y" where X is number of requests and Y is time period
# Supported periods: second, minute, hour, day
RATE_LIMITS = {
    # Critical resource-intensive endpoints
    "stream": "20 per minute",  # LLM streaming - most expensive operation
    "model_sync": "5 per hour",  # Model catalog sync - external API call
    "document_upload": "30 per minute",  # File uploads - resource intensive
    
    # Standard CRUD operations
    "sessions": "60 per minute",  # Session creation/updates
    "messages": "100 per minute",  # Message operations
    "profiles": "60 per minute",  # Profile CRUD
    
    # Read-only operations (more lenient)
    "models_list": "120 per minute",  # Model listing
    "usage_logs": "120 per minute",  # Usage statistics
    "health_check": "300 per minute",  # Health endpoint
}
