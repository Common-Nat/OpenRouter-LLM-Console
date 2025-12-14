from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List

from ..core.config import settings


def _uploads_dir() -> Path:
    path = Path(settings.uploads_dir).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_documents() -> List[Dict[str, str]]:
    docs: List[Dict[str, str]] = []
    for file_path in _uploads_dir().iterdir():
        if not file_path.is_file():
            continue
        stat = file_path.stat()
        docs.append(
            {
                "id": file_path.name,
                "name": file_path.name,
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }
        )

    docs.sort(key=lambda x: x["created_at"], reverse=True)
    return docs


def load_document(document_id: str) -> Dict[str, str]:
    # Prevent path traversal attacks
    uploads_dir = _uploads_dir()
    file_path = (uploads_dir / document_id).resolve()
    
    # Ensure the resolved path is within the uploads directory
    try:
        file_path.relative_to(uploads_dir.resolve())
    except ValueError:
        raise FileNotFoundError(f"Document not found: {document_id}")
    
    if not file_path.is_file():
        raise FileNotFoundError(f"Document not found: {document_id}")

    stat = file_path.stat()
    content = file_path.read_text(encoding="utf-8", errors="ignore")

    return {
        "id": file_path.name,
        "name": file_path.name,
        "size": stat.st_size,
        "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "content": content,
    }
