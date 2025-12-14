import aiosqlite
from pathlib import Path
from .core.config import settings

INIT_SQL = """PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS models (
  id TEXT PRIMARY KEY,
  openrouter_id TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  context_length INTEGER,
  pricing_prompt REAL,
  pricing_completion REAL,
  is_reasoning INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS profiles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  system_prompt TEXT,
  temperature REAL DEFAULT 0.7,
  max_tokens INTEGER DEFAULT 2048,
  openrouter_preset TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  session_type TEXT NOT NULL,
  title TEXT,
  profile_id INTEGER,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS messages (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  role TEXT NOT NULL CHECK(role IN ('system','user','assistant','tool')),
  content TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_session_created ON messages(session_id, created_at);

CREATE TABLE IF NOT EXISTS usage_logs (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  profile_id INTEGER,
  model_id TEXT,
  prompt_tokens INTEGER NOT NULL DEFAULT 0,
  completion_tokens INTEGER NOT NULL DEFAULT 0,
  total_tokens INTEGER NOT NULL DEFAULT 0,
  cost_usd REAL NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
  FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE SET NULL,
  FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_usage_logs_session_created ON usage_logs(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_usage_logs_model_created ON usage_logs(model_id, created_at);
"""

async def init_db() -> None:
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(settings.db_path) as db:
        await db.executescript(INIT_SQL)
        await _migrate_profiles(db)
        await db.commit()


async def _migrate_profiles(db: aiosqlite.Connection) -> None:
    cur = await db.execute("PRAGMA table_info(profiles)")
    columns = [row[1] for row in await cur.fetchall()]
    if "openrouter_preset" not in columns:
        await db.execute("ALTER TABLE profiles ADD COLUMN openrouter_preset TEXT")

async def get_db():
    db = await aiosqlite.connect(settings.db_path)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON;")
    try:
        yield db
    finally:
        await db.close()
