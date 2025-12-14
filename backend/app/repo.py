from __future__ import annotations
import uuid
from typing import Any, Dict, List, Optional
import aiosqlite
from .core.cache import profile_cache, model_cache

def _uuid() -> str:
    return str(uuid.uuid4())

async def upsert_models(db: aiosqlite.Connection, rows: List[Dict[str, Any]]) -> int:
    # rows: {openrouter_id, name, context_length, pricing_prompt, pricing_completion, is_reasoning}
    count = 0
    for r in rows:
        # Check if model already exists to preserve its UUID
        cur = await db.execute(
            "SELECT id FROM models WHERE openrouter_id = ?",
            (r["openrouter_id"],)
        )
        existing = await cur.fetchone()
        model_id = existing["id"] if existing else _uuid()
        
        await db.execute(
            """            INSERT INTO models(id, openrouter_id, name, context_length, pricing_prompt, pricing_completion, is_reasoning)
            VALUES(?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(openrouter_id) DO UPDATE SET
              name=excluded.name,
              context_length=excluded.context_length,
              pricing_prompt=excluded.pricing_prompt,
              pricing_completion=excluded.pricing_completion,
              is_reasoning=excluded.is_reasoning
            """,
            (
                model_id,
                r["openrouter_id"],
                r["name"],
                r.get("context_length"),
                r.get("pricing_prompt"),
                r.get("pricing_completion"),
                1 if r.get("is_reasoning") else 0,
            ),
        )
        count += 1
    await db.commit()
    # Invalidate model cache after sync
    model_cache.clear()
    return count

async def list_models(db: aiosqlite.Connection, *, reasoning: Optional[bool]=None, max_price: Optional[float]=None, min_context: Optional[int]=None) -> List[aiosqlite.Row]:
    # Build cache key from filters
    cache_key = f"models_r{reasoning}_p{max_price}_c{min_context}"
    cached = model_cache.get(cache_key)
    if cached is not None:
        return cached
    
    q = "SELECT id, openrouter_id, name, context_length, pricing_prompt, pricing_completion, is_reasoning FROM models WHERE 1=1"
    args: List[Any] = []
    if reasoning is not None:
        q += " AND is_reasoning = ?"
        args.append(1 if reasoning else 0)
    if min_context is not None:
        q += " AND (context_length IS NULL OR context_length >= ?)"
        args.append(min_context)
    if max_price is not None:
        # compare prompt+completion as rough upper bound if present
        q += " AND (pricing_prompt IS NULL OR pricing_prompt <= ?) AND (pricing_completion IS NULL OR pricing_completion <= ?)"
        args.extend([max_price, max_price])
    q += " ORDER BY name COLLATE NOCASE ASC"
    cur = await db.execute(q, args)
    result = await cur.fetchall()
    model_cache.set(cache_key, result)
    return result

async def create_profile(db: aiosqlite.Connection, data: Dict[str, Any]) -> int:
    cur = await db.execute(
        "INSERT INTO profiles(name, system_prompt, temperature, max_tokens, openrouter_preset) VALUES(?,?,?,?,?)",
        (
            data["name"],
            data.get("system_prompt"),
            data.get("temperature", 0.7),
            data.get("max_tokens", 2048),
            data.get("openrouter_preset"),
        ),
    )
    await db.commit()
    # Invalidate profiles list cache
    profile_cache.invalidate("profiles_all")
    return cur.lastrowid

async def get_profile(db: aiosqlite.Connection, profile_id: int) -> Optional[aiosqlite.Row]:
    cache_key = f"profile_{profile_id}"
    cached = profile_cache.get(cache_key)
    if cached is not None:
        return cached
    
    cur = await db.execute(
        "SELECT id, name, system_prompt, temperature, max_tokens, openrouter_preset FROM profiles WHERE id=?",
        (profile_id,),
    )
    result = await cur.fetchone()
    if result:
        profile_cache.set(cache_key, result)
    return result

async def update_profile(db: aiosqlite.Connection, profile_id: int, data: Dict[str, Any]) -> bool:
    cur = await db.execute(
        """
        UPDATE profiles
        SET name=?, system_prompt=?, temperature=?, max_tokens=?, openrouter_preset=?
        WHERE id=?
        """,
        (
            data["name"],
            data.get("system_prompt"),
            data.get("temperature", 0.7),
            data.get("max_tokens", 2048),
            data.get("openrouter_preset"),
            profile_id,
        ),
    )
    await db.commit()
    # Invalidate cache for this profile
    profile_cache.invalidate(f"profile_{profile_id}")
    profile_cache.invalidate("profiles_all")
    return cur.rowcount > 0

async def delete_profile(db: aiosqlite.Connection, profile_id: int) -> bool:
    cur = await db.execute("DELETE FROM profiles WHERE id=?", (profile_id,))
    await db.commit()
    # Invalidate cache for this profile and list
    profile_cache.invalidate(f"profile_{profile_id}")
    profile_cache.invalidate("profiles_all")
    return cur.rowcount > 0

async def list_profiles(db: aiosqlite.Connection) -> List[aiosqlite.Row]:
    cache_key = "profiles_all"
    cached = profile_cache.get(cache_key)
    if cached is not None:
        return cached
    
    cur = await db.execute(
        "SELECT id, name, system_prompt, temperature, max_tokens, openrouter_preset FROM profiles ORDER BY id DESC"
    )
    result = await cur.fetchall()
    profile_cache.set(cache_key, result)
    return result

