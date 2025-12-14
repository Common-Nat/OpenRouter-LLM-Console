# Backend (FastAPI)

Self-hosted FastAPI backend for the OpenRouter LLM Console. Provides REST API and Server-Sent Events (SSE) streaming for LLM interactions through OpenRouter.

## Architecture

### Core Technologies
- **FastAPI 0.115+** - Modern async web framework
- **aiosqlite 0.20+** - Async SQLite database adapter
- **httpx 0.27+** - Async HTTP client for OpenRouter API
- **Pydantic 2.10+** - Data validation and settings management
- **uvicorn** - ASGI server with hot reload support

### Key Components

**API Routes** (`app/api/routes/`):
- `health.py` - Health check endpoint
- `models.py` - Model catalog sync and filtering
- `profiles.py` - Profile CRUD operations
- `sessions.py` - Session management
- `messages.py` - Message history
- `stream.py` - SSE streaming endpoint
- `usage.py` - Token usage and cost tracking
- `documents.py` - Document upload and Q&A
- `admin.py` - Backup and restore operations

**Services** (`app/services/`):
- `openrouter.py` - OpenRouter API client with streaming support
- `documents.py` - Document storage and retrieval

**Core** (`app/core/`):
- `config.py` - Pydantic settings from environment variables
- `logging_config.py` - Structured JSON logging with request ID tracking
- `sse.py` - SSE formatting helpers

**Database** (`app/db.py`, `app/repo.py`):
- `db.py` - Schema initialization and migrations
- `repo.py` - Repository pattern for database operations
- `schemas.py` - Pydantic models for API contracts

## Quick Start

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env and set OPENROUTER_API_KEY=sk-or-v1-xxxxx

# Run development server
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

## Environment Variables

Create a `.env` file with the following variables:

```bash
# Required
OPENROUTER_API_KEY=sk-or-v1-xxxxx

# Optional (defaults shown)
APP_TITLE="OpenRouter LLM Console"
APP_ORIGINS="http://localhost:5173,http://localhost:3000"
DB_PATH="./console.db"
UPLOADS_DIR="./uploads"
OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
OPENROUTER_HTTP_REFERER="http://localhost:5173"
OPENROUTER_X_TITLE="Self-Hosted LLM Console"
```

## Database Schema

SQLite database with the following tables:

**models** - OpenRouter model catalog cache
- `id` (TEXT, PK)
- `openrouter_id` (TEXT, UNIQUE)
- `name` (TEXT)
- `context_length` (INTEGER)
- `pricing_prompt`, `pricing_completion` (REAL)
- `is_reasoning` (INTEGER)
- `created_at` (TEXT)

**profiles** - Reusable configuration presets
- `id` (INTEGER, PK, AUTOINCREMENT)
- `name` (TEXT)
- `system_prompt` (TEXT)
- `temperature` (REAL, default 0.7)
- `max_tokens` (INTEGER, default 2048)
- `openrouter_preset` (TEXT)
- `created_at` (TEXT)

**sessions** - Chat/code/documents/playground sessions
- `id` (TEXT, PK)
- `session_type` (TEXT: chat|code|documents|playground)
- `title` (TEXT)
- `profile_id` (INTEGER, FK to profiles)
- `created_at` (TEXT)

**messages** - Message history
- `id` (TEXT, PK)
- `session_id` (TEXT, FK to sessions)
- `role` (TEXT: system|user|assistant|tool)
- `content` (TEXT)
- `created_at` (TEXT)

**usage_logs** - Token usage and cost tracking
- `id` (TEXT, PK)
- `session_id` (TEXT, FK to sessions)
- `profile_id` (INTEGER, FK to profiles)
- `model_id` (TEXT, FK to models)
- `prompt_tokens`, `completion_tokens`, `total_tokens` (INTEGER)
- `cost_usd` (REAL)
- `created_at` (TEXT)

Database is initialized automatically on first startup with foreign key constraints and migrations.

## API Endpoints

### Core Endpoints
- `GET /api/health` - Health check
- `POST /api/models/sync` - Sync OpenRouter model catalog
- `GET /api/models` - List models with filters
- `GET /api/stream` - SSE streaming endpoint

