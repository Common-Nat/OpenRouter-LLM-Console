-- Add FTS5 full-text search for messages
-- This enables fast text search across message content with ranking and highlighting

PRAGMA foreign_keys = ON;

-- Create FTS5 virtual table for message search
-- content= option points to source table for external content storage
-- This keeps data in one place and syncs via triggers
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
  content,           -- Message text - full-text indexed
  role UNINDEXED,    -- Include for filtering but don't index
  session_id UNINDEXED,
  created_at UNINDEXED,
  content='messages',  -- Point to source table
  content_rowid='rowid'
);

-- Trigger: sync FTS index when new message is inserted
CREATE TRIGGER IF NOT EXISTS messages_after_insert AFTER INSERT ON messages BEGIN
  INSERT INTO messages_fts(rowid, content, role, session_id, created_at)
  VALUES (NEW.rowid, NEW.content, NEW.role, NEW.session_id, NEW.created_at);
END;

-- Trigger: sync FTS index when message is updated
CREATE TRIGGER IF NOT EXISTS messages_after_update AFTER UPDATE ON messages BEGIN
  UPDATE messages_fts 
  SET content = NEW.content,
      role = NEW.role,
      session_id = NEW.session_id,
      created_at = NEW.created_at
  WHERE rowid = NEW.rowid;
END;

-- Trigger: remove from FTS index when message is deleted
CREATE TRIGGER IF NOT EXISTS messages_after_delete AFTER DELETE ON messages BEGIN
  DELETE FROM messages_fts WHERE rowid = OLD.rowid;
END;

-- Backfill existing messages into FTS table
-- This is safe to run multiple times (INSERT OR IGNORE)
INSERT OR IGNORE INTO messages_fts(rowid, content, role, session_id, created_at)
SELECT rowid, content, role, session_id, created_at FROM messages;

-- Create index for common filter combinations
CREATE INDEX IF NOT EXISTS idx_messages_type_date ON messages(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_type_date ON sessions(session_type, created_at);
