from __future__ import annotations
import uuid
from typing import Any, Dict, List, Optional, Sequence
import aiosqlite

def _uuid() -> str:
    return str(uuid.uuid4())

async def upsert_models(db: aiosqlite.Connection, rows: List[Dict[str, Any]]) -> int:
    # rows: {openrouter_id, name, context_length, pricing_prompt, pricing_completion, is_reasoning}
    count = 0
    for r in rows:
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
                _uuid(),
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
    return count

async def list_models(db: aiosqlite.Connection, *, reasoning: Optional[bool]=None, max_price: Optional[float]=None, min_context: Optional[int]=None) -> List[aiosqlite.Row]:
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
    return await cur.fetchall()

async def create_profile(db: aiosqlite.Connection, data: Dict[str, Any]) -> int:
    cur = await db.execute(
        "INSERT INTO profiles(name, system_prompt, temperature, max_tokens) VALUES(?,?,?,?)",
        (data["name"], data.get("system_prompt"), data.get("temperature", 0.7), data.get("max_tokens", 2048)),
    )
    await db.commit()
    return cur.lastrowid

async def get_profile(db: aiosqlite.Connection, profile_id: int) -> Optional[aiosqlite.Row]:
    cur = await db.execute(
        "SELECT id, name, system_prompt, temperature, max_tokens FROM profiles WHERE id=?",
        (profile_id,),
    )
    return await cur.fetchone()

async def update_profile(db: aiosqlite.Connection, profile_id: int, data: Dict[str, Any]) -> bool:
    cur = await db.execute(
        """
        UPDATE profiles
        SET name=?, system_prompt=?, temperature=?, max_tokens=?
        WHERE id=?
        """,
        (data["name"], data.get("system_prompt"), data.get("temperature", 0.7), data.get("max_tokens", 2048), profile_id),
    )
    await db.commit()
    return cur.rowcount > 0

async def delete_profile(db: aiosqlite.Connection, profile_id: int) -> bool:
    cur = await db.execute("DELETE FROM profiles WHERE id=?", (profile_id,))
    await db.commit()
    return cur.rowcount > 0

async def list_profiles(db: aiosqlite.Connection) -> List[aiosqlite.Row]:
    cur = await db.execute("SELECT id, name, system_prompt, temperature, max_tokens FROM profiles ORDER BY id DESC")
    return await cur.fetchall()

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
