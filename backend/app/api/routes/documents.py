from __future__ import annotations

import asyncio
import json

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Path, UploadFile, File
from fastapi.responses import StreamingResponse
from pathlib import Path as PathLib

from ... import repo
from ...core.config import settings
from ...core.logging_config import request_id_ctx_var
from ...core.sse import sse_data
from ...db import get_db
from ...schemas import DocumentOut, DocumentQARequest
from ...services.documents import list_documents, load_document
from ...services.openrouter import OpenRouterError, stream_chat_completions

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

    async def gen():
        assistant_accum = ""
        usage_counts = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        yield sse_data({"message": "stream_start", "session_id": session_id, "document_id": document_id}, event="start")

        try:
            async for line in stream_chat_completions(
                model=resolved_model_id,
                messages=messages,
                temperature=resolved_temperature,
                max_tokens=resolved_max_tokens,
            ):
                if not line:
                    continue
                if line.startswith("data: "):
                    chunk = line[len("data: "):].strip()
                else:
                    chunk = line.strip()

                if chunk == "[DONE]":
                    break

                token = None
                obj = None

                try:
                    obj = json.loads(chunk)
                    delta = (((obj.get("choices") or [{}])[0]).get("delta") or {})

                    usage = obj.get("usage") or delta.get("usage") or ((obj.get("choices") or [{}])[0].get("usage"))
                    if isinstance(usage, dict):
                        usage_counts["prompt_tokens"] = int(usage.get("prompt_tokens") or usage_counts["prompt_tokens"] or 0)
                        usage_counts["completion_tokens"] = int(
                            usage.get("completion_tokens") or usage_counts["completion_tokens"] or 0
                        )
                        usage_counts["total_tokens"] = int(
                            usage.get("total_tokens")
                            or usage_counts["total_tokens"]
                            or usage_counts["prompt_tokens"] + usage_counts["completion_tokens"]
                        )

                    content = delta.get("content")
                    content_parts = []
                    if isinstance(content, str):
                        content_parts.append(content)
                    elif isinstance(content, list):
                        for item in content:
                            if isinstance(item, str):
                                content_parts.append(item)
                            elif isinstance(item, dict):
                                item_text = item.get("text") or item.get("content")
                                if isinstance(item_text, str):
                                    content_parts.append(item_text)

                    token = "".join(content_parts)

                    if not token:
                        tool_calls = delta.get("tool_calls") or []
                        tool_text_parts = []
                        if isinstance(tool_calls, list):
                            for call in tool_calls:
                                if not isinstance(call, dict):
                                    continue
                                if isinstance(call.get("function"), dict):
                                    arguments = call["function"].get("arguments")
                                    if isinstance(arguments, str):
                                        tool_text_parts.append(arguments)
                                call_text = call.get("text")
                                if isinstance(call_text, str):
                                    tool_text_parts.append(call_text)

                        token = "".join(tool_text_parts)
                except Exception:
                    obj = None

                if token:
                    assistant_accum += token
                    yield sse_data({"token": token}, event="token")
                else:
                    yield sse_data({"raw": chunk}, event="token")
        except asyncio.CancelledError:
            return
        except OpenRouterError as e:
            yield sse_data(
                {
                    "status": e.status_code,
                    "message": str(e),
                    "request_id": request_id_ctx_var.get("-"),
                },
                event="error",
            )
            return
        except Exception as e:
            yield sse_data(
                {"status": 500, "message": str(e), "request_id": request_id_ctx_var.get("-")},
                event="error",
            )
            return
        else:
            if assistant_accum.strip():
                await repo.add_message(db, session_id, "assistant", assistant_accum)

            await repo.insert_usage_log(
                db,
                session_id=session_id,
                model_id=resolved_model_id,
                prompt_tokens=usage_counts["prompt_tokens"],
                completion_tokens=usage_counts["completion_tokens"],
                profile_id=resolved_profile_id,
            )

            yield sse_data(
                {
                    "message": "stream_end",
                    "assistant": assistant_accum,
                    "usage": usage_counts,
                    "session_id": session_id,
                    "document_id": document_id,
                },
                event="done",
            )

    return StreamingResponse(gen(), media_type="text/event-stream")
