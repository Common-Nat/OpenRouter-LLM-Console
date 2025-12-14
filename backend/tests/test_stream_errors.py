"""
Tests for stream error handling scenarios.
"""
import pytest
import tempfile
import os
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch
from app.main import app
from app.core.config import settings
from app import repo
from app.services.openrouter import OpenRouterError


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="function", autouse=True)
async def setup_test_db():
    """Create a temporary database for each test."""
    # Create a temporary database file
    fd, temp_db = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    # Override the DB_PATH setting
    original_db_path = settings.db_path
    settings.db_path = temp_db
    
    # Import db module to force reinitialization
    from app import db
    # Initialize database
    await db.init_db()
    
    yield
    
    # Cleanup
    settings.db_path = original_db_path
    try:
        os.unlink(temp_db)
    except Exception:
        pass


@pytest.mark.asyncio
async def test_stream_missing_api_key(client: AsyncClient):
    """Test that missing OPENROUTER_API_KEY returns proper SSE error event."""
    with patch("app.core.config.settings.openrouter_api_key", None):
        response = await client.get(
            "/api/stream",
            params={
                "session_id": "test-session",
                "model_id": "test-model",
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Should receive SSE error event, not HTTP error
        content = response.text
        assert "event: error" in content
        # Check for error_code or message about API key
        assert ("MISSING_API_KEY" in content or "API key" in content)


@pytest.mark.asyncio
async def test_stream_session_not_found(client: AsyncClient):
    """Test that invalid session_id returns proper SSE error event."""
    with patch("app.api.routes.stream.settings.openrouter_api_key", "test-key"):
        response = await client.get(
            "/api/stream",
            params={
                "session_id": "nonexistent-session",
                "model_id": "test-model",
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        content = response.text
        assert "event: error" in content
        assert "Session not found" in content


@pytest.mark.asyncio
async def test_stream_profile_not_found(client: AsyncClient):
    """Test that invalid profile_id returns proper SSE error event."""
    # Create a session first
    from app.db import get_db
    with patch("app.api.routes.stream.settings.openrouter_api_key", "test-key"):
        async for db in get_db():
            session_id = await repo.create_session(db, {"session_type": "chat", "title": "test-session"})
            
            response = await client.get(
                "/api/stream",
                params={
                    "session_id": session_id,
                    "model_id": "test-model",
                    "profile_id": 999,  # Non-existent profile
                },
            )
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
            
            content = response.text
            assert "event: error" in content
            assert "Profile not found" in content


@pytest.mark.asyncio
async def test_stream_openrouter_error():
    """Test that OpenRouterError is properly converted to SSE error event."""
    from app.services.openrouter import process_streaming_response
    from app.db import get_db
    
    async for db in get_db():
        session_id = await repo.create_session(db, {"session_type": "chat", "title": "test-session"})
        
        with patch(
            "app.services.openrouter.stream_chat_completions",
            side_effect=OpenRouterError(429, "Rate limit exceeded"),
        ):
            events = []
            async for event in process_streaming_response(
                session_id=session_id,
                resolved_model_id="test-model",
                messages=[],
                resolved_temperature=0.7,
                resolved_max_tokens=100,
                resolved_profile_id=None,
                db=db,
            ):
                events.append(event)
            
            # Should get start event and error event
            error_events = [e for e in events if "event: error" in e]
            assert len(error_events) > 0
            
            error_content = "".join(error_events)
            assert "429" in error_content
            assert "Rate limit exceeded" in error_content


@pytest.mark.asyncio
async def test_stream_unexpected_error():
    """Test that unexpected exceptions are properly converted to SSE error events."""
    from app.services.openrouter import process_streaming_response
    from app.db import get_db
    
    async for db in get_db():
        session_id = await repo.create_session(db, {"session_type": "chat", "title": "test-session"})
        
        with patch(
            "app.services.openrouter.stream_chat_completions",
            side_effect=ValueError("Unexpected error"),
        ):
            events = []
            async for event in process_streaming_response(
                session_id=session_id,
                resolved_model_id="test-model",
                messages=[],
                resolved_temperature=0.7,
                resolved_max_tokens=100,
                resolved_profile_id=None,
                db=db,
            ):
                events.append(event)
            
            # Should get start event and error event
            error_events = [e for e in events if "event: error" in e]
            assert len(error_events) > 0
            
            error_content = "".join(error_events)
            assert "500" in error_content or "Internal server error" in error_content