async def create_session(db: aiosqlite.Connection, data: Dict[str, Any]) -> str:
    sid = _uuid()
    await db.execute(
        "INSERT INTO sessions(id, session_type, title, profile_id) VALUES(?,?,?,?)",
        (sid, data["session_type"], data.get("title"), data.get("profile_id")),
    )
    await db.commit()
    return sid

async def list_sessions(db: aiosqlite.Connection, limit: int=50) -> List[aiosqlite.Row]:
    cur = await db.execute(
        "SELECT id, session_type, title, profile_id, created_at FROM sessions ORDER BY created_at DESC LIMIT ?",
        (limit,),
    )
    return await cur.fetchall()

async def get_session(db: aiosqlite.Connection, session_id: str) -> Optional[aiosqlite.Row]:
    cur = await db.execute(
        "SELECT id, session_type, title, profile_id, created_at FROM sessions WHERE id=?",
        (session_id,),
    )
    return await cur.fetchone()

async def update_session(db: aiosqlite.Connection, session_id: str, data: Dict[str, Any]) -> bool:
    """Update session fields. Returns True if session was found and updated."""
    # Build dynamic SET clause based on provided fields
    fields = []
    values = []
    
    if "title" in data:
        fields.append("title=?")
        values.append(data["title"])
    
    if "profile_id" in data:
        fields.append("profile_id=?")
        values.append(data["profile_id"])
    
    if not fields:
        return True  # Nothing to update
    
    values.append(session_id)
    query = f"UPDATE sessions SET {', '.join(fields)} WHERE id=?"
    
    cur = await db.execute(query, values)
    await db.commit()
    return cur.rowcount > 0

async def delete_session(db: aiosqlite.Connection, session_id: str) -> bool:
    """Delete session and all related messages. Returns True if session was found and deleted."""
    # First delete related messages (due to foreign key constraint)
    await db.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
    
    # Delete usage logs
    await db.execute("DELETE FROM usage_logs WHERE session_id=?", (session_id,))
    
    # Then delete the session
    cur = await db.execute("DELETE FROM sessions WHERE id=?", (session_id,))
    await db.commit()
    return cur.rowcount > 0

async def list_messages(db: aiosqlite.Connection, session_id: str) -> List[aiosqlite.Row]:
    cur = await db.execute(
        "SELECT id, session_id, role, content, created_at FROM messages WHERE session_id=? ORDER BY created_at ASC",
        (session_id,),
    )
    return await cur.fetchall()

async def add_message(db: aiosqlite.Connection, session_id: str, role: str, content: str) -> str:
    mid = _uuid()
    await db.execute(
        "INSERT INTO messages(id, session_id, role, content) VALUES(?,?,?,?)",
        (mid, session_id, role, content),
    )
    await db.commit()
    return mid

async def insert_usage_log(
    db: aiosqlite.Connection,
    *,
    session_id: str,
    model_id: Optional[str],
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    profile_id: Optional[int] = None,
) -> str:
    prompt_tokens = int(prompt_tokens or 0)
    completion_tokens = int(completion_tokens or 0)
    total_tokens = prompt_tokens + completion_tokens

    pricing_prompt = 0.0
    pricing_completion = 0.0
    if model_id:
        cur = await db.execute(
            "SELECT pricing_prompt, pricing_completion FROM models WHERE id=?",
            (model_id,),
        )
        model_row = await cur.fetchone()
        if model_row:
            pricing_prompt = float(model_row["pricing_prompt"] or 0)
            pricing_completion = float(model_row["pricing_completion"] or 0)

    cost_usd = (
        (prompt_tokens * pricing_prompt) + (completion_tokens * pricing_completion)
    ) / 1_000_000

    uid = _uuid()
    await db.execute(
        """
        INSERT INTO usage_logs(
            id, session_id, profile_id, model_id, prompt_tokens, completion_tokens, total_tokens, cost_usd
        ) VALUES(?,?,?,?,?,?,?,?)
        """,
        (
            uid,
            session_id,
            profile_id,
            model_id,
            prompt_tokens,
            completion_tokens,
            total_tokens,
            cost_usd,
        ),
    )
    await db.commit()
    return uid

async def list_usage_by_session(db: aiosqlite.Connection, session_id: str) -> List[aiosqlite.Row]:
    cur = await db.execute(
        """
        SELECT ul.id, ul.session_id, ul.profile_id, ul.model_id,
               m.name AS model_name, m.openrouter_id,
               ul.prompt_tokens, ul.completion_tokens, ul.total_tokens, ul.cost_usd, ul.created_at
        FROM usage_logs ul
        LEFT JOIN models m ON ul.model_id = m.id
        WHERE ul.session_id=?
        ORDER BY ul.created_at DESC
        """,
        (session_id,),
    )
    return await cur.fetchall()

async def aggregate_usage_by_model(db: aiosqlite.Connection) -> List[aiosqlite.Row]:
    cur = await db.execute(
        """
        SELECT ul.model_id, m.name AS model_name, m.openrouter_id,
               SUM(ul.prompt_tokens) AS prompt_tokens,
               SUM(ul.completion_tokens) AS completion_tokens,
               SUM(ul.total_tokens) AS total_tokens,
               SUM(ul.cost_usd) AS cost_usd
        FROM usage_logs ul
        LEFT JOIN models m ON ul.model_id = m.id
        GROUP BY ul.model_id
        ORDER BY cost_usd DESC, total_tokens DESC
        """,
    )
    return await cur.fetchall()
