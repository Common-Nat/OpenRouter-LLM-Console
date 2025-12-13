# Backend (FastAPI)

## Quick start
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

## Notes
- SQLite database is created/initialized automatically.
- SSE streaming endpoint: `GET /api/stream?session_id=...&model_id=...`
- OpenRouter key is read from `OPENROUTER_API_KEY`.
