# OpenRouter LLM Console

A self-hosted, local-first multi-model LLM console for power users. This application provides a tabbed web interface (Chat, Code, Documents, Playground) for working with many different LLMs through the OpenRouter API, with streaming responses, reusable profiles, and session history.

All traffic to OpenRouter goes through your own backend. The browser never holds or sends the OpenRouter API key directly.

## Features

### Multi-model via OpenRouter
- Access GPT-style, Claude-style, and other models through a single OpenAI-compatible API
- Model selector with filters (e.g., free models, large context, reasoning models)
- Real-time model synchronization from OpenRouter's model catalog

### Local-first & Self-hosted
- FastAPI backend with your API key stored securely in environment variables
- SQLite database for models, profiles, sessions, and messages – no external database required
- All data stored locally on your machine

### Tabbed Power-user Console
- **Chat** – Classic chat UI with model/profile selector and streaming output
- **Code** – Code-oriented prompting with monospace output and coding-friendly defaults
- **Documents** – Upload text/markdown files and run Q&A or analysis
- **Playground** – Raw request builder for OpenRouter with full control over parameters

### Streaming Responses
- Backend calls OpenRouter with `stream: true` and exposes its own `/api/stream` SSE endpoint
- Frontend uses EventSource to render tokens as they arrive in real-time

### Profiles (Reusable Presets)
- Save reusable profiles containing: system prompt, temperature, max tokens, and OpenRouter preset
- Profiles can use OpenRouter presets (e.g., `@preset/coding` or `model@preset/assistant`)
- Easily switch between different configurations for various tasks

### Usage Tracking
- Track token usage and costs per session and model
- View usage statistics and cost breakdown

## Architecture

### Frontend
React single-page application (SPA) built with Vite, featuring:
- Tab navigation: Chat / Code / Documents / Playground
- Model selector with real-time filtering
- Temperature and max tokens controls
- Chat interface with streaming output and session history
- Document upload and Q&A interface

### Backend
FastAPI application using:
- **httpx** for outbound OpenRouter API calls
- **SQLite** (via aiosqlite) for async database operations
- **Server-Sent Events (SSE)** for streaming responses
- **CORS middleware** for local development

Key API endpoints:
- `POST /api/models/sync` – Fetches and caches OpenRouter's model catalog
- `GET /api/models` – Returns cached models with optional filters
- `GET /api/profiles` – List all profiles
- `POST /api/profiles` – Create new profiles
- `POST /api/sessions` – Create chat/code/documents/playground sessions
- `GET /api/sessions/{id}/messages` – Retrieve message history
- `POST /api/messages` – Create new messages
- `GET /api/stream` – SSE endpoint for streaming responses
- `GET /api/usage` – Token usage and cost tracking
- `POST /api/documents/upload` – Upload documents
- `POST /api/documents/{id}/qa` – Ask questions about documents

### Database (SQLite)
Main tables:
- **models** – Cached OpenRouter models with pricing and capabilities
- **profiles** – Reusable configuration presets
- **sessions** – Chat/code/documents/playground sessions
- **messages** – Message history for all sessions
- **usage_logs** – Token usage and cost tracking per session

## Prerequisites

- **Python 3.10+** (for backend)
- **Node.js + npm** (for frontend)
- **OpenRouter account and API key** – Get yours at [openrouter.ai](https://openrouter.ai)

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
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the `backend` directory with your OpenRouter API key:
```bash
OPENROUTER_API_KEY=sk-or-v1-xxxxx
```

Optional environment variables:
```bash
APP_TITLE="OpenRouter LLM Console"
APP_ORIGINS="http://localhost:5173"
DB_PATH="./console.db"
UPLOADS_DIR="./uploads"
OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
OPENROUTER_HTTP_REFERER="http://localhost:5173"
OPENROUTER_X_TITLE="Self-Hosted LLM Console"
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
- Upload text or markdown files (`.txt`, `.md`)
- Ask questions about uploaded documents
- Get AI-powered summaries and analysis
- Document content is embedded in the context for accurate responses

### Playground Tab
- Build raw OpenRouter API requests
- Full control over model, system prompt, temperature, top_p, and other parameters
- Inspect raw JSON requests and responses for debugging

## API Reference

### Health
- `GET /api/health` – Health check endpoint

### Models
- `POST /api/models/sync` – Fetch and cache models from OpenRouter
- `GET /api/models` – List cached models with optional filters

### Profiles
- `GET /api/profiles` – List all profiles
- `POST /api/profiles` – Create a new profile
- `PUT /api/profiles/{id}` – Update a profile
- `DELETE /api/profiles/{id}` – Delete a profile

### Sessions
- `GET /api/sessions` – List all sessions
- `POST /api/sessions` – Create a new session
- `GET /api/sessions/{id}` – Get session details
- `DELETE /api/sessions/{id}` – Delete a session

### Messages
- `GET /api/sessions/{id}/messages` – Get messages for a session
- `POST /api/messages` – Create a new message

### Streaming
- `GET /api/stream` – Server-Sent Events endpoint for streaming responses

### Usage
- `GET /api/usage` – Get token usage statistics and costs

### Documents
- `POST /api/documents/upload` – Upload a document
- `GET /api/documents` – List uploaded documents
- `POST /api/documents/{id}/qa` – Ask questions about a document
- `DELETE /api/documents/{id}` – Delete a document

## Testing

Run the backend test suite:
```bash
cd backend
pytest -q
```

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
