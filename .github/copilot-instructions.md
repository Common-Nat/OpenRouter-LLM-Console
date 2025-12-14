# OpenRouter LLM Console - AI Agent Instructions

## Architecture Overview

This is a **local-first FastAPI + React SPA** that proxies streaming LLM requests through OpenRouter. The backend holds the API key; the browser never sees it. All state lives in SQLite (`console.db`).

**Key components:**
- **Backend** (`backend/`): FastAPI with async SQLite, SSE streaming, structured JSON logging
- **Frontend** (`frontend/`): React SPA with Vite, tabbed UI (Chat/Code/Documents/Playground)
- **Data flow**: Browser → FastAPI → OpenRouter (streaming) → SSE → Browser EventSource

## Critical Patterns

### 1. Database: Async SQLite with aiosqlite

- **Connection:** Use `get_db()` dependency for FastAPI routes ([db.py](backend/app/db.py#L81-L89))
  ```python
  from app.db import get_db
  async def my_route(db: aiosqlite.Connection = Depends(get_db)):
      # db.row_factory is aiosqlite.Row
  ```
- **Schema migration:** Manual `ALTER TABLE` in `_migrate_profiles()` ([db.py](backend/app/db.py#L77-L79))
- **Repository pattern:** All DB queries in [repo.py](backend/app/repo.py), not in routes
- **Foreign keys:** Always `PRAGMA foreign_keys = ON;` in schema and connections

### 2. Streaming via Server-Sent Events (SSE)

- **Backend:** [stream.py](backend/app/api/routes/stream.py) calls `stream_chat_completions()` ([openrouter.py](backend/app/services/openrouter.py#L46-L103)), forwards `data: {...}` lines
- **Frontend:** [useStream.js](frontend/src/hooks/useStream.js) hook wraps EventSource, listens for `event: token`, `event: done`, etc.
- **SSE framing:** Use `sse_data(obj, event="token")` helper ([sse.py](backend/app/core/sse.py#L5-L11))
- **Token accumulation:** Backend accumulates assistant response and stores final message in DB

### 3. OpenRouter Integration

- **Model presets:** Profiles can specify `openrouter_preset` (e.g., `"coding"` → `model@preset/coding`) ([stream.py](backend/app/api/routes/stream.py#L42-L46))
- **Usage tracking:** Parse `usage: {prompt_tokens, completion_tokens}` from streaming chunks, store in `usage_logs` table
- **Headers:** Include `HTTP-Referer` and `X-Title` for OpenRouter analytics ([openrouter.py](backend/app/services/openrouter.py#L14-L24))

### 4. Configuration & Environment

- **Settings:** Pydantic Settings with `.env` file ([config.py](backend/app/core/config.py))
  - Required: `OPENROUTER_API_KEY`
  - Optional: `DB_PATH` (default `./console.db`), `APP_ORIGINS` (CORS)
- **Example file:** Copy [env.example](backend/env.example) to `.env` before running

### 5. Logging & Request Tracing

- **Structured JSON logs:** All logs use `JsonFormatter` with `request_id` context var ([logging_config.py](backend/app/core/logging_config.py))
- **Request ID middleware:** [main.py](backend/app/main.py#L38-L65) sets `request_id_ctx_var`, adds `X-Request-ID` header
- **Log OpenRouter calls:** Use `extra={"action": "openrouter_request", "model": ...}` for traceability

## Developer Workflows

### Running locally
```bash
# Backend (in backend/)
python -m venv .venv && .venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (in frontend/)
npm install
npm run dev  # Vite on localhost:5173
```

### Testing
```bash
# Backend tests (in backend/)
pytest                    # Uses pytest.ini with asyncio_mode=auto
pytest tests/test_health.py -v
```
- Tests use `AsyncClient` from `httpx` to call FastAPI app directly ([test_health.py](backend/tests/test_health.py))
- Database tests use in-memory SQLite or temp file

### Key commands
- **Sync models:** `POST /api/models/sync` fetches OpenRouter catalog, stores in `models` table
- **Run dev:** Backend auto-reloads with `--reload`; frontend HMR via Vite

## Conventions & Gotchas

- **No ORM:** Raw SQL via `aiosqlite`, rows returned as `aiosqlite.Row` (dict-like)
- **UUIDs:** All primary keys except `profiles` use string UUIDs via `uuid.uuid4()` ([repo.py](backend/app/repo.py#L6-L7))
- **Profiles override session:** If `profile_id` is passed to `/stream`, it overrides session's default profile
- **System prompt injection:** If profile has `system_prompt`, it's prepended to message list before sending to OpenRouter ([stream.py](backend/app/api/routes/stream.py#L51-L53))
- **Frontend tabs:** Each tab (`ChatTab`, `CodeTab`, etc.) manages its own session and message state

## File References

- Routes: [backend/app/api/routes/](backend/app/api/routes/)
- Database logic: [backend/app/repo.py](backend/app/repo.py)
- OpenRouter client: [backend/app/services/openrouter.py](backend/app/services/openrouter.py)
- React components: [frontend/src/components/](frontend/src/components/)
- Frontend tabs: [frontend/src/tabs/](frontend/src/tabs/)

## Documentation

For detailed information beyond this quick reference:

**Getting Started:**
- [Main README](../README.md) - Complete project overview, setup, and API reference
- [Backend README](../backend/README.md) - Detailed backend architecture and patterns
- [Changelog](../CHANGELOG.md) - Complete project history and updates

**Features:**
- [Search Feature](../docs/features/search.md) - FTS5-powered message search
- [Caching](../docs/features/caching.md) - In-memory caching implementation
- [Error Handling](../docs/features/error-handling.md) - Streaming error infrastructure
- [Structured Errors](../docs/features/structured-errors.md) - Machine-readable error codes

**Backend Details:**
- [Rate Limiting](../backend/RATE_LIMITING.md) - Complete rate limiting guide
- [Database Migrations](../backend/migrations/README.md) - Migration system

**Testing:**
- [Testing Guide](../TESTING_GUIDE.md) - Comprehensive testing documentation
- [Testing Quick Reference](../TESTING_QUICK_REFERENCE.md) - Command cheat sheet
- [Frontend Tests](../frontend/tests/README.md) - Frontend test suite

**Security:**
- [Path Traversal Fix](../docs/security/path-traversal-fix.md) - Security vulnerability details
