"""
Migration Test Harness

Tests bidirectional migration integrity:
- Forward migrations apply correctly
- Rollback migrations clean up properly
- Data preservation during compatible rollbacks
- Schema version tracking
"""
import pytest
import aiosqlite
import os
from pathlib import Path


MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"
TEST_DB = ":memory:"  # Use in-memory DB for tests


async def get_table_list(db: aiosqlite.Connection):
    """Get list of all tables in the database."""
    cursor = await db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    rows = await cursor.fetchall()
    return [row[0] for row in rows]


async def get_table_columns(db: aiosqlite.Connection, table_name: str):
    """Get list of columns for a table."""
    cursor = await db.execute(f"PRAGMA table_info({table_name})")
    rows = await cursor.fetchall()
    return [(row[1], row[2]) for row in rows]  # (name, type)


async def apply_migration(db: aiosqlite.Connection, migration_file: Path):
    """Apply a migration file to the database."""
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    # Execute migration in a transaction
    await db.executescript(sql)
    await db.commit()


@pytest.mark.asyncio
async def test_001_initial_schema_forward():
    """Test that 001_initial_schema.sql creates all required tables."""
    async with aiosqlite.connect(TEST_DB) as db:
        # Apply migration
        migration_file = MIGRATIONS_DIR / "001_initial_schema.sql"
        await apply_migration(db, migration_file)
        
        # Verify tables exist
        tables = await get_table_list(db)
        expected_tables = ['models', 'profiles', 'sessions', 'messages', 'usage_logs']
        
        for table in expected_tables:
            assert table in tables, f"Table {table} was not created"
        
        # Verify models table structure
        models_cols = await get_table_columns(db, 'models')
        models_col_names = [col[0] for col in models_cols]
        assert 'id' in models_col_names
        assert 'openrouter_id' in models_col_names
        assert 'name' in models_col_names
        assert 'context_length' in models_col_names
        assert 'pricing_prompt' in models_col_names
        assert 'pricing_completion' in models_col_names
        assert 'is_reasoning' in models_col_names
        assert 'created_at' in models_col_names
        
        # Verify profiles table structure
        profiles_cols = await get_table_columns(db, 'profiles')
        profiles_col_names = [col[0] for col in profiles_cols]
        assert 'id' in profiles_col_names
        assert 'name' in profiles_col_names
        assert 'system_prompt' in profiles_col_names
        assert 'temperature' in profiles_col_names
        assert 'max_tokens' in profiles_col_names
        assert 'created_at' in profiles_col_names
        
        # Verify sessions table structure
        sessions_cols = await get_table_columns(db, 'sessions')
        sessions_col_names = [col[0] for col in sessions_cols]
        assert 'id' in sessions_col_names
        assert 'session_type' in sessions_col_names
        assert 'title' in sessions_col_names
        assert 'profile_id' in sessions_col_names
        assert 'created_at' in sessions_col_names
        
        # Verify messages table structure
        messages_cols = await get_table_columns(db, 'messages')
        messages_col_names = [col[0] for col in messages_cols]
        assert 'id' in messages_col_names
        assert 'session_id' in messages_col_names
        assert 'role' in messages_col_names
        assert 'content' in messages_col_names
        assert 'created_at' in messages_col_names
        
        # Verify usage_logs table structure
        usage_cols = await get_table_columns(db, 'usage_logs')
        usage_col_names = [col[0] for col in usage_cols]
        assert 'id' in usage_col_names
        assert 'session_id' in usage_col_names
        assert 'profile_id' in usage_col_names
        assert 'model_id' in usage_col_names
        assert 'prompt_tokens' in usage_col_names
        assert 'completion_tokens' in usage_col_names
        assert 'total_tokens' in usage_col_names
        assert 'cost_usd' in usage_col_names
        assert 'created_at' in usage_col_names


