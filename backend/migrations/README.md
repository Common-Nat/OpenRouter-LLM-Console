# Database Migrations

This directory contains SQL migration files for schema evolution.

## How It Works

- Migrations are numbered `.sql` files: `001_name.sql`, `002_name.sql`, etc.
- On startup, `init_db()` runs all pending migrations in order
- Applied migrations are tracked in the `schema_migrations` table
- Each migration runs in a transaction (via `executescript`)

## Creating a New Migration

1. Create a new file with the next number: `003_your_feature.sql`
2. Write idempotent SQL when possible (use `IF NOT EXISTS`, etc.)
3. Test with a fresh database and an existing database
4. Commit the migration file

## Migration File Format

```sql
-- Brief description of what this migration does

CREATE TABLE IF NOT EXISTS my_new_table (
  id TEXT PRIMARY KEY,
  ...
);

-- Or for alterations:
ALTER TABLE existing_table ADD COLUMN new_column TEXT;
```

## Notes

- Migrations run automatically on app startup
- `ALTER TABLE ADD COLUMN` will fail if column exists, but this is handled gracefully
- Migration version is extracted from filename prefix (e.g., `001` → version `1`)
- Existing databases will have migrations backfilled as needed

## Existing Migrations

- `001_initial_schema.sql`: Base schema (models, profiles, sessions, messages, usage_logs)
- `002_add_openrouter_preset.sql`: Add `openrouter_preset` column to profiles table
