"""Tests for document upload and delete endpoints"""
from __future__ import annotations

import io
from pathlib import Path

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.config import settings


@pytest.mark.asyncio
async def test_upload_document_success():
    """Test successful document upload"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        content = b"This is a test document content"
        files = {"file": ("test_doc.txt", io.BytesIO(content), "text/plain")}
        
        response = await ac.post("/api/documents/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_doc.txt"
        assert data["size"] == len(content)
        assert "created_at" in data
        
        # Verify file was actually created
        uploads_dir = Path(settings.uploads_dir).expanduser()
        file_path = uploads_dir / "test_doc.txt"
        assert file_path.exists()
        
        # Cleanup
        file_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_upload_document_invalid_extension():
    """Test upload with invalid file extension"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        content = b"executable content"
        files = {"file": ("malware.exe", io.BytesIO(content), "application/octet-stream")}
        
        response = await ac.post("/api/documents/upload", files=files)
        
        assert response.status_code == 400
    # HTTPException returns either dict or string, handle both
    resp_data = response.json()
    error_msg = resp_data if isinstance(resp_data, str) else resp_data.get("detail", "")
    assert "Invalid file type" in error_msg
async def test_upload_document_too_large():
    """Test upload with file exceeding size limit"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create content larger than 10MB
        content = b"x" * (11 * 1024 * 1024)
        files = {"file": ("large_file.txt", io.BytesIO(content), "text/plain")}
        
        response = await ac.post("/api/documents/upload", files=files)
        
        assert response.status_code == 400
    # HTTPException returns either dict or string, handle both
    resp_data = response.json()
    error_msg = resp_data if isinstance(resp_data, str) else resp_data.get("detail", "")
    assert "File too large" in error_msg
async def test_upload_document_duplicate_name():
    """Test uploading file with duplicate name gets renamed"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        content1 = b"First file content"
        content2 = b"Second file content"
        
        files1 = {"file": ("duplicate.txt", io.BytesIO(content1), "text/plain")}
        response1 = await ac.post("/api/documents/upload", files=files1)
        assert response1.status_code == 200
        
        files2 = {"file": ("duplicate.txt", io.BytesIO(content2), "text/plain")}
        response2 = await ac.post("/api/documents/upload", files=files2)
        assert response2.status_code == 200
        
        data2 = response2.json()
        assert data2["name"] == "duplicate_1.txt"
        
        # Cleanup
        uploads_dir = Path(settings.uploads_dir).expanduser()
        (uploads_dir / "duplicate.txt").unlink(missing_ok=True)
        (uploads_dir / "duplicate_1.txt").unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_delete_document_success():
    """Test successful document deletion"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # First upload a document
        content = b"Document to delete"
        files = {"file": ("delete_me.txt", io.BytesIO(content), "text/plain")}
        upload_response = await ac.post("/api/documents/upload", files=files)
        assert upload_response.status_code == 200
        
        # Now delete it
        delete_response = await ac.delete("/api/documents/delete_me.txt")
        assert delete_response.status_code == 200
        assert "deleted successfully" in delete_response.json()["message"]
        
        # Verify file is gone
        uploads_dir = Path(settings.uploads_dir).expanduser()
        file_path = uploads_dir / "delete_me.txt"
        assert not file_path.exists()


@pytest.mark.asyncio
async def test_delete_document_not_found():
    """Test deleting non-existent document"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.delete("/api/documents/nonexistent.txt")
        assert response.status_code == 404
        error_data = response.json()
        assert error_data["error_code"] == "DOCUMENT_NOT_FOUND"
        assert "not found" in error_data["message"].lower()


@pytest.mark.asyncio
async def test_delete_document_path_traversal():
    """Test that path traversal is prevented in delete endpoint"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.delete("/api/documents/../../../etc/passwd")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
