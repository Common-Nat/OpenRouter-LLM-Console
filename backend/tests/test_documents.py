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
    error_data = response.json()
    assert error_data["error_code"] == "MISSING_API_KEY"
    assert "not configured" in error_data["message"]


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


@pytest.mark.asyncio
async def test_delete_document(monkeypatch, tmp_path):
    """Test deleting a document"""
    monkeypatch.setattr(settings, "db_path", str(tmp_path / "test_documents.db"))
    monkeypatch.setattr(settings, "uploads_dir", str(tmp_path / "uploads"))
    await dbmod.init_db()

    uploads = tmp_path / "uploads"
    uploads.mkdir(parents=True, exist_ok=True)
    test_file = uploads / "delete_me.txt"
    test_file.write_text("This will be deleted")

    # Verify file exists
    assert test_file.exists()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.delete("/api/documents/delete_me.txt")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Document deleted successfully"
    assert data["id"] == "delete_me.txt"
    
    # Verify file was deleted
    assert not test_file.exists()


@pytest.mark.asyncio
async def test_delete_nonexistent_document(monkeypatch, tmp_path):
    """Test deleting a document that doesn't exist"""
    monkeypatch.setattr(settings, "db_path", str(tmp_path / "test_documents.db"))
    monkeypatch.setattr(settings, "uploads_dir", str(tmp_path / "uploads"))
    await dbmod.init_db()

    uploads = tmp_path / "uploads"
    uploads.mkdir(parents=True, exist_ok=True)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.delete("/api/documents/nonexistent.txt")

    assert response.status_code == 404
    error_data = response.json()
    assert error_data["error_code"] == "DOCUMENT_NOT_FOUND"
    assert "not found" in error_data["message"].lower()
async def test_delete_document_path_traversal(monkeypatch, tmp_path):
    """Test that delete endpoint prevents path traversal attacks"""
    monkeypatch.setattr(settings, "db_path", str(tmp_path / "test_documents.db"))
    monkeypatch.setattr(settings, "uploads_dir", str(tmp_path / "uploads"))
    await dbmod.init_db()

    uploads = tmp_path / "uploads"
    uploads.mkdir(parents=True, exist_ok=True)
    
    # Create a file outside uploads directory
    secret_file = tmp_path / "secret.txt"
    secret_file.write_text("Secret data")

    # Try path traversal attack with URL encoding
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.delete("/api/documents/%2E%2E%2Fsecret.txt")

    # Should return 404, not delete the file outside uploads
    # FastAPI normalizes the path, so it may return different 404 messages
    assert response.status_code == 404
    assert response.json()["detail"] in ["Document not found", "Not Found"]
    
    # Verify the secret file still exists
    assert secret_file.exists()
