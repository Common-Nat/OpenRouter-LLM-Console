import pytest
from httpx import AsyncClient

from app.core.config import settings
from app import db as dbmod
from app.main import app


@pytest.mark.asyncio
async def test_create_message_invalid_session(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "db_path", str(tmp_path / "test_messages.db"))
    await dbmod.init_db()

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/messages",
            json={"session_id": "missing-session", "role": "user", "content": "Hello"},
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"
