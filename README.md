# OpenRouter LLM Console (self-hosted)

This is a minimal but robust starter project:
- **Backend:** FastAPI + SQLite (async, `aiosqlite`)
- **Frontend:** React (Vite)
- **Streaming:** Server-Sent Events (SSE) from OpenRouter → backend → browser

## Run it
### 1) Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### 2) Frontend
```bash
cd frontend
npm install
npm run dev
```

Then open the UI at `http://localhost:5173`.

## First-use checklist
1. Put your OpenRouter key in `backend/.env` (`OPENROUTER_API_KEY=...`).
2. In the UI, click **Sync** to pull models into SQLite.
3. Select a model and start chatting.

## API surface (backend)
- `GET /api/health`
- `POST /api/models/sync`
- `GET /api/models`
- `POST /api/profiles`
- `GET /api/profiles`
- `POST /api/sessions`
- `GET /api/sessions`
- `GET /api/sessions/{id}/messages`
- `POST /api/messages`
- `GET /api/stream` (SSE)

## Tests
```bash
cd backend
pytest -q
```

## License
This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
