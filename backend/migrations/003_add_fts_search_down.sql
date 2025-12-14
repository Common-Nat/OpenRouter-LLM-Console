-- Rollback FTS5 search implementation

PRAGMA foreign_keys = ON;

-- Drop triggers
DROP TRIGGER IF EXISTS messages_after_delete;
DROP TRIGGER IF EXISTS messages_after_update;
DROP TRIGGER IF EXISTS messages_after_insert;

-- Drop FTS virtual table
DROP TABLE IF EXISTS messages_fts;

-- Drop indexes
DROP INDEX IF EXISTS idx_sessions_type_date;
-- Note: idx_messages_type_date was created redundantly - it already exists as idx_messages_session_created
-- So we don't drop it in rollback