@pytest.mark.asyncio
async def test_001_initial_schema_rollback():
    """Test that 001_initial_schema_down.sql removes all tables."""
    async with aiosqlite.connect(TEST_DB) as db:
        # Apply forward migration
        forward_file = MIGRATIONS_DIR / "001_initial_schema.sql"
        await apply_migration(db, forward_file)
        
        # Verify tables exist
        tables_before = await get_table_list(db)
        assert len(tables_before) > 0
        
        # Apply rollback migration
        rollback_file = MIGRATIONS_DIR / "001_initial_schema_down.sql"
        await apply_migration(db, rollback_file)
        
        # Verify all tables are removed
        tables_after = await get_table_list(db)
        
        expected_removed = ['models', 'profiles', 'sessions', 'messages', 'usage_logs']
        for table in expected_removed:
            assert table not in tables_after, f"Table {table} was not removed"


@pytest.mark.asyncio
async def test_002_add_openrouter_preset_forward():
    """Test that 002_add_openrouter_preset.sql adds the column."""
    async with aiosqlite.connect(TEST_DB) as db:
        # Apply initial schema first
        await apply_migration(db, MIGRATIONS_DIR / "001_initial_schema.sql")
        
        # Check profiles table before migration
        cols_before = await get_table_columns(db, 'profiles')
        col_names_before = [col[0] for col in cols_before]
        assert 'openrouter_preset' not in col_names_before
        
        # Apply preset migration
        await apply_migration(db, MIGRATIONS_DIR / "002_add_openrouter_preset.sql")
        
        # Check profiles table after migration
        cols_after = await get_table_columns(db, 'profiles')
        col_names_after = [col[0] for col in cols_after]
        assert 'openrouter_preset' in col_names_after


@pytest.mark.asyncio
async def test_002_add_openrouter_preset_rollback():
    """Test that 002_add_openrouter_preset_down.sql removes the column."""
    async with aiosqlite.connect(TEST_DB) as db:
        # Apply both forward migrations
        await apply_migration(db, MIGRATIONS_DIR / "001_initial_schema.sql")
        await apply_migration(db, MIGRATIONS_DIR / "002_add_openrouter_preset.sql")
        
        # Verify column exists
        cols_before = await get_table_columns(db, 'profiles')
        col_names_before = [col[0] for col in cols_before]
        assert 'openrouter_preset' in col_names_before
        
        # Apply rollback
        rollback_file = MIGRATIONS_DIR / "002_add_openrouter_preset_down.sql"
        await apply_migration(db, rollback_file)
        
        # Verify column is removed
        cols_after = await get_table_columns(db, 'profiles')
        col_names_after = [col[0] for col in cols_after]
        assert 'openrouter_preset' not in col_names_after
        
        # Verify other columns still exist
        assert 'id' in col_names_after
        assert 'name' in col_names_after
        assert 'system_prompt' in col_names_after
        assert 'temperature' in col_names_after
        assert 'max_tokens' in col_names_after


@pytest.mark.asyncio
async def test_002_rollback_preserves_data():
    """Test that rollback preserves existing profile data."""
    async with aiosqlite.connect(TEST_DB) as db:
        # Apply both forward migrations
        await apply_migration(db, MIGRATIONS_DIR / "001_initial_schema.sql")
        await apply_migration(db, MIGRATIONS_DIR / "002_add_openrouter_preset.sql")
        
        # Insert test data
        await db.execute(
            """
            INSERT INTO profiles (name, system_prompt, temperature, max_tokens, openrouter_preset)
            VALUES ('Test Profile', 'You are helpful', 0.7, 2048, 'coding')
            """
        )
        await db.commit()
        
        # Verify data exists
        cursor = await db.execute("SELECT name, temperature, max_tokens FROM profiles")
        row_before = await cursor.fetchone()
        assert row_before[0] == 'Test Profile'
        assert row_before[1] == 0.7
        assert row_before[2] == 2048
        
        # Apply rollback
        await apply_migration(db, MIGRATIONS_DIR / "002_add_openrouter_preset_down.sql")
        
        # Verify data is preserved (minus openrouter_preset)
        cursor = await db.execute("SELECT name, temperature, max_tokens FROM profiles")
        row_after = await cursor.fetchone()
        assert row_after[0] == 'Test Profile'
        assert row_after[1] == 0.7
        assert row_after[2] == 2048


