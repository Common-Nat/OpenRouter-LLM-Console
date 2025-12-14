"""Tests for admin backup/restore endpoints."""
import pytest
import aiosqlite
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings


@pytest.mark.asyncio
async def test_backup_creates_file():
    """Test that backup endpoint creates a downloadable file."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/admin/backup")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/x-sqlite3"
        assert "console_backup_" in response.headers["content-disposition"]
        assert len(response.content) > 0  # File has content


@pytest.mark.asyncio
async def test_list_backups():
    """Test that list backups endpoint returns backup info."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create a backup first
        await ac.get("/api/admin/backup")
        
        # List backups
        response = await ac.get("/api/admin/backups")
        
        assert response.status_code == 200
        data = response.json()
        assert "backups" in data
        assert "total" in data
        assert data["total"] >= 1
        assert isinstance(data["backups"], list)
        
        # Check backup structure
        if data["backups"]:
            backup = data["backups"][0]
            assert "filename" in backup
            assert "size_bytes" in backup
            assert "created_at" in backup


@pytest.mark.asyncio
async def test_restore_invalid_file_type():
    """Test that restore rejects non-.db files."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Try to upload a text file
        files = {"file": ("test.txt", b"not a database", "text/plain")}
        response = await ac.post("/api/admin/restore", files=files)
        
        assert response.status_code == 400
        assert "error_code" in response.json()
        assert response.json()["error_code"] == "INVALID_FILE_TYPE"


@pytest.mark.asyncio
async def test_restore_invalid_database():
    """Test that restore rejects invalid SQLite files."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Try to upload a fake .db file with invalid content
        files = {"file": ("fake.db", b"not a real SQLite database file", "application/x-sqlite3")}
        response = await ac.post("/api/admin/restore", files=files)
        
        assert response.status_code == 400
        assert "error_code" in response.json()
        assert response.json()["error_code"] == "INVALID_DATABASE"


@pytest.mark.asyncio
async def test_backup_restore_roundtrip(tmp_path):
    """Test full backup and restore cycle."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create a backup
        backup_response = await ac.get("/api/admin/backup")
        assert backup_response.status_code == 200
        backup_content = backup_response.content
        
        # 2. Verify the backup is a valid SQLite database
        temp_db = tmp_path / "test_backup.db"
        temp_db.write_bytes(backup_content)
        
        async with aiosqlite.connect(temp_db) as db:
            cursor = await db.execute("PRAGMA integrity_check")
            result = await cursor.fetchone()
            assert result[0] == "ok"
        
        # 3. Test restore with the backup
        files = {"file": ("backup.db", backup_content, "application/x-sqlite3")}
        restore_response = await ac.post("/api/admin/restore", files=files)
        
        assert restore_response.status_code == 200
        data = restore_response.json()
        assert "message" in data
        assert "safety_backup" in data
        assert "successfully" in data["message"].lower()
