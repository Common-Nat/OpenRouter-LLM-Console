-- Schema version tracking table
-- This table tracks which migrations have been applied
-- Used by the migration test harness

CREATE TABLE IF NOT EXISTS schema_version (
  version INTEGER PRIMARY KEY,
  migration_name TEXT NOT NULL,
  applied_at TEXT DEFAULT (datetime('now'))
);