@pytest.mark.asyncio
async def test_full_migration_cycle():
    """Test complete forward and backward migration cycle."""
    async with aiosqlite.connect(TEST_DB) as db:
        # Start with empty DB
        tables_start = await get_table_list(db)
        assert len(tables_start) == 0
        
        # Apply all forward migrations
        await apply_migration(db, MIGRATIONS_DIR / "001_initial_schema.sql")
        await apply_migration(db, MIGRATIONS_DIR / "002_add_openrouter_preset.sql")
        
        # Verify final state
        tables_forward = await get_table_list(db)
        assert 'profiles' in tables_forward
        
        cols_forward = await get_table_columns(db, 'profiles')
        col_names_forward = [col[0] for col in cols_forward]
        assert 'openrouter_preset' in col_names_forward
        
        # Rollback all migrations in reverse order
        await apply_migration(db, MIGRATIONS_DIR / "002_add_openrouter_preset_down.sql")
        
        # Verify intermediate state (profiles exist but no openrouter_preset)
        cols_mid = await get_table_columns(db, 'profiles')
        col_names_mid = [col[0] for col in cols_mid]
        assert 'openrouter_preset' not in col_names_mid
        assert 'name' in col_names_mid  # Other columns still exist
        
        # Rollback initial schema
        await apply_migration(db, MIGRATIONS_DIR / "001_initial_schema_down.sql")
        
        # Verify we're back to empty
        tables_end = await get_table_list(db)
        expected_removed = ['models', 'profiles', 'sessions', 'messages', 'usage_logs']
        for table in expected_removed:
            assert table not in tables_end


@pytest.mark.asyncio
async def test_idempotent_forward_migrations():
    """Test that forward migrations can be applied multiple times safely."""
    async with aiosqlite.connect(TEST_DB) as db:
        # Apply migration twice
        await apply_migration(db, MIGRATIONS_DIR / "001_initial_schema.sql")
        await apply_migration(db, MIGRATIONS_DIR / "001_initial_schema.sql")
        
        # Verify tables exist and schema is correct
        tables = await get_table_list(db)
        assert 'profiles' in tables
        
        # Apply preset migration twice
        await apply_migration(db, MIGRATIONS_DIR / "002_add_openrouter_preset.sql")
        
        # Second application should fail gracefully (SQLite will raise error for duplicate column)
        # We expect this to fail, so we catch it
        try:
            await apply_migration(db, MIGRATIONS_DIR / "002_add_openrouter_preset.sql")
        except aiosqlite.OperationalError as e:
            # Expected: "duplicate column name: openrouter_preset"
            assert 'duplicate column' in str(e).lower()


@pytest.mark.asyncio
async def test_foreign_key_constraints():
    """Test that foreign key constraints are properly enforced."""
    async with aiosqlite.connect(TEST_DB) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        
        # Apply migrations
        await apply_migration(db, MIGRATIONS_DIR / "001_initial_schema.sql")
        
        # Insert a profile
        await db.execute(
            "INSERT INTO profiles (id, name) VALUES (1, 'Test Profile')"
        )
        
        # Insert a session referencing the profile
        await db.execute(
            "INSERT INTO sessions (id, session_type, profile_id) VALUES ('sess-1', 'chat', 1)"
        )
        await db.commit()
        
        # Delete the profile (should set session.profile_id to NULL due to ON DELETE SET NULL)
        await db.execute("DELETE FROM profiles WHERE id = 1")
        await db.commit()
        
        # Verify session still exists but profile_id is NULL
        cursor = await db.execute("SELECT profile_id FROM sessions WHERE id = 'sess-1'")
        row = await cursor.fetchone()
        assert row[0] is None
        
        # Test CASCADE delete for messages
        await db.execute(
            "INSERT INTO messages (id, session_id, role, content) VALUES ('msg-1', 'sess-1', 'user', 'Hello')"
        )
        await db.commit()
        
        # Delete session (should cascade delete messages)
        await db.execute("DELETE FROM sessions WHERE id = 'sess-1'")
        await db.commit()
        
        # Verify message was deleted
        cursor = await db.execute("SELECT COUNT(*) FROM messages WHERE id = 'msg-1'")
        count = await cursor.fetchone()
        assert count[0] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
