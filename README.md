# OpenRouter LLM Console

A self-hosted, local-first multi-model LLM console for power users. This application provides a tabbed web interface (Chat, Code, Documents, Playground) for working with many different LLMs through the OpenRouter API, with streaming responses, reusable profiles, and session history.

All traffic to OpenRouter goes through your own backend. The browser never holds or sends the OpenRouter API key directly.

## Features

### Multi-model via OpenRouter
- Access GPT-4, Claude, Gemini, Llama, and 100+ other models through a single OpenAI-compatible API
- Model selector with filters by reasoning capability, context length, and pricing
- Real-time model synchronization from OpenRouter's model catalog
- Support for OpenRouter presets (e.g., `@preset/coding`, `@preset/assistant`)

### Local-first & Self-hosted
- FastAPI backend with your API key stored securely in environment variables
- SQLite database for models, profiles, sessions, messages, and usage logs – no external database required
- All data stored locally on your machine
- No telemetry, no cloud dependencies

### Tabbed Power-user Console
- **Chat** – Classic chat UI with model/profile selector and streaming output
- **Code** – Code-oriented prompting with monospace output and coding-friendly defaults
- **Documents** – Upload text files (`.txt`, `.md`, `.py`, `.json`, etc.) and run Q&A or analysis with document context
- **Playground** – Raw request builder for OpenRouter with full control over parameters

### Streaming Responses via SSE
- Backend calls OpenRouter with `stream: true` and exposes its own `/api/stream` SSE endpoint
- Frontend uses EventSource to render tokens as they arrive in real-time
- Comprehensive error handling with timeout protection and graceful degradation
- Request ID tracking for debugging and traceability

### Profiles (Reusable Presets)
- Save reusable profiles containing: name, system prompt, temperature, max tokens, and OpenRouter preset
- Profiles can override session settings for quick context switching
- Easily switch between different configurations for various tasks (coding, creative writing, analysis, etc.)

### Usage Tracking & Cost Analysis
- Track prompt and completion tokens per session and model
- Calculate costs based on OpenRouter pricing
- View usage statistics and cost breakdown by model
- Export usage data for billing and analysis

## Architecture

### Frontend
React single-page application (SPA) built with Vite 5, featuring:
- Tab navigation: Chat / Code / Documents / Playground
- Model selector with real-time filtering (by reasoning, context, price)
- Profile manager for creating and managing reusable configuration presets
- Temperature and max tokens controls per session
- Streaming chat interface with SSE (EventSource)
- Document upload with file type validation (supports `.txt`, `.md`, `.py`, `.js`, `.json`, and many more)
- Usage panel showing token consumption and costs
- Session history management

### Backend
FastAPI 0.115+ application using:
- **httpx** for async HTTP client to OpenRouter API
- **aiosqlite** for async SQLite database operations
- **Server-Sent Events (SSE)** for streaming LLM responses
- **CORS middleware** for local development
- **Pydantic 2.10+** for request/response validation and settings management
- **Structured JSON logging** with request ID tracking for production-grade observability
- **Path traversal protection** for document uploads and access

Key API endpoints:
- `GET /api/health` – Health check
- `POST /api/models/sync` – Fetches and caches OpenRouter's model catalog
- `GET /api/models` – Returns cached models with optional filters (`reasoning`, `min_context`, `max_price`)
- `GET /api/profiles` – List all profiles
- `POST /api/profiles` – Create new profile
- `PUT /api/profiles/{id}` – Update profile
- `DELETE /api/profiles/{id}` – Delete profile
- `GET /api/sessions` – List all sessions with optional type filter
- `POST /api/sessions` – Create chat/code/documents/playground session
- `GET /api/sessions/{id}` – Get session details
- `PUT /api/sessions/{id}` – Update session (title, profile)
- `DELETE /api/sessions/{id}` – Delete session
- `GET /api/sessions/{id}/messages` – Retrieve message history
- `POST /api/messages` – Create new message
- `GET /api/stream` – SSE endpoint for streaming responses (query params: `session_id`, `model_id`, `profile_id`, `temperature`, `max_tokens`)
- `GET /api/usage` – Token usage and cost tracking with optional filters
- `GET /api/usage/summary` – Usage summary grouped by model
- `POST /api/documents/upload` – Upload document (10MB max, validated file types)
- `GET /api/documents` – List uploaded documents
- `POST /api/documents/{id}/qa` – Ask questions about a document
- `DELETE /api/documents/{id}` – Delete document

