# Database Migrations

This directory contains SQL migration files for the OpenRouter LLM Console database schema.

## Migration Files

### Forward Migrations
- `001_initial_schema.sql` - Creates all core tables (models, profiles, sessions, messages, usage_logs)
- `002_add_openrouter_preset.sql` - Adds `openrouter_preset` column to profiles table

### Rollback Migrations
- `001_initial_schema_down.sql` - Removes all tables created by 001
- `002_add_openrouter_preset_down.sql` - Removes openrouter_preset column

### Version Tracking
- `000_version_tracking.sql` - Schema version table (optional, for migration tooling)

## How Migrations Work

Migrations are applied automatically when the application starts. The migration system:
1. Checks which migrations have been applied
2. Runs any pending migrations in order
3. All migrations are idempotent (safe to run multiple times)

## Migration Testing

Run the full test suite for migrations:

```bash
# From backend/ directory
pytest tests/test_migrations.py -v
```

Tests verify:
- ✅ Forward migrations create correct schema
- ✅ Rollback migrations clean up properly
- ✅ Data preservation during compatible rollbacks
- ✅ Foreign key constraints work correctly
- ✅ Idempotent migration behavior

## Creating New Migrations

When adding a new migration:

1. **Create forward migration:**
   ```sql
   -- e.g., 003_add_tags_table.sql
   CREATE TABLE IF NOT EXISTS tags (
     id TEXT PRIMARY KEY,
     name TEXT NOT NULL UNIQUE
   );
   ```

2. **Create rollback migration:**
   ```sql
   -- 003_add_tags_table_down.sql
   DROP TABLE IF EXISTS tags;
   ```

3. **Make migrations idempotent using IF NOT EXISTS / IF EXISTS**

4. **Test thoroughly:**
   ```python
   # Add test to tests/test_migrations.py
   @pytest.mark.asyncio
   async def test_003_add_tags_forward():
       # Test forward migration
       pass
   ```

5. **Document the migration in this README**

## Rollback Process

To manually rollback a migration:

```bash
# From backend/ directory
sqlite3 console.db < migrations/002_add_openrouter_preset_down.sql
```

⚠️ **Warning:** Rollbacks may cause data loss. Always backup your database first!

## SQLite Limitations

SQLite has limited `ALTER TABLE` support:
- ✅ Can ADD COLUMN
- ❌ Cannot DROP COLUMN (requires table recreation)
- ❌ Cannot RENAME COLUMN (requires table recreation)

For complex schema changes, see `002_add_openrouter_preset_down.sql` for the table recreation pattern.

## Notes

- Migrations run automatically on app startup
- `ALTER TABLE ADD COLUMN` will fail if column exists, but this is handled gracefully
- Migration version is extracted from filename prefix (e.g., `001` → version `1`)
- Existing databases will have migrations backfilled as needed
