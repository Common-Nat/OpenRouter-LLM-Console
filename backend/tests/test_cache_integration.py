"""
Integration tests for repository caching.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.cache import profile_cache, model_cache


@pytest.fixture(autouse=True)
def clear_caches():
    """Clear caches before each test."""
    profile_cache.clear()
    model_cache.clear()
    yield
    profile_cache.clear()
    model_cache.clear()


@pytest.mark.asyncio
async def test_profile_caching():
    """Test that profiles are cached and reused."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create a profile
        response = await client.post(
            "/api/profiles",
            json={
                "name": "Cache Test Profile",
                "system_prompt": "Test prompt",
                "temperature": 0.8,
                "max_tokens": 1024
            }
        )
        assert response.status_code == 200
        profile_id = response.json()["id"]
        
        # First fetch - should be a cache miss
        initial_stats = profile_cache.stats()
        initial_misses = initial_stats["misses"]
        
        response = await client.get(f"/api/profiles/{profile_id}")
        assert response.status_code == 200
        
        stats_after_first = profile_cache.stats()
        assert stats_after_first["misses"] == initial_misses + 1  # Cache miss
        assert stats_after_first["size"] == 1  # One item cached
        
        # Second fetch - should be a cache hit
        response = await client.get(f"/api/profiles/{profile_id}")
        assert response.status_code == 200
        
        stats_after_second = profile_cache.stats()
        assert stats_after_second["hits"] == initial_stats["hits"] + 1  # Cache hit
        assert stats_after_second["misses"] == stats_after_first["misses"]  # No new misses


@pytest.mark.asyncio
async def test_profile_cache_invalidation_on_update():
    """Test that updating a profile invalidates its cache."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create a profile
        response = await client.post(
            "/api/profiles",
            json={"name": "Original Name", "temperature": 0.7}
        )
        profile_id = response.json()["id"]
        
        # Fetch to populate cache
        response = await client.get(f"/api/profiles/{profile_id}")
        original_data = response.json()
        assert original_data["name"] == "Original Name"
        
        # Verify it's cached
        stats = profile_cache.stats()
        assert stats["size"] >= 1
        
        # Update the profile
        response = await client.put(
            f"/api/profiles/{profile_id}",
            json={"name": "Updated Name", "temperature": 0.9}
        )
        assert response.status_code == 200
        
        # Fetch again - should get fresh data (not cached old data)
        response = await client.get(f"/api/profiles/{profile_id}")
        updated_data = response.json()
        assert updated_data["name"] == "Updated Name"
        assert updated_data["temperature"] == 0.9


@pytest.mark.asyncio
async def test_profile_list_cache_invalidation():
    """Test that profile list cache is invalidated on create/delete."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Get initial list and cache it
        response = await client.get("/api/profiles")
        initial_count = len(response.json())
        
        # Should be cached now
        stats = profile_cache.stats()
        assert stats["size"] >= 1
        
        # Create a new profile
        response = await client.post(
            "/api/profiles",
            json={"name": "New Profile"}
        )
        new_profile_id = response.json()["id"]
        
        # Fetch list again - should reflect the new profile
        response = await client.get("/api/profiles")
        new_count = len(response.json())
        assert new_count == initial_count + 1
        
        # Delete the profile
        response = await client.delete(f"/api/profiles/{new_profile_id}")
        assert response.status_code == 204
        
        # List should be updated
        response = await client.get("/api/profiles")
        final_count = len(response.json())
        assert final_count == initial_count


@pytest.mark.asyncio
async def test_cache_stats_endpoint():
    """Test the cache stats endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/cache/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "caches" in data
        assert len(data["caches"]) == 2  # profiles and models
        
        # Check structure
        for cache_stats in data["caches"]:
            assert "name" in cache_stats
            assert "hits" in cache_stats
            assert "misses" in cache_stats
            assert "size" in cache_stats
            assert "ttl" in cache_stats


@pytest.mark.asyncio
async def test_cache_clear_endpoint():
    """Test the cache clear endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Add some cached data
        response = await client.get("/api/profiles")
        assert profile_cache.stats()["size"] >= 0
        
        # Clear all caches
        response = await client.post("/api/cache/clear")
        assert response.status_code == 200
        assert "cleared" in response.json()
        
        # Verify caches are empty
        assert profile_cache.stats()["size"] == 0
        assert model_cache.stats()["size"] == 0
