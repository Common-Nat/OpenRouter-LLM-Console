import aiosqlite
import logging
from pathlib import Path
from .core.config import settings

logger = logging.getLogger(__name__)

async def _create_migrations_table(db: aiosqlite.Connection) -> None:
    """Create the schema_migrations table if it doesn't exist."""
    await db.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TEXT DEFAULT (datetime('now'))
        )
    """)


async def _get_applied_migrations(db: aiosqlite.Connection) -> set[int]:
    """Get the set of migration versions that have been applied."""
    cur = await db.execute("SELECT version FROM schema_migrations ORDER BY version")
    rows = await cur.fetchall()
    return {row[0] for row in rows}


async def _apply_migration(db: aiosqlite.Connection, version: int, sql: str) -> None:
    """Apply a single migration and record it."""
    try:
        # Execute the migration SQL
        await db.executescript(sql)
        # Record that this migration was applied
        await db.execute(
            "INSERT INTO schema_migrations (version) VALUES (?)",
            (version,)
        )
        logger.info(f"Applied migration {version:03d}")
    except Exception as e:
        # For migrations that might fail if already applied (e.g., ALTER TABLE),
        # check if it's a "duplicate column" error and mark as applied anyway
        if "duplicate column name" in str(e).lower():
            await db.execute(
                "INSERT OR IGNORE INTO schema_migrations (version) VALUES (?)",
                (version,)
            )
            logger.info(f"Migration {version:03d} already applied (column exists), marked as complete")
        else:
            raise


async def _run_migrations(db: aiosqlite.Connection) -> None:
    """Run all pending migrations from the migrations/ directory."""
    # Get the migrations directory path
    migrations_dir = Path(__file__).parent.parent / "migrations"
    if not migrations_dir.exists():
        logger.warning(f"Migrations directory not found: {migrations_dir}")
        return

    # Get applied migrations
    applied = await _get_applied_migrations(db)

    # Find all migration files (exclude _down.sql rollback files)
    migration_files = sorted(
        f for f in migrations_dir.glob("*.sql") 
        if not f.stem.endswith("_down")
    )
    
    for migration_file in migration_files:
        # Extract version number from filename (e.g., "001_initial_schema.sql" -> 1)
        try:
            version = int(migration_file.stem.split("_")[0])
        except (ValueError, IndexError):
            logger.warning(f"Skipping invalid migration filename: {migration_file.name}")
            continue

        # Skip if already applied
        if version in applied:
            continue

        # Read and apply the migration
        sql = migration_file.read_text(encoding="utf-8")
        logger.info(f"Applying migration {version:03d}: {migration_file.name}")
        await _apply_migration(db, version, sql)


async def init_db() -> None:
    """Initialize the database and run all pending migrations."""
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(settings.db_path) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute("PRAGMA foreign_keys = ON;")
        
        # Create migrations tracking table
        await _create_migrations_table(db)
        
        # Run all pending migrations
        await _run_migrations(db)
        
        await db.commit()

async def get_db():
    db = await aiosqlite.connect(settings.db_path)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON;")
    try:
        yield db
    finally:
        await db.close()
