"""
Cache management endpoints for monitoring and clearing caches.
"""
from fastapi import APIRouter
from ...core.cache import profile_cache, model_cache

router = APIRouter(prefix="/cache", tags=["cache"])


@router.get("/stats")
async def get_cache_stats():
    """
    Get statistics for all cache instances.
    
    Returns hit rates, sizes, and TTL configurations.
    """
    return {
        "caches": [
            profile_cache.stats(),
            model_cache.stats(),
        ]
    }


@router.post("/clear")
async def clear_all_caches():
    """
    Clear all cache instances.
    
    Use this if you suspect stale data or after manual database changes.
    """
    profile_cache.clear()
    model_cache.clear()
    return {
        "message": "All caches cleared successfully",
        "cleared": ["profiles", "models"]
    }


@router.post("/clear/profiles")
async def clear_profile_cache():
    """Clear only the profile cache."""
    profile_cache.clear()
    return {
        "message": "Profile cache cleared successfully"
    }


@router.post("/clear/models")
async def clear_model_cache():
    """Clear only the model cache."""
    model_cache.clear()
    return {
        "message": "Model cache cleared successfully"
    }
