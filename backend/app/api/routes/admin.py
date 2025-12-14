"""Admin routes for backup and restore operations."""
import logging
import shutil
import aiosqlite
from datetime import datetime, UTC
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Request, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse

from ...core.config import settings
from ...core.ratelimit import limiter, RATE_LIMITS
from ...db import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


def get_backup_dir() -> Path:
    """Get the backup directory path, create if it doesn't exist."""
    backup_dir = Path("./backups")
    backup_dir.mkdir(exist_ok=True)
    return backup_dir


async def validate_sqlite_db(db_path: Path) -> bool:
    """Validate that a file is a valid SQLite database.
    
    Args:
        db_path: Path to the database file
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute("PRAGMA integrity_check")
            result = await cursor.fetchone()
            return result and result[0] == "ok"
    except Exception as e:
        logger.error(f"SQLite validation failed: {e}")
        return False


@router.get("/admin/backup")
@limiter.limit(RATE_LIMITS["profiles"])  # Reuse profiles rate limit (60/min)
async def download_backup(request: Request):
    """Create and download a timestamped backup of the database.
    
    Creates a copy of console.db with timestamp and returns it as a download.
    The backup is also saved to the ./backups/ directory.
    
    Returns:
        FileResponse: The backup database file
        
    Raises:
        HTTPException: If backup creation fails
    """
    try:
        # Generate timestamped filename
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d_%H-%M-%S")
        backup_name = f"console_backup_{timestamp}.db"
        
        # Create backup directory and copy database
        backup_dir = get_backup_dir()
        backup_path = backup_dir / backup_name
        
        db_path = Path(settings.db_path)
        if not db_path.exists():
            raise HTTPException(
                status_code=404,
                detail={"error": "Database file not found", "error_code": "DB_NOT_FOUND"}
            )
        
        # Copy the database file
        shutil.copy2(db_path, backup_path)
        
        logger.info(
            "Database backup created",
            extra={
                "action": "backup_created",
                "backup_file": backup_name,
                "size_bytes": backup_path.stat().st_size
            }
        )
        
        return FileResponse(
            path=str(backup_path),
            filename=backup_name,
            media_type="application/x-sqlite3",
            headers={
                "Content-Disposition": f'attachment; filename="{backup_name}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Backup creation failed",
            extra={"action": "backup_failed", "error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail={"error": f"Backup failed: {str(e)}", "error_code": "BACKUP_FAILED"}
        )


@router.post("/admin/restore")
@limiter.limit(RATE_LIMITS["document_upload"])  # Reuse upload rate limit (50/min)
async def restore_backup(
    request: Request,
    file: Annotated[UploadFile, File(description="SQLite database backup file")]
):
    """Restore database from uploaded backup file.
    
    Validates the uploaded file is a valid SQLite database, creates a backup
    of the current database, and replaces it with the uploaded file.
    
    **Important:** The server must be restarted after restore for changes to take effect.
    
    Args:
        file: Uploaded .db backup file
        
    Returns:
        dict: Success message with backup location
        
    Raises:
        HTTPException: If validation fails or restore fails
    """
    temp_path = None
    try:
        # Validate file extension
        if not file.filename.endswith('.db'):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid file type. Must be a .db file",
                    "error_code": "INVALID_FILE_TYPE"
                }
            )
        
        # Save uploaded file to temp location
        backup_dir = get_backup_dir()
        temp_path = backup_dir / f"temp_restore_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.db"
        
        # Write uploaded file
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Validate it's a proper SQLite database
        is_valid = await validate_sqlite_db(temp_path)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid SQLite database file",
                    "error_code": "INVALID_DATABASE"
                }
            )
        
        # Backup current database before replacing
        db_path = Path(settings.db_path)
        backup_name = f"console_backup_before_restore_{datetime.now(UTC).strftime('%Y-%m-%d_%H-%M-%S')}.db"
        backup_path = backup_dir / backup_name
        
        if db_path.exists():
            shutil.copy2(db_path, backup_path)
            logger.info(
                "Created safety backup before restore",
                extra={"action": "pre_restore_backup", "backup_file": backup_name}
            )
        
        # Replace current database with uploaded file
        shutil.copy2(temp_path, db_path)
        
        logger.info(
            "Database restored from backup",
            extra={
                "action": "database_restored",
                "source_file": file.filename,
                "safety_backup": backup_name
            }
        )
        
        return {
            "message": "Database restored successfully",
            "safety_backup": backup_name,
            "note": "Server restart recommended for changes to take full effect"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Database restore failed",
            extra={"action": "restore_failed", "error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail={"error": f"Restore failed: {str(e)}", "error_code": "RESTORE_FAILED"}
        )
    finally:
        # Clean up temp file
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")


@router.get("/admin/backups")
@limiter.limit(RATE_LIMITS["profiles"])
async def list_backups(request: Request):
    """List all available backup files.
    
    Returns information about backup files in the ./backups/ directory.
    
    Returns:
        dict: List of backup files with metadata
    """
    try:
        backup_dir = get_backup_dir()
        backups = []
        
        for backup_file in sorted(backup_dir.glob("console_backup_*.db"), reverse=True):
            stat = backup_file.stat()
            backups.append({
                "filename": backup_file.name,
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        return {
            "backups": backups,
            "total": len(backups),
            "backup_directory": str(backup_dir.absolute())
        }
        
    except Exception as e:
        logger.error(
            "Failed to list backups",
            extra={"action": "list_backups_failed", "error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail={"error": f"Failed to list backups: {str(e)}", "error_code": "LIST_FAILED"}
        )
