import pytest
from httpx import AsyncClient, ASGITransport

from app.core.config import settings
from app import db as dbmod
from app.main import app


@pytest.mark.asyncio
async def test_list_documents(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "db_path", str(tmp_path / "test_documents.db"))
    monkeypatch.setattr(settings, "uploads_dir", str(tmp_path / "uploads"))
    await dbmod.init_db()

    uploads = tmp_path / "uploads"
    uploads.mkdir(parents=True, exist_ok=True)
    (uploads / "example.txt").write_text("This is a sample document.")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/documents")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "example.txt"
    assert data[0]["size"] == len("This is a sample document.")


@pytest.mark.asyncio
async def test_document_qa_requires_api_key(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "db_path", str(tmp_path / "test_documents.db"))
    monkeypatch.setattr(settings, "uploads_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "openrouter_api_key", "")
    await dbmod.init_db()

    uploads = tmp_path / "uploads"
    uploads.mkdir(parents=True, exist_ok=True)
    (uploads / "example.txt").write_text("Hello")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/documents/example.txt/qa", json={"question": "Hi?", "model_id": "test-model"}
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "OPENROUTER_API_KEY is not set"


@pytest.mark.asyncio
async def test_document_path_traversal_prevented(monkeypatch, tmp_path):
    """Test that path traversal attacks are prevented"""
    monkeypatch.setattr(settings, "db_path", str(tmp_path / "test_documents.db"))
    monkeypatch.setattr(settings, "uploads_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")
    await dbmod.init_db()

    uploads = tmp_path / "uploads"
    uploads.mkdir(parents=True, exist_ok=True)
    (uploads / "example.txt").write_text("Safe document")
    
    # Create a file outside uploads directory
    (tmp_path / "secret.txt").write_text("Secret data")

    # Try path traversal attack
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/documents/../secret.txt/qa",
            json={"question": "What's in this file?", "model_id": "test-model"}
        )

    # Should return 404, not expose the secret file
    assert response.status_code == 404
    # Accept either FastAPI's generic 404 or our custom error message
    assert response.json()["detail"] in ["Document not found", "Not Found"]
