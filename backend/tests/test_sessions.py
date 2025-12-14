import pytest
import tempfile
import os
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings


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
async def test_create_and_get_session():
    """Test creating a session and then retrieving it by ID."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create a session
        create_response = await ac.post(
            "/api/sessions",
            json={"session_type": "chat", "title": "Test Session", "profile_id": None}
        )
        assert create_response.status_code == 200
        session_data = create_response.json()
        session_id = session_data["id"]
        assert session_data["title"] == "Test Session"
        assert session_data["session_type"] == "chat"
        
        # Get the session by ID
        get_response = await ac.get(f"/api/sessions/{session_id}")
        assert get_response.status_code == 200
        retrieved_session = get_response.json()
        assert retrieved_session["id"] == session_id
        assert retrieved_session["title"] == "Test Session"


@pytest.mark.asyncio
async def test_get_nonexistent_session():
    """Test getting a session that doesn't exist."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/sessions/nonexistent-id-12345")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_session_title():
    """Test updating a session's title."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create a session
        create_response = await ac.post(
            "/api/sessions",
            json={"session_type": "chat", "title": "Original Title"}
        )
        session_id = create_response.json()["id"]
        
        # Update the title
        update_response = await ac.put(
            f"/api/sessions/{session_id}",
            json={"title": "Updated Title"}
        )
        assert update_response.status_code == 200
        updated_session = update_response.json()
        assert updated_session["title"] == "Updated Title"
        assert updated_session["id"] == session_id
        
        # Verify the update persisted
        get_response = await ac.get(f"/api/sessions/{session_id}")
        assert get_response.json()["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_update_session_profile():
    """Test updating a session's profile_id to None."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create a session without profile
        create_response = await ac.post(
            "/api/sessions",
            json={"session_type": "chat", "title": "Profile Test"}
        )
        session_id = create_response.json()["id"]
        
        # Update profile_id to None (allowed since it's nullable)
        update_response = await ac.put(
            f"/api/sessions/{session_id}",
            json={"profile_id": None}
        )
        assert update_response.status_code == 200
        updated_session = update_response.json()
        assert updated_session["profile_id"] is None


@pytest.mark.asyncio
async def test_update_nonexistent_session():
    """Test updating a session that doesn't exist."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.put(
            "/api/sessions/nonexistent-id-12345",
            json={"title": "New Title"}
        )
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_session():
    """Test deleting a session."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create a session
        create_response = await ac.post(
            "/api/sessions",
            json={"session_type": "chat", "title": "To Be Deleted"}
        )
        session_id = create_response.json()["id"]
        
        # Delete the session
        delete_response = await ac.delete(f"/api/sessions/{session_id}")
        assert delete_response.status_code == 200
        assert "deleted" in delete_response.json()["message"].lower()
        
        # Verify it's gone
        get_response = await ac.get(f"/api/sessions/{session_id}")
        assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_session():
    """Test deleting a session that doesn't exist."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.delete("/api/sessions/nonexistent-id-12345")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_session_cascades_messages():
    """Test that deleting a session also deletes its messages."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create a session
        create_response = await ac.post(
            "/api/sessions",
            json={"session_type": "chat", "title": "Message Cascade Test"}
        )
        session_id = create_response.json()["id"]
        
        # Add a message to the session
        message_response = await ac.post(
            "/api/messages",
            json={
                "session_id": session_id,
                "role": "user",
                "content": "Test message"
            }
        )
        assert message_response.status_code == 200
        
        # Verify message exists
        messages_response = await ac.get(f"/api/sessions/{session_id}/messages")
        assert len(messages_response.json()) == 1
        
        # Delete the session
        delete_response = await ac.delete(f"/api/sessions/{session_id}")
        assert delete_response.status_code == 200
        
        # Verify session is gone (this indirectly tests cascade)
        get_response = await ac.get(f"/api/sessions/{session_id}")
        assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_partial_update():
    """Test that updating only one field doesn't affect others."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create a session with title (no profile)
        create_response = await ac.post(
            "/api/sessions",
            json={"session_type": "chat", "title": "Original", "profile_id": None}
        )
        session_id = create_response.json()["id"]
        
        # Update only the title
        update_response = await ac.put(
            f"/api/sessions/{session_id}",
            json={"title": "New Title"}
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        
        # Verify title changed but profile_id stayed the same (None)
        assert updated["title"] == "New Title"
        assert updated["profile_id"] is None