### CRUD Endpoints
- Profiles: `GET`, `POST`, `PUT`, `DELETE` on `/api/profiles`
- Sessions: `GET`, `POST`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}` on `/api/sessions`
- Messages: `GET /api/sessions/{id}/messages`, `POST /api/messages`
- Documents: `POST /api/documents/upload`, `GET`, `POST /{id}/qa`, `DELETE /{id}` on `/api/documents`
- Usage: `GET /api/usage`, `GET /api/usage/summary`

See main README or `/docs` endpoint for full API documentation.

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Verbose output
pytest -v

# Specific test file
pytest tests/test_health.py -v

# With coverage
pytest --cov=app tests/

# Run specific test
pytest tests/test_stream_errors.py::test_stream_missing_api_key -v
```

Test files:
- `test_health.py` - Health endpoint
- `test_db_init.py` - Database initialization
- `test_sessions.py` - Session CRUD
- `test_messages.py` - Message operations
- `test_documents.py` - Document upload/download with security tests
- `test_stream_errors.py` - Streaming error handling
- `test_upload.py` - File upload validation

## Development

### Code Quality

Run linter (Ruff):
```bash
ruff check .
ruff check . --fix  # Auto-fix issues
```

### Logging

Application uses structured JSON logging with request ID tracking:
```python
import logging
logger = logging.getLogger(__name__)

logger.info("Model synced", extra={
    "action": "model_sync",
    "model_count": 150
})
```

Request IDs are automatically added to all logs for tracing.

### Adding New Endpoints

1. Create route in `app/api/routes/`
2. Define Pydantic schemas in `app/schemas.py`
3. Add repository functions in `app/repo.py`
4. Write tests in `tests/`
5. Register router in `app/main.py`

### SSE Streaming Pattern

Use the `sse_data()` helper for proper SSE formatting:

```python
from app.core.sse import sse_data

async def my_stream():
    yield sse_data({"text": "Hello"}, event="token")
    yield sse_data({"done": True}, event="done")
```

## Backup & Restore

Backup and restore functionality is essential for local-first data safety:

### Creating Backups

```bash
# Download database backup via API
curl -O http://localhost:8000/api/admin/backup

# List all backups
curl http://localhost:8000/api/admin/backups
```

Backups are stored in `./backups/` with timestamped filenames like `console_backup_2025-12-14_15-30-45.db`.

### Restoring from Backup

**Via API:**
```bash
curl -X POST http://localhost:8000/api/admin/restore \
  -F "file=@console_backup_2025-12-14_15-30-45.db"
```

**Manual restore:**
1. Stop the server
2. Replace `console.db` with your backup file
3. Restart the server

**Important:** The API creates a safety backup before restoring (stored as `console_backup_before_restore_*.db`).

### Migrating Between Machines

1. Download backup from source machine: `GET /api/admin/backup`
2. Copy backup file to destination machine
3. On destination machine, restore via API or replace `console.db` manually

## Security

- **Path Traversal Protection**: Document operations use `.resolve()` and `.relative_to()` checks
- **Input Validation**: All requests validated via Pydantic models
- **API Key Storage**: OpenRouter key stored server-side only
- **File Upload Limits**: 10MB max, validated extensions
- **Foreign Keys**: Database integrity with CASCADE/SET NULL
- **CORS**: Configurable allowed origins
- **Backup Validation**: SQLite integrity checks on restore operations

## Production Deployment

Example production command:
```bash
gunicorn app.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

Or using uvicorn directly:
```bash
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4
```

## Troubleshooting

**Database locked errors**: SQLite doesn't handle high concurrency well. For production with many users, consider PostgreSQL.

**Streaming timeout**: Default SSE timeout is 300 seconds. Frontend can configure timeout in `useStream` hook.

**OpenRouter errors**: Check logs with request ID for full error details. Common issues:
- Invalid API key
- Rate limiting
- Model not found
- Insufficient credits

**CORS errors**: Ensure frontend URL is in `APP_ORIGINS` environment variable.
