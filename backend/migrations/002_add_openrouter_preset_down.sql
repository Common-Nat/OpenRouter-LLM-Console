-- Rollback for 002_add_openrouter_preset.sql
-- Removes the openrouter_preset column from profiles table
-- Note: SQLite doesn't support DROP COLUMN directly, so we need to recreate the table

PRAGMA foreign_keys = OFF;

-- Create a backup of the profiles table without openrouter_preset
CREATE TABLE profiles_backup (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  system_prompt TEXT,
  temperature REAL DEFAULT 0.7,
  max_tokens INTEGER DEFAULT 2048,
  created_at TEXT DEFAULT (datetime('now'))
);

-- Copy data from the original table (excluding openrouter_preset)
INSERT INTO profiles_backup (id, name, system_prompt, temperature, max_tokens, created_at)
SELECT id, name, system_prompt, temperature, max_tokens, created_at
FROM profiles;

-- Drop the original table
DROP TABLE profiles;

-- Rename the backup table to the original name
ALTER TABLE profiles_backup RENAME TO profiles;

PRAGMA foreign_keys = ON;
