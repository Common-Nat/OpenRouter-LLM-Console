import pytest
from httpx import AsyncClient, ASGITransport

from app.core.config import settings
from app import db as dbmod
from app.main import app


@pytest.mark.asyncio
async def test_create_message_invalid_session(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "db_path", str(tmp_path / "test_messages.db"))
    await dbmod.init_db()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/messages",
            json={"session_id": "missing-session", "role": "user", "content": "Hello"},
        )

    assert response.status_code == 404
    error_data = response.json()
    assert error_data["error_code"] == "SESSION_NOT_FOUND"
    assert "not found" in error_data["message"].lower()