### Database (SQLite)
Main tables:
- **models** – Cached OpenRouter models with `openrouter_id`, `name`, `context_length`, `pricing_prompt`, `pricing_completion`, `is_reasoning`
- **profiles** – Reusable configuration presets with `name`, `system_prompt`, `temperature`, `max_tokens`, `openrouter_preset`
- **sessions** – Chat/code/documents/playground sessions with `session_type`, `title`, `profile_id` (foreign key)
- **messages** – Message history with `session_id`, `role` (system/user/assistant/tool), `content`
- **usage_logs** – Token usage and cost tracking with `session_id`, `profile_id`, `model_id`, `prompt_tokens`, `completion_tokens`, `total_tokens`, `cost_usd`

All tables use foreign keys with proper cascade/set null behavior. Database schema is initialized automatically on first startup with migration support.

## Prerequisites

- **Python 3.10+** (for backend) – Tested with Python 3.9+, recommended 3.10+
- **Node.js 18+** and **npm** (for frontend)
- **OpenRouter account and API key** – Get yours at [openrouter.ai](https://openrouter.ai)
- **Git** (for cloning the repository)

## Setup

### 1. Clone the repository
```bash
git clone https://github.com/Common-Nat/OpenRouter-LLM-Console.git
cd OpenRouter-LLM-Console
```

### 2. Backend setup (FastAPI + SQLite)
```bash
cd backend
python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate

pip install -r requirements.txt
```

Create a `.env` file in the `backend` directory (use `env.example` as template):
```bash
# Required
OPENROUTER_API_KEY=sk-or-v1-xxxxx

# Optional (with defaults shown)
APP_TITLE="OpenRouter LLM Console"
APP_ORIGINS="http://localhost:5173,http://localhost:3000"
DB_PATH="./console.db"
UPLOADS_DIR="./uploads"
OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
OPENROUTER_HTTP_REFERER="http://localhost:5173"
OPENROUTER_X_TITLE="Self-Hosted LLM Console"
```

Or simply copy the example file:
```bash
cp env.example .env
# Then edit .env and add your OPENROUTER_API_KEY
```

Run the backend:
```bash
uvicorn app.main:app --reload --port 8000
```

The database schema will be initialized automatically on first startup.

### 3. Frontend setup (React)
```bash
cd frontend
npm install
npm run dev
```

Open your browser to the URL displayed by Vite (typically `http://localhost:5173`).

### 4. First-time setup
1. In the UI, click **Sync Models** to pull the latest models from OpenRouter
2. Create a profile with your preferred settings, or use a model directly
3. Start chatting!

## Usage

### Chat Tab
- Select a model or profile from the dropdown
- Type messages and receive streaming responses
- Session history is automatically saved to SQLite

### Code Tab
- Use coding-optimized profiles or models
- Ask for code with syntax highlighting and monospace formatting
- Easy code copying from responses

### Documents Tab
- Upload text files with various extensions: `.txt`, `.md`, `.py`, `.js`, `.json`, `.xml`, `.html`, `.css`, `.java`, `.cpp`, `.c`, `.h`, `.ts`, `.jsx`, `.tsx`, `.yaml`, `.yml`, `.toml`, `.ini`, `.cfg`, `.conf`, `.log`, `.csv`, and more
- Maximum file size: 10 MB
- Ask questions about uploaded documents with full document context
- Get AI-powered summaries and analysis
- Document content is embedded in the context for accurate responses
- Delete documents when no longer needed

### Playground Tab
- Build raw OpenRouter API requests
- Full control over model, system prompt, temperature, top_p, and other parameters
- Inspect raw JSON requests and responses for debugging

## API Reference

### Health
- `GET /api/health` – Health check endpoint (returns `{"status": "ok"}`)

### Models
- `POST /api/models/sync` – Fetch and cache models from OpenRouter (returns count of synced models)
- `GET /api/models` – List cached models with optional query params:
  - `reasoning` (bool): Filter reasoning-capable models
  - `min_context` (int): Minimum context length
  - `max_price` (float): Maximum price per token

### Profiles
- `GET /api/profiles` – List all profiles
- `POST /api/profiles` – Create a new profile (requires `name`, optional: `system_prompt`, `temperature`, `max_tokens`, `openrouter_preset`)
- `PUT /api/profiles/{id}` – Update a profile
- `DELETE /api/profiles/{id}` – Delete a profile

### Sessions
- `GET /api/sessions` – List all sessions (optional query param: `session_type`)
- `POST /api/sessions` – Create a new session (requires `session_type`: chat/code/documents/playground, optional: `title`, `profile_id`)
- `GET /api/sessions/{id}` – Get session details
- `PUT /api/sessions/{id}` – Update session (title or profile_id)
- `DELETE /api/sessions/{id}` – Delete a session and all associated messages

### Messages
- `GET /api/sessions/{id}/messages` – Get messages for a session (chronologically ordered)
- `POST /api/messages` – Create a new message (requires `session_id`, `role`, `content`)

### Streaming
- `GET /api/stream` – Server-Sent Events endpoint for streaming LLM responses
  - Query params: `session_id` (required), `model_id` (required), `profile_id` (optional), `temperature` (optional), `max_tokens` (optional)
  - Events: `token` (delta text), `done` (final payload with usage), `error` (error details)
  - Returns `text/event-stream` with proper SSE formatting

### Usage
- `GET /api/usage` – Get token usage logs with optional filters (`session_id`, `model_id`, `start_date`, `end_date`)
- `GET /api/usage/summary` – Get usage summary grouped by model (total tokens and costs)

### Documents
- `POST /api/documents/upload` – Upload a document (multipart/form-data, max 10MB, validated extensions)
- `GET /api/documents` – List uploaded documents with metadata
- `POST /api/documents/{id}/qa` – Ask questions about a document (requires `question`, `model_id`, optional: `session_id`, `profile_id`, `temperature`, `max_tokens`)
- `DELETE /api/documents/{id}` – Delete a document from uploads directory

## Testing

Run the backend test suite:
```bash
cd backend

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_health.py -v

# Run with coverage
pytest --cov=app tests/
```

Test suite includes:
- Health endpoint tests
- Database initialization tests
- Model sync and filtering tests
- Profile CRUD operations
- Session and message management
- Document upload and Q&A with path traversal protection
- Streaming error handling (missing API key, invalid session, OpenRouter errors)

## Security Features

- **Path Traversal Protection**: Document upload and access endpoints use path resolution and boundary checking to prevent directory traversal attacks
- **API Key Security**: OpenRouter API key is stored server-side only, never exposed to browser
- **Input Validation**: All API endpoints use Pydantic models for request validation
- **File Upload Validation**: File type whitelist and size limits (10MB) on document uploads
- **CORS Configuration**: Configurable allowed origins for cross-origin requests
- **Foreign Key Constraints**: Database integrity enforced with proper cascading deletes

## Production Deployment

For production deployment, consider:

1. **Environment Variables**:
   - Set `APP_ORIGINS` to your production domain(s)
   - Use a secure `OPENROUTER_API_KEY`
   - Configure `DB_PATH` to a persistent volume
   - Set `UPLOADS_DIR` to a secure file storage location

2. **Database**:
   - The SQLite database is suitable for single-user or small team deployments
   - For larger deployments, consider migrating to PostgreSQL (requires code changes)
   - Regular backups of `console.db` recommended

3. **Web Server**:
   - Use a production ASGI server like `gunicorn` with `uvicorn` workers
   - Example: `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000`

4. **Frontend**:
   - Build production bundle: `cd frontend && npm run build`
   - Serve static files with nginx or similar
   - Configure API proxy to backend

5. **Security**:
   - Use HTTPS/TLS for production
   - Set up rate limiting on API endpoints
   - Configure firewall rules
   - Regular security updates for dependencies

## Troubleshooting

### Backend won't start
- Verify Python 3.10+ is installed: `python --version`
- Check `.env` file exists with `OPENROUTER_API_KEY`
- Ensure virtual environment is activated
- Check for port conflicts on 8000

### Frontend won't connect
- Verify backend is running on `http://localhost:8000`
- Check browser console for CORS errors
- Verify `APP_ORIGINS` in `.env` includes frontend URL

### Streaming not working
- Check OpenRouter API key is valid
- Verify model ID exists (run `POST /api/models/sync` first)
- Check browser DevTools Network tab for SSE connection
- Review backend logs for error details (request ID included)

### Database errors
- Delete `console.db` to reset (will lose all data)
- Check file permissions on database file
- Verify `DB_PATH` directory is writable

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run `pytest` and `ruff check` to verify
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/), [React](https://react.dev/), and [Vite](https://vitejs.dev/)
- Powered by [OpenRouter](https://openrouter.ai/) for unified LLM access
- Inspired by the need for a local-first, privacy-focused LLM console

Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

## Development

### Backend Development
The backend uses:
- **FastAPI** for the web framework
- **Pydantic** for data validation
- **aiosqlite** for async SQLite operations
- **httpx** for async HTTP requests
- **pytest** for testing

Linting and formatting:
```bash
cd backend
ruff check app tests
ruff format app tests
```

### Frontend Development
The frontend uses:
- **React 18** for the UI
- **Vite** for fast development and building
- **Native fetch API** and **EventSource** for API calls

Build for production:
```bash
cd frontend
npm run build
npm run preview
```

## Notes & Limitations

- This is designed for local self-hosting and manual experimentation, not as a multi-tenant SaaS
- No user accounts or authentication are implemented; everything runs as a single local user
- Only text/markdown documents are supported in the Documents tab
- All data is stored locally in SQLite; no cloud sync

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Acknowledgments

- Built with [OpenRouter](https://openrouter.ai) for multi-model LLM access
- Powered by [FastAPI](https://fastapi.tiangolo.com/) and [React](https://react.dev/)
