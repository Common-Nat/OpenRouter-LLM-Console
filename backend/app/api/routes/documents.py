from __future__ import annotations

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Path, UploadFile, File
from fastapi.responses import StreamingResponse
from pathlib import Path as PathLib

from ... import repo
from ...core.config import settings
from ...db import get_db
from ...schemas import DocumentOut, DocumentQARequest
from ...services.documents import list_documents, load_document
from ...services.openrouter import process_streaming_response

router = APIRouter(prefix="/documents", tags=["documents"])

# Allowed file extensions for uploads
ALLOWED_EXTENSIONS = {".txt", ".md", ".py", ".js", ".json", ".xml", ".html", ".css", ".java", ".cpp", ".c", ".h", ".ts", ".jsx", ".tsx", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".log", ".csv"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/upload", response_model=DocumentOut)
async def upload_document(file: UploadFile = File(...)):
    """Upload a text document for Q&A analysis"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Validate file extension
    file_ext = PathLib(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    
    # Read file content and check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024:.0f} MB"
        )
    
    # Ensure uploads directory exists
    uploads_dir = PathLib(settings.uploads_dir).expanduser()
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    # Sanitize filename to prevent path traversal
    safe_filename = PathLib(file.filename).name
    file_path = uploads_dir / safe_filename
    
    # If file exists, append a number to make it unique
    if file_path.exists():
        base_name = file_path.stem
        extension = file_path.suffix
        counter = 1
        while file_path.exists():
            safe_filename = f"{base_name}_{counter}{extension}"
            file_path = uploads_dir / safe_filename
            counter += 1
    
    # Write file
    try:
        file_path.write_bytes(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Return document metadata
    stat = file_path.stat()
    from datetime import datetime
    return DocumentOut(
        id=safe_filename,
        name=safe_filename,
        size=stat.st_size,
        created_at=datetime.fromtimestamp(stat.st_mtime).isoformat()
    )


@router.get("", response_model=list[DocumentOut])
async def get_documents():
    return list_documents()


@router.delete("/{document_id}")
async def delete_document(document_id: str = Path(..., description="Identifier of the uploaded document (filename)")):
    """Delete an uploaded document"""
    uploads_dir = PathLib(settings.uploads_dir).expanduser()
    file_path = (uploads_dir / document_id).resolve()
    
    # Prevent path traversal attacks
    try:
        file_path.relative_to(uploads_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        file_path.unlink()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")
    
    return {"message": "Document deleted successfully", "id": document_id}


@router.post("/{document_id}/qa")
async def document_qa(
    payload: DocumentQARequest,
    document_id: str = Path(..., description="Identifier of the uploaded document (filename)"),
    db: aiosqlite.Connection = Depends(get_db),
):
    if not settings.openrouter_api_key:
        raise HTTPException(status_code=400, detail="OPENROUTER_API_KEY is not set")

    try:
        document = load_document(document_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")

    session_id = payload.session_id
    session = None
    if session_id:
        session = await repo.get_session(db, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session_id = await repo.create_session(
            db,
            {
                "session_type": "documents",
                "title": document["name"],
                "profile_id": payload.profile_id,
            },
        )

    session_profile_id = session["profile_id"] if session else payload.profile_id
    resolved_profile_id = payload.profile_id if payload.profile_id is not None else session_profile_id
    profile = None
    if resolved_profile_id is not None:
        profile = await repo.get_profile(db, int(resolved_profile_id))
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

    resolved_temperature = payload.temperature if payload.temperature is not None else (profile["temperature"] if profile else 0.7)
    resolved_max_tokens = payload.max_tokens if payload.max_tokens is not None else (profile["max_tokens"] if profile else 2048)

    resolved_model_id = payload.model_id
    profile_preset = profile.get("openrouter_preset") if profile else None
    if profile_preset:
        preset_suffix = profile_preset if str(profile_preset).startswith("@preset/") else f"@preset/{profile_preset}"
        if "@preset/" not in resolved_model_id:
            resolved_model_id = f"{resolved_model_id}{preset_suffix}"

    history_rows = await repo.list_messages(db, session_id)
    messages = [{"role": r["role"], "content": r["content"]} for r in history_rows]
    if profile and profile.get("system_prompt"):
        messages = [{"role": "system", "content": profile["system_prompt"]}, *messages]

    document_context = (
        f"You are assisting with questions about the uploaded document '{document['name']}'.\n\n"
        f"Document content:\n{document['content']}\n\n"
        "Always answer using only the document content. If the answer is not present, say you don't have enough information."
    )

    messages.extend(
        [
            {"role": "system", "content": document_context},
            {"role": "user", "content": payload.question},
        ]
    )

    await repo.add_message(db, session_id, "user", f"[Document:{document_id}] {payload.question}")

    return StreamingResponse(
        process_streaming_response(
            session_id=session_id,
            resolved_model_id=resolved_model_id,
            messages=messages,
            resolved_temperature=resolved_temperature,
            resolved_max_tokens=resolved_max_tokens,
            resolved_profile_id=resolved_profile_id,
            db=db,
            start_event_data={
                "message": "stream_start",
                "session_id": session_id,
                "document_id": document_id,
            },
        ),
        media_type="text/event-stream",
    )
